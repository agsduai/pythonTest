# ===== 第513课：数据仓库建模-数据血缘与指标口径 =====
# 知识点：
#   - 数据血缘：表/字段/指标之间的上下游关系，回答“这个数从哪来、改了会影响谁”
#   - 指标注册表：指标名、口径定义、负责人、来源表、更新频率
#   - 影响分析：某张源表要改，沿着血缘找下游表/指标/报表
#   - 用递归 CTE（第436课）沿有向边遍历下游
#   - 口径统一的价值：避免“同名指标不同数”，也是数据治理的基础
#   - 与第45章 ETL、第511课指标口径直接相关
# 依赖：无（sqlite3 内置）

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE lineage (
    upstream TEXT NOT NULL,      -- 上游表/字段
    downstream TEXT NOT NULL,    -- 下游表/字段
    relation TEXT,               -- 加工方式：join/aggregate/derive
    PRIMARY KEY (upstream, downstream)
);
CREATE TABLE metric_registry (
    metric TEXT PRIMARY KEY,
    definition TEXT NOT NULL,
    owner TEXT,
    source_tables TEXT,
    refresh TEXT
);
""")

# ---- 血缘关系 ----
LINEAGE = [
    ("raw_orders", "stg_orders", "clean"),
    ("raw_users", "stg_users", "clean"),
    ("stg_orders", "fact_sales", "join+aggregate"),
    ("stg_users", "dim_user", "dedup"),
    ("fact_sales", "metric_revenue", "sum(amount)"),
    ("fact_sales", "metric_aov", "sum(amount)/count(order_id)"),
    ("dim_user", "metric_new_users", "count(distinct user_id)"),
    ("metric_revenue", "dashboard_sales", "chart"),
    ("metric_aov", "dashboard_sales", "chart"),
]
conn.executemany("INSERT INTO lineage VALUES (?, ?, ?)", LINEAGE)

# ---- 指标注册表 ----
METRICS = [
    ("metric_revenue", "SUM(fact_sales.amount)，含已支付订单", "数据组",
     "fact_sales", "每日 02:00"),
    ("metric_aov", "SUM(amount)/COUNT(DISTINCT order_id)，已支付", "数据组",
     "fact_sales", "每日 02:00"),
    ("metric_new_users", "当日首次下单用户数", "增长组",
     "dim_user, fact_sales", "每日 02:00"),
]
conn.executemany("INSERT INTO metric_registry VALUES (?, ?, ?, ?, ?)", METRICS)
conn.commit()

print("== 血缘边 ==")
for r in conn.execute("SELECT * FROM lineage ORDER BY upstream"):
    print(f"  {r['upstream']:14s} → {r['downstream']:16s}（{r['relation']}）")

print("\n== 指标注册表 ==")
for r in conn.execute("SELECT * FROM metric_registry"):
    print(f"  {r['metric']}")
    print(f"    定义：{r['definition']}")
    print(f"    负责人：{r['owner']} | 来源：{r['source_tables']} | 刷新：{r['refresh']}")


# ---- 下游影响分析（递归 CTE）----
def downstream_of(conn, source):
    rows = conn.execute("""
        WITH RECURSIVE downstream(node, depth, path) AS (
            SELECT downstream, 1, upstream || ' → ' || downstream
            FROM lineage WHERE upstream = ?
            UNION
            SELECT l.downstream, d.depth + 1, d.path || ' → ' || l.downstream
            FROM lineage l JOIN downstream d ON l.upstream = d.node
            WHERE d.depth < 10
        )
        SELECT DISTINCT node, MIN(depth) AS depth, MIN(path) AS path
        FROM downstream GROUP BY node ORDER BY depth, node
    """, (source,)).fetchall()
    return rows


print("\n== 影响分析：raw_orders 变更会影响谁 ==")
for r in downstream_of(conn, "raw_orders"):
    print(f"  {'  ' * (r['depth'] - 1)}└─ {r['node']}（{r['depth']} 层）")
    if r["depth"] == 1:
        print(f"      路径：{r['path']}")

print("\n== 影响分析：stg_orders ==")
for r in downstream_of(conn, "stg_orders"):
    print(f"  {r['node']}（{r['depth']} 层）")

# ---- 上游溯源 ----
def upstream_of(conn, target):
    rows = conn.execute("""
        WITH RECURSIVE upstream(node, depth) AS (
            SELECT upstream, 1 FROM lineage WHERE downstream = ?
            UNION
            SELECT l.upstream, u.depth + 1
            FROM lineage l JOIN upstream u ON l.downstream = u.node
            WHERE u.depth < 10
        )
        SELECT DISTINCT node, MIN(depth) AS depth FROM upstream GROUP BY node ORDER BY depth
    """, (target,)).fetchall()
    return rows


print("\n== 溯源：metric_aov 依赖哪些表 ==")
for r in upstream_of(conn, "metric_aov"):
    print(f"  {'  ' * (r['depth'] - 1)}└─ {r['node']}")

# ---- 口径冲突检测 ----
print("\n== 口径检查 ==")
conflicts = conn.execute("""
    SELECT metric, definition, owner FROM metric_registry
    WHERE metric IN ('metric_revenue', 'metric_aov')
""").fetchall()
for r in conflicts:
    print(f"  {r['metric']}: {r['definition']}（{r['owner']}）")
print("  如果两个部门各写一份 SQL，口径就可能漂移 → 统一到注册表/语义层")

# ---- 治理清单 ----
print("\n== 数据治理清单 ==")
for item in [
    "每个指标有唯一名字、明确公式、负责人、刷新频率",
    "血缘自动采集（解析 SQL/ETL 代码）而不是手工维护",
    "源表变更前跑影响分析，通知下游",
    "关键指标做一致性对账（新旧口径并行跑一段时间）",
    "废弃指标要标记 deprecated，而不是直接删除",
]:
    print("  -", item)

conn.close()

# ===== 练习题 =====
# 1. 增加一条 lineage：dim_user → metric_user_city，并重跑影响分析。
# 2. 给 metric_registry 增加“口径版本”字段，支持新旧口径并存。
# 3. 写函数 find_orphan_metrics()：没有任何上游血缘的指标。
# 4. 思考：为什么“手工维护血缘”通常不可靠？
