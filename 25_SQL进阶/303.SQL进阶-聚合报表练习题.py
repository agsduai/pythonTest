# ===== 第303课：SQL进阶-聚合报表 =====
# 知识点：
#   - GROUP BY 分组 + 聚合函数：COUNT / SUM / AVG / MAX / MIN
#   - HAVING：对“分组之后的结果”过滤（WHERE 过滤的是原始行）
#   - CASE WHEN：在 SQL 里做 if/else，常用于“分数段”“标签”
#   - 这一条 SQL 就能产出一张报表（对照第206课的基础聚合）

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE class (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE score (student_id INTEGER, subject TEXT, value REAL);
""")
conn.execute("INSERT INTO class VALUES (1, '一班'), (2, '二班')")
conn.executemany(
    "INSERT INTO score VALUES (?, ?, ?)",
    [
        (1, "语文", 92), (1, "数学", 88), (1, "英语", 95),
        (2, "语文", 55), (2, "数学", 70), (2, "英语", 61),
        (3, "语文", 80), (3, "数学", 85),
    ],   # 3 号学生属于一班
)
conn.commit()

# ---- 每班人数、平均分、最高分 ----
rows = conn.execute("""
    SELECT class.name AS 班级,
           COUNT(*) AS 条数,
           ROUND(AVG(score.value), 1) AS 平均分,
           MAX(score.value) AS 最高分
    FROM score JOIN class ON class.id = score.student_id
    GROUP BY class.id
""").fetchall()
for r in rows:
    print(dict(r))

# ---- HAVING：只看平均分 >= 80 的班级 ----
rows = conn.execute("""
    SELECT class.name AS 班级, ROUND(AVG(score.value), 1) AS 平均分
    FROM score JOIN class ON class.id = score.student_id
    GROUP BY class.id
    HAVING AVG(score.value) >= 80
""").fetchall()
print("平均分达标的班级：", [(r["班级"], r["平均分"]) for r in rows])

# ---- CASE WHEN：分数段统计 ----
rows = conn.execute("""
    SELECT CASE
               WHEN value >= 90 THEN '优秀'
               WHEN value >= 60 THEN '及格'
               ELSE '不及格'
           END AS 等级,
           COUNT(*) AS 科目数
    FROM score
    GROUP BY 等级
    ORDER BY 科目数 DESC
""").fetchall()
for r in rows:
    print(dict(r))

# ---- 每个学生：科目数 + 平均分（按学生分组）----
rows = conn.execute("""
    SELECT student_id, COUNT(*) AS 科目数,
           ROUND(AVG(value), 1) AS 平均分
    FROM score GROUP BY student_id ORDER BY 平均分 DESC
""").fetchall()
print("学生榜：", [(r["student_id"], r["平均分"]) for r in rows])

conn.close()

# ===== 练习题 =====
# 1. 统计每个科目的人数与平均分，按平均分降序。
# 2. CASE WHEN 换个玩法：把平均分映射成 A/B/C/D 等级。
# 3. 思考：WHERE 和 HAVING 的执行顺序谁先谁后？为什么？
