# ===== 第520课：消息队列与事件驱动-事务消息与Outbox =====
# 知识点：
#   - 双写问题：业务写库 + 发消息是两个操作，无法天然原子
#   - 先写库后发消息：发消息失败 → 数据有了、事件丢了
#   - 先发消息后写库：写库失败 → 事件发了、数据没有
#   - Outbox 模式：把“要发的消息”和业务数据写进同一个本地事务
#   - 中继（relay）轮询 outbox，发送成功后标记 sent；失败可重试
#   - 至少一次投递 → 消费端幂等（第447课）；也可用事件 ID 去重
#   - 与第208课事务、第515课投递语义直接相关
import json
import sqlite3
import uuid


class FakeBroker:
    def __init__(self):
        self.published = []

    def publish(self, topic, event):
        self.published.append((topic, event))
        print(f"  [broker] {topic} ← {event['event_id'][:8]}… {event['type']}")


conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    amount REAL,
    status TEXT
);
CREATE TABLE outbox (
    event_id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    payload TEXT NOT NULL,
    sent INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    sent_at TEXT
);
""")
broker = FakeBroker()


def create_order(order_id, amount):
    """业务数据 + 事件在同一个事务里写入。"""
    event = {
        "event_id": str(uuid.uuid4()),
        "type": "order.created",
        "order_id": order_id,
        "amount": amount,
    }
    with conn:                                    # 事务：要么都成功，要么都回滚
        conn.execute("INSERT INTO orders (order_id, amount, status) VALUES (?, ?, 'created')",
                     (order_id, amount))
        conn.execute("INSERT INTO outbox (event_id, topic, payload) VALUES (?, ?, ?)",
                     (event["event_id"], "order-events", json.dumps(event, ensure_ascii=False)))


def relay(limit=10) -> int:
    """把未发送的 outbox 事件发到 broker，成功后标记 sent。"""
    rows = conn.execute(
        "SELECT * FROM outbox WHERE sent = 0 ORDER BY created_at LIMIT ?", (limit,)
    ).fetchall()
    sent = 0
    for row in rows:
        try:
            broker.publish(row["topic"], json.loads(row["payload"]))
        except Exception as exc:
            print(f"  [relay] 发送失败，保留待重试：{exc}")
            continue
        conn.execute("UPDATE outbox SET sent = 1, sent_at = datetime('now') WHERE event_id = ?",
                     (row["event_id"],))
        conn.commit()
        sent += 1
    return sent


print("== 1. 创建订单（事务内写业务 + outbox）==")
create_order("O1", 99.0)
print("  订单表：", [dict(r) for r in conn.execute("SELECT * FROM orders")])
print("  outbox：", [(r["event_id"][:8], r["sent"]) for r in
                     conn.execute("SELECT * FROM outbox")])

print("\n== 2. 模拟“写库成功但 relay 前宕机” ==")
print("  重启后 relay 扫描 outbox：")
print("  发送数量：", relay())

print("\n== 3. 再次 relay（不应重复发送）==")
print("  发送数量：", relay())
print("  broker 已收事件数：", len(broker.published))

print("\n== 4. 模拟“发送成功但标记 sent 前宕机” ==")
create_order("O2", 199.0)
# 手动发一次但不标记 sent，模拟崩溃
row = conn.execute("SELECT * FROM outbox WHERE sent = 0").fetchone()
broker.publish(row["topic"], json.loads(row["payload"]))
print("  broker 已收事件数：", len(broker.published))
print("  outbox 仍未标记：", conn.execute(
    "SELECT COUNT(*) FROM outbox WHERE sent = 0").fetchone()[0])
print("  重启 relay 会再发一次（at-least-once）")
relay()
print("  broker 已收事件数：", len(broker.published), "（O2 出现两次）")

# ---- 消费端幂等去重 ----
print("\n== 5. 消费端按 event_id 去重 ==")
seen = set()
for topic, event in broker.published:
    if event["event_id"] in seen:
        print(f"  {event['order_id']}: 重复事件，跳过")
    else:
        seen.add(event["event_id"])
        print(f"  {event['order_id']}: 处理 {event['type']}")

print("\n== 6. 事务回滚：业务失败，outbox 也不写 ==")
try:
    with conn:
        conn.execute("INSERT INTO orders VALUES ('O3', 50, 'created')")
        conn.execute("INSERT INTO outbox (event_id, topic, payload) VALUES (?, ?, ?)",
                     ("dup", "order-events", "{}"))
        raise RuntimeError("模拟业务校验失败")
except RuntimeError as exc:
    print("  业务失败：", exc)
print("  O3 是否存在：", conn.execute(
    "SELECT COUNT(*) FROM orders WHERE order_id='O3'").fetchone()[0])
print("  outbox 中 dup 是否存在：", conn.execute(
    "SELECT COUNT(*) FROM outbox WHERE event_id='dup'").fetchone()[0])
print("  结论：同一事务保证“业务与事件同生共死”")

# ---- Outbox vs 其他方案 ----
print("\n== 方案对比 ==")
rows = [
    ("先库后消息", "简单", "消息可能丢"),
    ("先消息后库", "不会丢消息", "可能发空事件"),
    ("Outbox", "不丢、可重试、实现简单", "需要中继、至少一次"),
    ("事务消息（MQ 支持）", "由 MQ 保证", "依赖具体中间件"),
]
print(f"  {'方案':<18}{'优点':<22}{'代价'}")
for r in rows:
    print(f"  {r[0]:<18}{r[1]:<22}{r[2]}")

# ---- 落地清单 ----
print("\n== 落地清单 ==")
for item in [
    "outbox 与业务表在同一个数据库/事务",
    "relay 独立进程/定时任务，失败自动重试",
    "事件带唯一 event_id，消费端去重",
    "outbox 定期归档，避免无限增长",
    "监控积压量（sent=0 的数量）与发送延迟",
]:
    print("  -", item)

conn.close()

# ===== 练习题 =====
# 1. 给 outbox 增加 attempts 与 last_error，实现失败重试计数。
# 2. 实现 relay 的“批量发送 + 部分失败”处理。
# 3. 用 SQLite 的唯一约束保证 event_id 不重复插入。
# 4. 思考：为什么 Outbox 不能解决“消费端重复处理”，必须靠幂等？
