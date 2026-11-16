# ===== 第507课：数据仓库建模-维度建模概述 =====
# 知识点：
#   - OLTP（业务库）vs OLAP（分析库）：前者重事务，后者重聚合查询
#   - 维度建模：事实表（度量）+ 维度表（描述），组成星型结构
#   - 事实表：一行一条业务事件（订单行/支付/点击），含外键与数值度量
#   - 维度表：描述“谁、何时、何地、什么”，通常宽表、冗余、易读
#   - 粒度（grain）：事实表一行代表什么，必须在建模前定清楚
#   - 与第13/25章的区别：那里是业务 CRUD，这里是为分析而组织
# 依赖：无（sqlite3 内置）

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
-- 维度：日期
CREATE TABLE dim_date (
    date_id TEXT PRIMARY KEY,      -- 2026-11-12
    year INTEGER, month INTEGER, day INTEGER, weekday TEXT
);
-- 维度：商品
CREATE TABLE dim_product (
    product_id TEXT PRIMARY KEY,
    name TEXT, category TEXT, brand TEXT
);
-- 维度：门店
CREATE TABLE dim_store (
    store_id TEXT PRIMARY KEY,
    name TEXT, city TEXT, region TEXT
);
-- 事实：销售明细（粒度 = 一个订单行）
CREATE TABLE fact_sales (
    sale_id INTEGER PRIMARY KEY,
    date_id TEXT REFERENCES dim_date(date_id),
    product_id TEXT REFERENCES dim_product(product_id),
    store_id TEXT REFERENCES dim_store(store_id),
    quantity INTEGER,
    amount REAL
);
""")

conn.executemany("INSERT INTO dim_date VALUES (?, ?, ?, ?, ?)", [
    ("2026-11-10", 2026, 11, 10, "周二"),
    ("2026-11-11", 2026, 11, 11, "周三"),
    ("2026-11-12", 2026, 11, 12, "周四"),
])
conn.executemany("INSERT INTO dim_product VALUES (?, ?, ?, ?)", [
    ("P1", "机械键盘", "外设", "A厂"),
    ("P2", "无线鼠标", "外设", "B厂"),
    ("P3", "显示器", "显示设备", "A厂"),
])
conn.executemany("INSERT INTO dim_store VALUES (?, ?, ?, ?)", [
    ("S1", "北京旗舰店", "北京", "华北"),
    ("S2", "上海店", "上海", "华东"),
])
conn.executemany("INSERT INTO fact_sales VALUES (?, ?, ?, ?, ?, ?)", [
    (1, "2026-11-10", "P1", "S1", 2, 398.0),
    (2, "2026-11-10", "P2", "S1", 1, 99.0),
    (3, "2026-11-11", "P3", "S2", 1, 1299.0),
    (4, "2026-11-11", "P1", "S2", 3, 597.0),
    (5, "2026-11-12", "P2", "S1", 2, 198.0),
    (6, "2026-11-12", "P3", "S1", 1, 1299.0),
])
conn.commit()

print("== 表结构 ==")
for table in ("dim_date", "dim_product", "dim_store", "fact_sales"):
    cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table})")]
    print(f"  {table}: {cols}")

print("\n== 事实表（明细）==")
for r in conn.execute("SELECT * FROM fact_sales ORDER BY sale_id"):
    print("  ", dict(r))

print("\n== 星型查询：按品类汇总销售额 ==")
rows = conn.execute("""
    SELECT p.category AS 品类,
           SUM(f.amount) AS 销售额,
           SUM(f.quantity) AS 销量,
           COUNT(*) AS 订单行数
    FROM fact_sales f
    JOIN dim_product p ON p.product_id = f.product_id
    GROUP BY p.category
    ORDER BY 销售额 DESC
""").fetchall()
for r in rows:
    print(f"  {r['品类']:6s} {r['销售额']:8.0f} 元 | {r['销量']} 件 | {r['订单行数']} 行")

print("\n== 按城市 + 日期 ==")
rows = conn.execute("""
    SELECT d.date_id AS 日期, s.city AS 城市, SUM(f.amount) AS 销售额
    FROM fact_sales f
    JOIN dim_date d ON d.date_id = f.date_id
    JOIN dim_store s ON s.store_id = f.store_id
    GROUP BY d.date_id, s.city
    ORDER BY d.date_id, s.city
""").fetchall()
for r in rows:
    print(f"  {r['日期']} {r['城市']:3s} {r['销售额']:8.0f}")

# ---- 建模检查清单 ----
print("\n== 建模前必须回答 ==")
for item in [
    "事实表的粒度是什么？（订单行 / 支付 / 每日快照）",
    "维度有哪些？（时间/商品/门店/用户/渠道）",
    "度量有哪些？（金额/数量/次数，必须可加或可半加）",
    "维度是否需要历史追踪？（SCD2，第509课）",
    "查询主要按什么切片？（决定索引与预聚合）",
]:
    print("  -", item)

conn.close()

# ===== 练习题 =====
# 1. 增加 dim_user 维度，并给 fact_sales 加 user_id 外键。
# 2. 查询“华北区域各品类销售额”。
# 3. 计算每个门店的客单价（销售额 / 订单行数）。
# 4. 思考：为什么维度表通常允许冗余（城市+区域都存）？
