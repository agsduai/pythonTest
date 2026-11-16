# ===== 第447课：可靠性设计-幂等设计 =====
# 知识点：
#   - 幂等：同一个请求执行一次和执行多次，业务结果相同
#   - 为什么需要：网络超时后客户端会重试、消息队列会重复投递、用户会连点
#   - 实现核心：幂等键（idempotency key）+ 唯一约束 + 结果缓存
#   - 流程：查键 → 已处理则直接返回旧结果；未处理则执行并写入键
#   - 并发安全：用数据库唯一约束兜底，而不是“先查再插”的应用层判断
#   - 与第437课 UPSERT、第208课事务直接相关
import sqlite3
import uuid


class PaymentGateway:
    """模拟支付网关：记录真实扣款次数。"""

    def __init__(self):
        self.charges = []

    def charge(self, request_id, amount):
        self.charges.append((request_id, amount))
        return {"charge_id": f"ch_{len(self.charges):04d}", "amount": amount}


conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE idempotency (
    key TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    response TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
""")
gateway = PaymentGateway()


def process_payment(idem_key: str, amount: float) -> dict:
    # 1) 先查：已处理过就直接返回旧结果
    row = conn.execute(
        "SELECT status, response FROM idempotency WHERE key = ?", (idem_key,)
    ).fetchone()
    if row:
        return {"duplicate": True, "status": row["status"], "response": row["response"]}

    # 2) 调外部支付（真实场景这里可能超时，所以必须幂等）
    result = gateway.charge(idem_key, amount)

    # 3) 写入幂等键（唯一约束兜底并发重复）
    try:
        conn.execute(
            "INSERT INTO idempotency (key, status, response) VALUES (?, 'success', ?)",
            (idem_key, str(result)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # 并发下另一个请求已经写入 → 以已存在的结果为准
        conn.rollback()
        row = conn.execute(
            "SELECT status, response FROM idempotency WHERE key = ?", (idem_key,)
        ).fetchone()
        return {"duplicate": True, "status": row["status"], "response": row["response"]}

    return {"duplicate": False, "status": "success", "response": result}


print("== 场景 1：客户端超时后重试（同一个幂等键）==")
key = str(uuid.uuid4())
print("  第一次：", process_payment(key, 99))
print("  重试  ：", process_payment(key, 99))
print("  再重试：", process_payment(key, 99))
print("  真实扣款次数：", len(gateway.charges), "（只扣了一次）")

print("\n== 场景 2：不同用户/不同订单（不同键）==")
print("  订单 A：", process_payment(str(uuid.uuid4()), 50))
print("  订单 B：", process_payment(str(uuid.uuid4()), 50))
print("  真实扣款次数：", len(gateway.charges))

print("\n== 幂等表内容 ==")
for r in conn.execute("SELECT key, status, response, created_at FROM idempotency"):
    print(f"  {r['key'][:8]}… | {r['status']} | {r['response']} | {r['created_at']}")

# ---- 幂等键怎么生成 ----
print("\n== 幂等键设计 ==")
for item in [
    "客户端生成 UUID，放在请求头 X-Idempotency-Key（推荐）",
    "业务键：订单号 + 操作类型（如 pay:order-123）",
    "键要有过期策略：太老的数据可归档，避免无限增长",
    "响应也要存：重试时返回和第一次完全相同的结果",
]:
    print("  -", item)

# ---- 哪些操作需要幂等 ----
print("\n== 适用操作 ==")
print("  必须：支付、退款、下单、扣库存、发券")
print("  不需要：查询、纯展示类接口（天然幂等）")

conn.close()

# ===== 练习题 =====
# 1. 给幂等表加“过期清理”：删除 7 天前的记录。
# 2. 支持处理中状态：第一次请求还在跑时，第二次请求返回 409/等待。
# 3. 把 process_payment 改成上下文管理器，异常时删除幂等键（允许重试）。
# 4. 思考：为什么“先查再插”在并发下不够？唯一约束如何兜底？
