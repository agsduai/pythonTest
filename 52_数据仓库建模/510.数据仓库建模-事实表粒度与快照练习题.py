# ===== 第510课：数据仓库建模-事实表粒度与快照 =====
# 知识点：
#   - 事实表三种常见类型：
#     1. 事务事实表：一行一个事件（订单行、支付），最细粒度
#     2. 周期快照表：一行一个周期（每日库存/余额），可加性差但查询快
#     3. 累积快照表：一行一个流程（订单从下单到完成），记录各里程碑时间
#   - 粒度决定“能回答什么问题”：事务表能还原任意聚合，快照表不能
#   - 快照是“用空间换查询速度”，也是半可加度量（库存不能跨天相加）
#   - 累积快照适合算“各阶段耗时/转化率”
#   - 与第507课“先定粒度”呼应
# 依赖：无（sqlite3 内置）

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
-- 事务事实表：一行一个订单事件
CREATE TABLE fact_order_event (
    event_id INTEGER PRIMARY KEY,
    order_id TEXT,
    product_id TEXT,
    event_type TEXT,          -- created / paid / shipped / completed
    quantity INTEGER,
    amount REAL,
    event_time TEXT
);
-- 周期快照：每日库存
CREATE TABLE snapshot_stock (
    snap_date TEXT,
    product_id TEXT,
    stock INTEGER,
    PRIMARY KEY (snap_date, product_id)
);
-- 累积快照：订单生命周期
CREATE TABLE accumulating_order (
    order_id TEXT PRIMARY KEY,
    created_at TEXT,
    paid_at TEXT,
    shipped_at TEXT,
    completed_at TEXT,
    amount REAL
);
""")

# ---- 事务事实数据 ----
events = [
    (1, "O1", "P1", "created", 2, 398.0, "2026-11-10 09:00:00"),
    (2, "O1", "P1", "paid", 2, 398.0, "2026-11-10 09:05:00"),
    (3, "O1", "P1", "shipped", 2, 398.0, "2026-11-11 10:00:00"),
    (4, "O1", "P1", "completed", 2, 398.0, "2026-11-13 18:00:00"),
    (5, "O2", "P2", "created", 1, 99.0, "2026-11-10 11:00:00"),
    (6, "O2", "P2", "paid", 1, 99.0, "2026-11-10 11:02:00"),
    (7, "O3", "P3", "created", 1, 1299.0, "2026-11-12 15:00:00"),
    (8, "O3", "P3", "paid", 1, 1299.0, "2026-11-12 15:01:00"),
]
conn.executemany("INSERT INTO fact_order_event VALUES (?, ?, ?, ?, ?, ?, ?)", events)
conn.commit()

print("== 1. 事务事实表：从事件还原订单 ==")
rows = conn.execute("""
    SELECT order_id, product_id, MAX(amount) AS amount,
           MIN(CASE WHEN event_type='created' THEN event_time END) AS created,
           MIN(CASE WHEN event_type='paid' THEN event_time END) AS paid,
           MIN(CASE WHEN event_type='completed' THEN event_time END) AS completed
    FROM fact_order_event
    GROUP BY order_id
""").fetchall()
for r in rows:
    print(f"  {r['order_id']} {r['product_id']} {r['amount']:.0f} 元 | "
          f"下单 {r['created']} | 支付 {r['paid']} | 完成 {r['completed'] or '未完成'}")

# ---- 2. 周期快照：每日库存 ----
print("\n== 2. 周期快照：每日库存 ==")
stock_data = [
    ("2026-11-10", "P1", 100), ("2026-11-10", "P2", 200),
    ("2026-11-11", "P1", 98), ("2026-11-11", "P2", 199),
    ("2026-11-12", "P1", 98), ("2026-11-12", "P2", 198),
]
conn.executemany("INSERT INTO snapshot_stock VALUES (?, ?, ?)", stock_data)
conn.commit()
for r in conn.execute("SELECT * FROM snapshot_stock ORDER BY snap_date, product_id"):
    print("  ", dict(r))

print("\n  快照能回答：每天库存是多少")
print("  快照不能回答：11-10 到 11-12 之间任意时刻的库存")
print("  库存是半可加度量：可以按商品加总，但不能把几天库存相加")

# ---- 3. 累积快照：订单生命周期 ----
print("\n== 3. 累积快照：订单里程碑 ==")
conn.execute("""
    INSERT INTO accumulating_order
    SELECT order_id, MAX(amount),
           MIN(CASE WHEN event_type='created' THEN event_time END),
           MIN(CASE WHEN event_type='paid' THEN event_time END),
           MIN(CASE WHEN event_type='shipped' THEN event_time END),
           MIN(CASE WHEN event_type='completed' THEN event_time END)
    FROM fact_order_event
    GROUP BY order_id
""")
conn.commit()
for r in conn.execute("SELECT * FROM accumulating_order ORDER BY order_id"):
    print("  ", dict(r))

print("\n== 阶段耗时（小时）==")
rows = conn.execute("""
    SELECT order_id,
           ROUND((julianday(paid_at) - julianday(created_at)) * 24, 2) AS 支付耗时,
           ROUND((julianday(shipped_at) - julianday(paid_at)) * 24, 2) AS 发货耗时,
           ROUND((julianday(completed_at) - julianday(shipped_at)) * 24, 2) AS 确认耗时
    FROM accumulating_order
""").fetchall()
for r in rows:
    print(f"  {r['order_id']}: 支付 {r['支付耗时']}h | "
          f"发货 {r['发货耗时']}h | 确认 {r['确认耗时']}h")

# ---- 4. 三种事实表对比 ----
print("\n== 三种事实表对比 ==")
rows = [
    ("事务事实表", "一个事件一行", "最细、可还原任意聚合", "数据量大"),
    ("周期快照", "一个周期一行", "查询快、趋势直观", "只保留周期点"),
    ("累积快照", "一个流程一行", "算阶段耗时/转化", "需随流程更新"),
]
print(f"  {'类型':<10}{'粒度':<14}{'优点':<24}{'代价'}")
for r in rows:
    print(f"  {r[0]:<10}{r[1]:<14}{r[2]:<24}{r[3]}")

# ---- 选型建议 ----
print("\n== 选型建议 ==")
for item in [
    "要支持任意维度下钻 → 事务事实表（最灵活）",
    "固定看每日/每月余额、库存 → 周期快照",
    "看订单全流程耗时、转化率 → 累积快照",
    "同一份数据可以同时建事务表 + 快照表（空间换速度）",
    "快照表的日期要连续补全（无数据也要有一行 0/上次值）",
]:
    print("  -", item)

conn.close()

# ===== 练习题 =====
# 1. 给 snapshot_stock 补全 11-13 的库存（沿用前一天的 98/198）。
# 2. 用事务事实表计算“每日支付金额”，并与快照对比。
# 3. 给累积快照增加“取消时间”，计算取消率。
# 4. 思考：为什么“库存天数”不能简单把每天库存相加再除以天数？
