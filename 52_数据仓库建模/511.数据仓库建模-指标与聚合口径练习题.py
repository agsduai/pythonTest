# ===== 第511课：数据仓库建模-指标与聚合口径 =====
# 知识点：
#   - 可加度量：销售额、订单数 —— 任意维度相加都有意义
#   - 半可加度量：库存、余额 —— 可按商品/门店加，不能按时间加
#   - 非可加度量：比率（客单价、转化率）—— 不能直接相加/平均
#   - 比率的正确算法：先分别汇总分子分母，再做除法
#   - “平均的平均”陷阱：各天订单量不同，直接平均日客单价会失真
#   - 同环比：本月 vs 上月（MoM）、今年 vs 去年（YoY），用窗口函数 LAG
#   - 指标口径要写进注册表（第513课），避免各部门各算各的
# 依赖：无（sqlite3 内置）

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE daily_sales (
    sale_date TEXT,
    orders INTEGER,
    revenue REAL,
    stock INTEGER
);
CREATE TABLE monthly_sales (
    month TEXT PRIMARY KEY,
    revenue REAL
);
""")

conn.executemany("INSERT INTO daily_sales VALUES (?, ?, ?, ?)", [
    ("2026-11-10", 10, 1000.0, 500),
    ("2026-11-11", 100, 5000.0, 450),
    ("2026-11-12", 20, 1400.0, 430),
])
conn.executemany("INSERT INTO monthly_sales VALUES (?, ?)", [
    ("2026-09", 10000.0), ("2026-10", 12000.0), ("2026-11", 15000.0),
])
conn.commit()

print("== 每日数据 ==")
for r in conn.execute("SELECT * FROM daily_sales"):
    aov = r["revenue"] / r["orders"]
    print(f"  {r['sale_date']} 订单 {r['orders']:3d}，收入 {r['revenue']:7.0f}，客单价 {aov:6.2f}")

# ---- 可加 vs 半可加 ----
print("\n== 可加性 ==")
total_revenue = conn.execute("SELECT SUM(revenue) FROM daily_sales").fetchone()[0]
total_orders = conn.execute("SELECT SUM(orders) FROM daily_sales").fetchone()[0]
print(f"  销售额可加：{total_revenue:.0f}")
print(f"  订单数可加：{total_orders}")

print(f"  库存（三天分别 500/450/430）：")
print("    按商品加总（同一天）有意义；把三天相加 = 1380 没有业务含义")
print("    正确看“期末库存”= 最后一天 430，或“平均库存”= (500+450+430)/3")

# ---- 比率的正确算法 ----
print("\n== 客单价：正确 vs 错误 ==")
correct_aov = total_revenue / total_orders
wrong_aov = sum((r["revenue"] / r["orders"]) for r in conn.execute("SELECT * FROM daily_sales")) / 3
print(f"  正确（总收/总单）：{correct_aov:.2f}")
print(f"  错误（日客单价平均）：{wrong_aov:.2f}")
print("  差异原因：11-11 订单多，客单价低，但它在“平均的日客单价”里权重被放大")

# ---- 同环比 ----
print("\n== 环比（MoM）==")
rows = conn.execute("""
    SELECT month, revenue,
           LAG(revenue) OVER (ORDER BY month) AS prev_revenue
    FROM monthly_sales ORDER BY month
""").fetchall()
for r in rows:
    if r["prev_revenue"] is None:
        print(f"  {r['month']}: {r['revenue']:.0f}（无上月）")
    else:
        mom = (r["revenue"] - r["prev_revenue"]) / r["prev_revenue"]
        print(f"  {r['month']}: {r['revenue']:.0f}，环比 {mom:+.1%}")

print("\n== 同比（YoY）==")
print("  同比 = 本月 vs 去年同月；没有去年同期数据时无法计算")
print("  同比能排除季节性，环比更敏感 —— 两个一起看")

# ---- 常见指标口径 ----
print("\n== 常见指标口径 ==")
rows = [
    ("GMV", "SUM(订单金额)", "可加", "含未支付？要写清"),
    ("客单价 AOV", "SUM(金额)/COUNT(订单)", "比率", "先汇总再除"),
    ("转化率", "支付人数/访问人数", "比率", "分子分母同口径"),
    ("复购率", ">=2 单用户/总用户", "比率", "时间窗口要固定"),
    ("库存周转", "出库量/平均库存", "比率", "平均库存怎么算要约定"),
]
print(f"  {'指标':<10}{'公式':<24}{'类型':<6}{'注意'}")
for r in rows:
    print(f"  {r[0]:<10}{r[1]:<24}{r[2]:<6}{r[3]}")

# ---- 口径不一致的后果 ----
print("\n== 口径不一致的后果 ==")
for item in [
    "运营说转化率 10%，财务说 8%：一个按访客、一个按下单用户",
    "GMV 含退款 vs 不含退款，差出几个百分点",
    "“月活”按登录算还是按有行为算，结果完全不同",
    "解决：指标注册表 + 统一 SQL/语义层（第513课）",
]:
    print("  -", item)

conn.close()

# ===== 练习题 =====
# 1. 用 daily_sales 计算“日均收入”和“平均日客单价”，对比总客单价。
# 2. 给 monthly_sales 增加去年同期数据，计算 YoY。
# 3. 定义“退款率”的口径，并说明需要哪些字段。
# 4. 思考：为什么比率指标不能按维度直接相加？
