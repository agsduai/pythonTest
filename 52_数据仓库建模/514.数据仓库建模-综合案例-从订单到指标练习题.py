# ===== 第514课：数据仓库建模-综合案例-从订单到指标 =====
# 知识点：
#   - 综合运用：星型模型（508）+ SCD2（509）+ 快照（510）+ 指标口径（511）
#   - 流程：原始订单 → 维度（商品/日期/门店）→ 事实表 → 指标查询
#   - 商品价格会变：事实表存“下单时的价格”和“商品版本代理键”
#   - 指标：销售额、订单数、客单价、Top 商品、每日趋势
#   - 所有查询只依赖维度/事实表，不碰原始业务表
# 依赖：无（sqlite3 内置）

import random
import sqlite3

random.seed(2026)

# ---------------- 1. 原始数据（模拟业务库） ----------------
RAW_ORDERS = []
for i in range(1, 61):
    day = random.choice([10, 11, 12])
    product = random.choice(["P1", "P2", "P3", "P4"])
    qty = random.randint(1, 3)
    status = random.choices(["paid", "refunded"], weights=[9, 1])[0]
    RAW_ORDERS.append({
        "order_id": f"O{i:03d}",
        "product_id": product,
        "store_id": random.choice(["S1", "S2", "S3"]),
        "qty": qty,
        "status": status,
        "created_at": f"2026-11-{day:02d} {random.randint(8, 21):02d}:00:00",
        "updated_at": f"2026-11-{day:02d} {random.randint(8, 21):02d}:30:00",
    })

# 商品价格历史：P1 在 11-11 调价，P3 在 11-12 调价
PRICE_HISTORY = {
    "P1": [("2026-11-01", 199.0), ("2026-11-11", 179.0)],
    "P2": [("2026-11-01", 99.0)],
    "P3": [("2026-11-01", 1299.0), ("2026-11-12", 1199.0)],
    "P4": [("2026-11-01", 5999.0)],
}
PRODUCT_META = {
    "P1": ("机械键盘", "外设", "A厂"),
    "P2": ("无线鼠标", "外设", "B厂"),
    "P3": ("显示器", "显示设备", "A厂"),
    "P4": ("笔记本", "电脑", "C厂"),
}
STORE_META = {
    "S1": ("北京旗舰店", "北京", "华北"),
    "S2": ("上海店", "上海", "华东"),
    "S3": ("广州店", "广州", "华南"),
}


def price_on(product, date):
    """取某天有效的价格。"""
    current = None
    for start, price in PRICE_HISTORY[product]:
        if start <= date:
            current = price
    return current


# ---------------- 2. 建仓库 ----------------
conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE dim_date (
    date_id TEXT PRIMARY KEY, year INTEGER, month INTEGER, day INTEGER, weekday TEXT
);
CREATE TABLE dim_product (
    sk INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT, name TEXT, category TEXT, brand TEXT,
    price REAL, valid_from TEXT, valid_to TEXT, is_current INTEGER DEFAULT 1
);
CREATE TABLE dim_store (
    store_id TEXT PRIMARY KEY, name TEXT, city TEXT, region TEXT
);
CREATE TABLE fact_sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT, date_id TEXT, product_sk INTEGER, store_id TEXT,
    quantity INTEGER, unit_price REAL, amount REAL, status TEXT
);
""")

# 日期维度
for day in (10, 11, 12):
    conn.execute("INSERT INTO dim_date VALUES (?, ?, ?, ?, ?)",
                 (f"2026-11-{day:02d}", 2026, 11, day, "周" + "一二三四五六日"[day % 7]))

# 门店维度
for sid, (name, city, region) in STORE_META.items():
    conn.execute("INSERT INTO dim_store VALUES (?, ?, ?, ?)", (sid, name, city, region))

# 商品维度：展开价格历史（SCD2 简化版）
for pid, (name, category, brand) in PRODUCT_META.items():
    versions = PRICE_HISTORY[pid]
    for i, (start, price) in enumerate(versions):
        end = versions[i + 1][0] if i + 1 < len(versions) else None
        conn.execute("""
            INSERT INTO dim_product
            (product_id, name, category, brand, price, valid_from, valid_to, is_current)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (pid, name, category, brand, price, start, end,
              1 if end is None else 0))
conn.commit()


def product_sk(conn, product_id, date):
    row = conn.execute("""
        SELECT sk FROM dim_product
        WHERE product_id = ? AND valid_from <= ?
          AND (valid_to IS NULL OR valid_to > ?)
        ORDER BY valid_from DESC LIMIT 1
    """, (product_id, date, date)).fetchone()
    return row["sk"]


