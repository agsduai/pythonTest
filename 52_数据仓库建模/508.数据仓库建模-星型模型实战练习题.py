# ===== 第508课：数据仓库建模-星型模型实战 =====
# 知识点：
#   - 星型模型：一个事实表居中，多个维度表围绕，JOIN 路径短
#   - 雪花模型：维度再拆子维度（如商品→品类→部门），规范化但 JOIN 多
#   - 星型优先：分析查询简单、性能好；冗余换可读性
#   - 常用查询模式：切片（WHERE 维度）、钻取（GROUP BY 更细粒度）、汇总
#   - 维度表要有稳定的代理键（surrogate key），业务键只做唯一约束
#   - 与第25章 JOIN 的区别：这里是“为分析设计的表结构”
# 依赖：无（sqlite3 内置）

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE dim_date (
    date_id TEXT PRIMARY KEY, year INTEGER, month INTEGER, day INTEGER,
    week INTEGER, weekday TEXT
);
CREATE TABLE dim_product (
    product_id TEXT PRIMARY KEY, name TEXT, category TEXT, brand TEXT
);
CREATE TABLE dim_store (
    store_id TEXT PRIMARY KEY, name TEXT, city TEXT, region TEXT
);
CREATE TABLE fact_sales (
    sale_id INTEGER PRIMARY KEY,
    date_id TEXT, product_id TEXT, store_id TEXT,
    quantity INTEGER, amount REAL
);
""")

# 维度数据
dates = []
for day in range(1, 13):
    dates.append((f"2026-11-{day:02d}", 2026, 11, day, 46 + day // 7,
                  "周" + "一二三四五六日"[day % 7]))
conn.executemany("INSERT INTO dim_date VALUES (?, ?, ?, ?, ?, ?)", dates)
conn.executemany("INSERT INTO dim_product VALUES (?, ?, ?, ?)", [
    ("P1", "机械键盘", "外设", "A厂"),
    ("P2", "无线鼠标", "外设", "B厂"),
    ("P3", "显示器", "显示设备", "A厂"),
    ("P4", "笔记本", "电脑", "C厂"),
])
conn.executemany("INSERT INTO dim_store VALUES (?, ?, ?, ?)", [
    ("S1", "北京旗舰店", "北京", "华北"),
    ("S2", "上海店", "上海", "华东"),
    ("S3", "广州店", "广州", "华南"),
])

# 事实数据：12 天 × 随机组合
import random
random.seed(7)
sales = []
sale_id = 1
for day in range(1, 13):
    for _ in range(4):
        product = random.choice(["P1", "P2", "P3", "P4"])
        store = random.choice(["S1", "S2", "S3"])
        qty = random.randint(1, 3)
        price = {"P1": 199, "P2": 99, "P3": 1299, "P4": 5999}[product]
        sales.append((sale_id, f"2026-11-{day:02d}", product, store, qty, qty * price))
        sale_id += 1
conn.executemany("INSERT INTO fact_sales VALUES (?, ?, ?, ?, ?, ?)", sales)
conn.commit()

print(f"事实行数：{len(sales)}")

print("\n== 1. 切片：华北区域销售额 ==")
rows = conn.execute("""
    SELECT s.city, SUM(f.amount) AS total
    FROM fact_sales f JOIN dim_store s ON s.store_id = f.store_id
    WHERE s.region = '华北'
    GROUP BY s.city
""").fetchall()
for r in rows:
    print(f"  {r['city']}: {r['total']:.0f} 元")

print("\n== 2. 钻取：品类 → 商品 → 门店 ==")
rows = conn.execute("""
    SELECT p.category AS 品类, p.name AS 商品, s.name AS 门店, SUM(f.amount) AS 销售额
    FROM fact_sales f
    JOIN dim_product p ON p.product_id = f.product_id
    JOIN dim_store s ON s.store_id = f.store_id
    GROUP BY p.category, p.name, s.name
    ORDER BY 销售额 DESC
    LIMIT 6
""").fetchall()
for r in rows:
    print(f"  {r['品类']:5s} {r['商品']:6s} {r['门店']:6s} {r['销售额']:9.0f}")

print("\n== 3. 时间趋势：按周汇总 ==")
rows = conn.execute("""
    SELECT d.week AS 周, SUM(f.amount) AS 销售额, SUM(f.quantity) AS 销量
    FROM fact_sales f JOIN dim_date d ON d.date_id = f.date_id
    GROUP BY d.week ORDER BY d.week
""").fetchall()
for r in rows:
    print(f"  第 {r['周']} 周：{r['销售额']:9.0f} 元，{r['销量']} 件")

print("\n== 4. 门店排行（含占比）==")
rows = conn.execute("""
    SELECT s.name AS 门店, SUM(f.amount) AS 销售额
    FROM fact_sales f JOIN dim_store s ON s.store_id = f.store_id
    GROUP BY s.store_id
    ORDER BY 销售额 DESC
""").fetchall()
grand = sum(r["销售额"] for r in rows)
for r in rows:
    share = r["销售额"] / grand
    bar = "█" * int(share * 30)
    print(f"  {r['门店']:8s} {r['销售额']:9.0f} 元 {share:6.1%} {bar}")

print("\n== 5. 交叉表：品类 × 区域 ==")
rows = conn.execute("""
    SELECT p.category AS 品类,
           SUM(CASE WHEN s.region = '华北' THEN f.amount ELSE 0 END) AS 华北,
           SUM(CASE WHEN s.region = '华东' THEN f.amount ELSE 0 END) AS 华东,
           SUM(CASE WHEN s.region = '华南' THEN f.amount ELSE 0 END) AS 华南
    FROM fact_sales f
    JOIN dim_product p ON p.product_id = f.product_id
    JOIN dim_store s ON s.store_id = f.store_id
    GROUP BY p.category
    ORDER BY p.category
""").fetchall()
print(f"  {'品类':<6}{'华北':>9}{'华东':>9}{'华南':>9}")
for r in rows:
    print(f"  {r['品类']:<6}{r['华北']:>9.0f}{r['华东']:>9.0f}{r['华南']:>9.0f}")

# ---- 星型 vs 雪花 ----
print("\n== 星型 vs 雪花 ==")
rows = [
    ("星型", "维度冗余、JOIN 少", "查询快、易理解", "存储略多"),
    ("雪花", "维度规范化、JOIN 多", "省空间、一致性高", "查询复杂、性能差"),
]
print(f"  {'模型':<6}{'特点':<18}{'优点':<16}{'代价'}")
for r in rows:
    print(f"  {r[0]:<6}{r[1]:<18}{r[2]:<16}{r[3]}")
print("  分析型仓库通常优先星型；维度特别大且复用高时才雪花")

conn.close()

# ===== 练习题 =====
# 1. 增加“渠道”维度（线上/线下），并做渠道×品类交叉表。
# 2. 查询每个门店销售额最高的商品。
# 3. 计算各区域的“客单价”（销售额 / 订单行数）。
# 4. 思考：为什么事实表通常不存“商品名称”，而存 product_id？
