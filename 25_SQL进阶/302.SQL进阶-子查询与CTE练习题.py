# ===== 第302课：SQL进阶-子查询与CTE =====
# 知识点：
#   - 子查询：一条 SQL 里嵌另一条 SELECT
#   - WHERE ... IN (子查询)：按“集合成员”过滤
#   - 标量子查询：子查询只返回一个值，可以直接参与比较
#   - WITH ... AS（CTE 公用表表达式）：给中间结果命名，复杂查询分层写

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE student (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE score (student_id INTEGER, subject TEXT, value REAL);
""")
conn.executemany("INSERT INTO student (name) VALUES (?)", [("小明",), ("小红",), ("小刚",)])
conn.executemany(
    "INSERT INTO score VALUES (?, ?, ?)",
    [
        (1, "语文", 92), (1, "数学", 88),
        (2, "语文", 75), (2, "数学", 95),
        (3, "语文", 58), (3, "数学", 64),
    ],
)
conn.commit()

# ---- IN 子查询：谁有 90 分以上的科目 ----
rows = conn.execute("""
    SELECT name FROM student
    WHERE id IN (SELECT student_id FROM score WHERE value >= 90)
""").fetchall()
print("有90+科目的学生：", [r["name"] for r in rows])

# ---- NOT IN：谁没有任何 90+ 科目 ----
rows = conn.execute("""
    SELECT name FROM student
    WHERE id NOT IN (SELECT student_id FROM score WHERE value >= 90)
""").fetchall()
print("没有90+科目的学生：", [r["name"] for r in rows])

# ---- 标量子查询：和“全班平均分”比 ----
rows = conn.execute("""
    SELECT name, value FROM score
    JOIN student ON student.id = score.student_id
    WHERE value > (SELECT AVG(value) FROM score)
    ORDER BY value DESC
""").fetchall()
print("高于全班平均的科目：", [(r["name"], r["value"]) for r in rows])

# ---- CTE：分步思考复杂问题 ----
rows = conn.execute("""
    WITH student_avg AS (
        SELECT student_id, AVG(value) AS avg_value
        FROM score GROUP BY student_id
    )
    SELECT student.name, ROUND(student_avg.avg_value, 1) AS 平均分
    FROM student_avg
    JOIN student ON student.id = student_avg.student_id
    ORDER BY 平均分 DESC
""").fetchall()
print("各人平均分（CTE 版）：", [(r["name"], r["平均分"]) for r in rows])

conn.close()

# ===== 练习题 =====
# 1. 用标量子查询实现“比小刚平均分高的学生”。
# 2. 把 IN 子查询改写成 JOIN 写法，对比可读性。
# 3. CTE 支持链式：WITH a AS (...), b AS (SELECT * FROM a ...) —— 练一次。
# 4. 思考：子查询和 JOIN 什么场景下可以互换？各有什么代价？