# ---------------- 3. 灌入事实表 ----------------
for order in RAW_ORDERS:
    date = order["created_at"][:10]
    sk = product_sk(conn, order["product_id"], date)
    unit_price = price_on(order["product_id"], date)
    conn.execute("""
        INSERT INTO fact_sales
        (order_id, date_id, product_sk, store_id, quantity, unit_price, amount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (order["order_id"], date, sk, order["store_id"],
          order["qty"], unit_price, order["qty"] * unit_price, order["status"]))
conn.commit()

print(f"原始订单 {len(RAW_ORDERS)} 条，事实表 "
      f"{conn.execute('SELECT COUNT(*) FROM fact_sales').fetchone()[0]} 行")

# ---------------- 4. 指标查询 ----------------
print("\n== 1. 每日销售额（仅已支付）==")
rows = conn.execute("""
    SELECT date_id, SUM(amount) AS revenue, COUNT(*) AS orders
    FROM fact_sales WHERE status = 'paid'
    GROUP BY date_id ORDER BY date_id
""").fetchall()
total_revenue = total_orders = 0
for r in rows:
    total_revenue += r["revenue"]
    total_orders += r["orders"]
    print(f"  {r['date_id']}: {r['revenue']:9.0f} 元，{r['orders']} 单")

aov = total_revenue / total_orders
print(f"  合计：{total_revenue:.0f} 元，{total_orders} 单，客单价 {aov:.2f} 元")

print("\n== 2. 品类销售占比 ==")
rows = conn.execute("""
    SELECT p.category, SUM(f.amount) AS revenue
    FROM fact_sales f JOIN dim_product p ON p.sk = f.product_sk
    WHERE f.status = 'paid'
    GROUP BY p.category ORDER BY revenue DESC
""").fetchall()
for r in rows:
    print(f"  {r['category']:6s} {r['revenue']:9.0f} 元（{r['revenue'] / total_revenue:.1%}）")

print("\n== 3. Top 5 商品 ==")
rows = conn.execute("""
    SELECT p.name, SUM(f.quantity) AS qty, SUM(f.amount) AS revenue
    FROM fact_sales f JOIN dim_product p ON p.sk = f.product_sk
    WHERE f.status = 'paid'
    GROUP BY p.product_id ORDER BY revenue DESC LIMIT 5
""").fetchall()
for i, r in enumerate(rows, 1):
    print(f"  {i}. {r['name']:6s} {r['qty']:3d} 件，{r['revenue']:9.0f} 元")

print("\n== 4. 门店 × 品类交叉 ==")
rows = conn.execute("""
    SELECT s.name AS store, p.category AS category, SUM(f.amount) AS revenue
    FROM fact_sales f
    JOIN dim_product p ON p.sk = f.product_sk
    JOIN dim_store s ON s.store_id = f.store_id
    WHERE f.status = 'paid'
    GROUP BY s.name, p.category ORDER BY s.name, revenue DESC
""").fetchall()
current_store = None
for r in rows:
    if r["store"] != current_store:
        current_store = r["store"]
        print(f"  {current_store}:")
    print(f"    {r['category']:6s} {r['revenue']:9.0f}")

print("\n== 5. 退款率 ==")
refund = conn.execute(
    "SELECT COUNT(*) FROM fact_sales WHERE status='refunded'").fetchone()[0]
all_orders = conn.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
print(f"  退款 {refund}/{all_orders} = {refund / all_orders:.1%}")

print("\n== 6. 价格版本验证 ==")
rows = conn.execute("""
    SELECT p.product_id, p.price, p.valid_from, p.valid_to,
           COUNT(f.sale_id) AS sales
    FROM dim_product p LEFT JOIN fact_sales f ON f.product_sk = p.sk
    GROUP BY p.sk ORDER BY p.product_id, p.valid_from
""").fetchall()
for r in rows:
    print(f"  {r['product_id']} {r['price']:7.0f} 元 "
          f"[{r['valid_from']} ~ {r['valid_to'] or '至今'}] 关联销售 {r['sales']} 行")

# ---------------- 5. 交付清单 ----------------
print("\n== 交付清单 ==")
for item in [
    "dim_date / dim_product(SCD2) / dim_store",
    "fact_sales：粒度=订单行，存 unit_price 与 amount",
    "指标：每日销售额、客单价、品类占比、Top 商品、退款率",
    "历史可追溯：调价前的订单仍按下单价计算",
    "所有查询只 JOIN 维度与事实表",
]:
    print("  -", item)

conn.close()

# ===== 练习题 =====
# 1. 增加“用户”维度，并统计新老用户销售额占比。
# 2. 把“退款”从销售额中扣除，重新计算客单价。
# 3. 增加“每日累计销售额”（窗口函数）。
# 4. 思考：如果事实表只存 product_id 不存 sk，会丢失什么？
