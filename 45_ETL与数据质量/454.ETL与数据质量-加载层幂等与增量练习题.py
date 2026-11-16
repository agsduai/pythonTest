# ===== 第454课：ETL与数据质量-加载层幂等与增量 =====
# 知识点：
#   - 加载层第一要求：可重跑（幂等），否则重跑一次就重复一份数据
#   - 实现：目标表建唯一键，用 UPSERT（第437课）写入
#   - 增量：记录 watermark（上次成功处理到的最大更新时间）
#   - 流程：读 watermark → 只取新数据 → UPSERT → 更新 watermark（同一事务）
#   - watermark 用“源数据的最大 updated_at”，不要用本机当前时间
import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
-- 源表（模拟业务库）
CREATE TABLE source_orders (
    order_id TEXT PRIMARY KEY,
    amount REAL,
    status TEXT,
    updated_at TEXT
);
-- 目标表（数据仓库）
CREATE TABLE dw_orders (
    order_id TEXT PRIMARY KEY,
    amount REAL,
    status TEXT,
    updated_at TEXT,
    loaded_at TEXT DEFAULT (datetime('now'))
);
-- ETL 状态表
CREATE TABLE etl_state (
    job TEXT PRIMARY KEY,
    watermark TEXT
);
""")
conn.executemany(
    "INSERT INTO source_orders VALUES (?, ?, ?, ?)",
    [
        ("A001", 99.5, "paid", "2026-11-12 10:00:00"),
        ("A002", 199, "paid", "2026-11-12 10:05:00"),
        ("A003", 50, "refunded", "2026-11-12 10:10:00"),
    ],
)
conn.commit()


def get_watermark(job="orders") -> str:
    row = conn.execute("SELECT watermark FROM etl_state WHERE job = ?", (job,)).fetchone()
    return row["watermark"] if row else "1970-01-01 00:00:00"


def load_incremental(job="orders") -> int:
    watermark = get_watermark(job)
    rows = conn.execute("""
        SELECT * FROM source_orders
        WHERE updated_at > ?
        ORDER BY updated_at
    """, (watermark,)).fetchall()
    if not rows:
        print(f"  水位 {watermark} → 没有新数据")
        return 0

    max_updated = watermark
    for r in rows:
        conn.execute("""
            INSERT INTO dw_orders (order_id, amount, status, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(order_id) DO UPDATE SET
                amount = excluded.amount,
                status = excluded.status,
                updated_at = excluded.updated_at,
                loaded_at = datetime('now')
        """, (r["order_id"], r["amount"], r["status"], r["updated_at"]))
        max_updated = max(max_updated, r["updated_at"])

    conn.execute("""
        INSERT INTO etl_state (job, watermark) VALUES (?, ?)
        ON CONFLICT(job) DO UPDATE SET watermark = excluded.watermark
    """, (job, max_updated))
    conn.commit()
    print(f"  水位 {watermark} → {max_updated}，加载 {len(rows)} 条")
    return len(rows)


print("== 第一次运行 ==")
load_incremental()
print("目标表：", [dict(r) for r in conn.execute("SELECT * FROM dw_orders ORDER BY order_id")])

print("\n== 第二次运行（无新数据，幂等）==")
load_incremental()
print("目标表行数：", conn.execute("SELECT COUNT(*) FROM dw_orders").fetchone()[0])

print("\n== 源表更新：A002 状态变化 + 新增 A004 ==")
conn.execute("UPDATE source_orders SET status = 'refunded', updated_at = '2026-11-12 11:00:00' "
             "WHERE order_id = 'A002'")
conn.execute("INSERT INTO source_orders VALUES ('A004', 399, 'paid', '2026-11-12 11:05:00')")
conn.commit()
load_incremental()

print("\n== 最终目标表 ==")
for r in conn.execute("SELECT * FROM dw_orders ORDER BY order_id"):
    print(f"  {r['order_id']} {r['amount']:6.1f} {r['status']:9s} "
          f"updated={r['updated_at']} loaded={r['loaded_at']}")

print("\n== 校验 ==")
print("  源表行数：", conn.execute("SELECT COUNT(*) FROM source_orders").fetchone()[0])
print("  目标行数：", conn.execute("SELECT COUNT(*) FROM dw_orders").fetchone()[0])
print("  水位：", get_watermark())
print("  A002 状态已更新为：", conn.execute(
    "SELECT status FROM dw_orders WHERE order_id='A002'").fetchone()[0])

# ---- 常见坑 ----
print("\n== 常见坑 ==")
for item in [
    "用当前时间当水位：源库延迟写入的数据会被跳过 → 用源数据的 updated_at",
    "先更新水位再写数据：写失败后数据永久丢失 → 同一事务里做",
    "没有唯一键：UPSERT 无法去重 → 目标表必须有业务主键",
    "时区不一致：字符串比较会乱序 → 统一 UTC 或统一格式",
    "物理删除同步：源删除的数据目标还在 → 另做 delete 标记或全量对账",
]:
    print("  -", item)

conn.close()

# ===== 练习题 =====
# 1. 给 etl_state 增加 last_run_at 与 rows_loaded 字段，记录每次运行。
# 2. 实现全量加载模式：先 TRUNCATE 再灌，和增量模式对比。
# 3. 模拟“写目标成功但水位更新失败”，验证事务回滚后数据不会丢。
# 4. 思考：如果源表用自增 id 而不是 updated_at 做水位，有什么风险？
