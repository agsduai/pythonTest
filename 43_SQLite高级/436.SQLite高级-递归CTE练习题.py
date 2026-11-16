# ===== 第436课：SQLite高级-递归CTE =====
# 知识点：
#   - 递归 CTE：WITH RECURSIVE 名字 AS (初始查询 UNION ALL 递归查询)
#   - 适合“层级/树/图”的遍历：组织架构、分类目录、BOM 物料清单
#   - 递归部分引用自身；必须有终止条件（否则无限递归）
#   - 可以携带 depth、path 等派生列，方便展示与防环
#   - 与第254课二叉树遍历、第333课 DFS 的思想一致，只是用 SQL 表达
# 依赖：无（sqlite3 内置）

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE employee (
    id INTEGER PRIMARY KEY,
    name TEXT,
    manager_id INTEGER REFERENCES employee(id),
    salary REAL
);
""")
conn.executemany(
    "INSERT INTO employee (id, name, manager_id, salary) VALUES (?, ?, ?, ?)",
    [
        (1, "张总", None, 30000),
        (2, "李经理", 1, 20000),
        (3, "王经理", 1, 18000),
        (4, "小明", 2, 10000),
        (5, "小红", 2, 12000),
        (6, "小刚", 3, 11000),
    ],
)
conn.commit()

print("== 组织架构树（递归 CTE）==")
rows = conn.execute("""
    WITH RECURSIVE org(id, name, manager_id, depth, path) AS (
        SELECT id, name, manager_id, 0, name
        FROM employee
        WHERE manager_id IS NULL
        UNION ALL
        SELECT e.id, e.name, e.manager_id, org.depth + 1, org.path || ' > ' || e.name
        FROM employee e
        JOIN org ON e.manager_id = org.id
    )
    SELECT id, name, depth, path FROM org ORDER BY path
""").fetchall()

for r in rows:
    print(f"  {'  ' * r['depth']}{r['name']}（深度 {r['depth']}）")
    if r["depth"] == 2:
        print(f"      路径：{r['path']}")

print("\n== 某个经理的整个子树 ==")
rows = conn.execute("""
    WITH RECURSIVE subtree(id, name, salary) AS (
        SELECT id, name, salary FROM employee WHERE id = 2
        UNION ALL
        SELECT e.id, e.name, e.salary
        FROM employee e JOIN subtree s ON e.manager_id = s.id
    )
    SELECT name, salary FROM subtree
""").fetchall()
total = sum(r["salary"] for r in rows)
print("  李经理团队：", [(r["name"], r["salary"]) for r in rows])
print("  团队总薪资：", total)

print("\n== 每人的下属数量（含间接下属）==")
rows = conn.execute("""
    WITH RECURSIVE chain(boss_id, sub_id) AS (
        SELECT manager_id, id FROM employee WHERE manager_id IS NOT NULL
        UNION ALL
        SELECT c.boss_id, e.id
        FROM chain c JOIN employee e ON e.manager_id = c.sub_id
    )
    SELECT e.name, COUNT(c.sub_id) AS reports
    FROM employee e LEFT JOIN chain c ON c.boss_id = e.id
    GROUP BY e.id ORDER BY reports DESC
""").fetchall()
for r in rows:
    print(f"  {r['name']}: {r['reports']} 人")

print("\n== 递归 CTE 也能生成序列 ==")
rows = conn.execute("""
    WITH RECURSIVE nums(n, sq) AS (
        SELECT 1, 1
        UNION ALL
        SELECT n + 1, (n + 1) * (n + 1) FROM nums WHERE n < 8
    )
    SELECT n, sq FROM nums
""").fetchall()
print("  1~8 的平方：", [(r["n"], r["sq"]) for r in rows])

print("\n== BOM 物料清单展开 ==")
parts = [
    ("自行车", "车架", 1), ("自行车", "车轮", 2),
    ("车轮", "轮胎", 1), ("车轮", "辐条", 32),
    ("车架", "钢管", 3),
]
conn.execute("CREATE TABLE bom (parent TEXT, child TEXT, qty INTEGER)")
conn.executemany("INSERT INTO bom VALUES (?, ?, ?)", parts)
conn.commit()

rows = conn.execute("""
    WITH RECURSIVE explode(item, level, total_qty) AS (
        SELECT child, 1, qty FROM bom WHERE parent = '自行车'
        UNION ALL
        SELECT b.child, e.level + 1, e.total_qty * b.qty
        FROM bom b JOIN explode e ON b.parent = e.item
    )
    SELECT item, level, SUM(total_qty) AS qty FROM explode
    GROUP BY item, level ORDER BY level, item
""").fetchall()
for r in rows:
    print(f"  第{r['level']}层 {r['item']}: {r['qty']}")

conn.close()

# 防坑：
#   1) 递归必须有终止条件（WHERE / JOIN 自然结束）
#   2) 图里有环会无限递归 —— 加 WHERE id NOT IN (已访问) 或 UNION 去重
#   3) 深度很大时注意 SQLite 的递归深度限制

# ===== 练习题 =====
# 1. 给组织树增加“是否叶子节点”标记。
# 2. 求每个节点的“自底向上薪资汇总”（叶子向根累加）。
# 3. 用递归 CTE 生成 2026 年 1~12 月的月份列表。
# 4. 思考：递归 CTE 与在 Python 里写 DFS 相比，各适合什么场景？
