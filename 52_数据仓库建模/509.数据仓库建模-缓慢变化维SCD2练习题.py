# ===== 第509课：数据仓库建模-缓慢变化维SCD2 =====
# 知识点：
#   - 维度值会变（商品改名/调价、客户换城市），历史报表要“按当时的值”统计
#   - SCD1：直接覆盖，简单但丢历史
#   - SCD2：保留多行，用 valid_from/valid_to/is_current 标记有效期
#   - 查询当前值：is_current = 1；查询历史某天：valid_from <= d < valid_to
#   - 事实表存“当时的维度代理键”，保证历史可追溯
#   - 与第488课缓存版本号、第512课拉链表的思想一致
# 依赖：无（sqlite3 内置）


def create_schema(conn):
    conn.executescript("""
    CREATE TABLE dim_product (
        sk INTEGER PRIMARY KEY AUTOINCREMENT,   -- 代理键
        product_id TEXT NOT NULL,               -- 业务键
        name TEXT NOT NULL,
        price REAL NOT NULL,
        valid_from TEXT NOT NULL,
        valid_to TEXT,                          -- NULL 表示当前有效
        is_current INTEGER NOT NULL DEFAULT 1
    );
    CREATE UNIQUE INDEX idx_product_current
        ON dim_product(product_id) WHERE is_current = 1;
    """)
    conn.commit()


def scd2_upsert(conn, product_id, name, price, changed_at):
    """有变化则关闭旧行、插入新行；无变化不动。返回是否发生变化。"""
    current = conn.execute(
        "SELECT * FROM dim_product WHERE product_id = ? AND is_current = 1",
        (product_id,),
    ).fetchone()

    if current and current["name"] == name and current["price"] == price:
        return False

    if current:
        conn.execute(
            "UPDATE dim_product SET valid_to = ?, is_current = 0 WHERE sk = ?",
            (changed_at, current["sk"]),
        )
    conn.execute("""
        INSERT INTO dim_product (product_id, name, price, valid_from, valid_to, is_current)
        VALUES (?, ?, ?, ?, NULL, 1)
    """, (product_id, name, price, changed_at))
    conn.commit()
    return True


def as_of(conn, product_id, date):
    """查询某天有效的版本。"""
    return conn.execute("""
        SELECT * FROM dim_product
        WHERE product_id = ?
          AND valid_from <= ?
          AND (valid_to IS NULL OR valid_to > ?)
    """, (product_id, date, date)).fetchone()


import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
create_schema(conn)

print("== 初始版本 ==")
scd2_upsert(conn, "P1", "机械键盘", 199.0, "2026-11-01")
scd2_upsert(conn, "P2", "无线鼠标", 99.0, "2026-11-01")
for r in conn.execute("SELECT * FROM dim_product ORDER BY sk"):
    print("  ", dict(r))

print("\n== 11-10：P1 调价到 179 ==")
changed = scd2_upsert(conn, "P1", "机械键盘", 179.0, "2026-11-10")
print("  是否变化：", changed)
for r in conn.execute("SELECT * FROM dim_product WHERE product_id='P1' ORDER BY sk"):
    print("  ", dict(r))

print("\n== 11-12：P1 改名（价格不变）==")
changed = scd2_upsert(conn, "P1", "机械键盘 Pro", 179.0, "2026-11-12")
print("  是否变化：", changed)

print("\n== 11-15：重复写入相同值 ==")
changed = scd2_upsert(conn, "P1", "机械键盘 Pro", 179.0, "2026-11-15")
print("  是否变化：", changed, "（无变化不产生新行）")

print("\n== 当前视图（is_current=1）==")
for r in conn.execute("SELECT product_id, name, price FROM dim_product WHERE is_current=1"):
    print("  ", dict(r))

print("\n== 历史时点查询 ==")
for date in ("2026-11-05", "2026-11-10", "2026-11-12", "2026-11-20"):
    row = as_of(conn, "P1", date)
    print(f"  {date}: {row['name']} / {row['price']} 元"
          f"（有效 {row['valid_from']} ~ {row['valid_to'] or '至今'}）")

print("\n== 全部历史行 ==")
for r in conn.execute("SELECT * FROM dim_product WHERE product_id='P1' ORDER BY sk"):
    print("  ", dict(r))

# ---- 事实表如何关联 ----
print("\n== 事实表应存代理键 ==")
print("  下单时的价格版本：", as_of(conn, "P1", "2026-11-08")["sk"],
      "（11-08 的有效版本）")
print("  分析 11-08 的销售额时 JOIN 这个 sk，才能得到当时的价格")
print("  如果只存 product_id 并 JOIN is_current=1，历史会被新价格覆盖")

# ---- SCD1 vs SCD2 ----
print("\n== SCD1 vs SCD2 ==")
rows = [
    ("SCD1", "覆盖原值", "省空间、查询简单", "丢失历史"),
    ("SCD2", "新增版本行", "可追溯、可复现报表", "表变大、查询要带时间条件"),
]
print(f"  {'类型':<6}{'做法':<14}{'优点':<20}{'代价'}")
for r in rows:
    print(f"  {r[0]:<6}{r[1]:<14}{r[2]:<20}{r[3]}")

# ---- 实现要点 ----
print("\n== 实现要点 ==")
for item in [
    "用部分唯一索引保证每个业务键只有一条 is_current=1",
    "valid_to 用开区间（不含），查询用 < 而不是 <=",
    "变更时间用业务时间，不要用 ETL 运行时间",
    "事实表存代理键；只存业务键会丢失历史上下文",
    "批量变更要在一个事务里完成（第208课）",
]:
    print("  -", item)

conn.close()

# ===== 练习题 =====
# 1. 给 dim_product 增加 category 字段，并处理品类变更。
# 2. 写 current_dim(conn) 视图，简化 is_current=1 查询。
# 3. 模拟“错误地只存 product_id”的查询，观察历史报表失真。
# 4. 思考：SCD2 表越来越大时，如何优化“查当前值”？
