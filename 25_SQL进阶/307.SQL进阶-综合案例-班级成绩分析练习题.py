# ===== 第307课：SQL进阶-综合案例-班级成绩分析 =====
# 知识点：
#   - 综合运用：外键建表（300）+ JOIN（301）+ 聚合/CASE（303）+ 视图（305）
#   - 一条流水线：建库 → 入数据 → SQL 出三张报表
#   - 体会：报表口径写进 SQL，Python 只负责组装与展示

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON")
conn.executescript("""
CREATE TABLE class (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE student (
    id INTEGER PRIMARY KEY,
    name TEXT,
    class_id INTEGER REFERENCES class(id)
);
CREATE TABLE score (
    student_id INTEGER REFERENCES student(id),
    subject TEXT,
    value REAL
);
""")

conn.executemany("INSERT INTO class (name) VALUES (?)", [("一班",), ("二班",)])
conn.executemany(
    "INSERT INTO student (name, class_id) VALUES (?, ?)",
    [("小明", 1), ("小红", 1), ("小刚", 2), ("小丽", 2)],
)
conn.executemany(
    "INSERT INTO score VALUES (?, ?, ?)",
    [
        (1, "语文", 92), (1, "数学", 88), (1, "英语", 95),
        (2, "语文", 75), (2, "数学", 95), (2, "英语", 85),
        (3, "语文", 58), (3, "数学", 70),
        (4, "语文", 88), (4, "数学", 92), (4, "英语", 90),
    ],
)
conn.commit()

# ---- 建视图：学生平均分榜 ----
conn.execute("""
    CREATE VIEW student_avg AS
    SELECT student.name AS 姓名, class.name AS 班级,
           COUNT(score.value) AS 科目数,
           ROUND(AVG(score.value), 1) AS 平均分
    FROM student
    JOIN class ON class.id = student.class_id
    LEFT JOIN score ON score.student_id = student.id
    GROUP BY student.id
""")

# ---- 报表1：班级总览 ----
print("== 各班人数与平均分 ==")
for r in conn.execute("""
    SELECT 班级, COUNT(*) AS 学生数, ROUND(AVG(平均分), 1) AS 班级均分
    FROM student_avg GROUP BY 班级
"""):
    print(" ", dict(r))

# ---- 报表2：学生榜 + 等级 ----
print("== 学生榜（含等级）==")
for r in conn.execute("""
    SELECT 姓名, 班级, 平均分,
           CASE WHEN 平均分 >= 90 THEN 'A'
                WHEN 平均分 >= 80 THEN 'B'
                WHEN 平均分 >= 60 THEN 'C'
                ELSE 'D' END AS 等级
    FROM student_avg WHERE 科目数 > 0
    ORDER BY 平均分 DESC
"""):
    print(" ", dict(r))

# ---- 报表3：偏科预警（单科与个人均分差 >= 20）----
print("== 偏科预警 ==")
for r in conn.execute("""
    WITH personal AS (SELECT student_id, AVG(value) AS avg_v FROM score GROUP BY student_id)
    SELECT student.name AS 姓名, score.subject AS 科目, score.value AS 分数,
           ROUND(personal.avg_v, 1) AS 个人均分
    FROM score
    JOIN personal ON personal.student_id = score.student_id
    JOIN student ON student.id = score.student_id
    WHERE ABS(score.value - personal.avg_v) >= 20
"""):
    print(" ", dict(r))

conn.close()

# ===== 练习题 =====
# 1. 增加“各科平均分”报表（GROUP BY subject）。
# 2. 把三张报表导出成一个 Excel 的三个 sheet（结合第290课）。
# 3. 思考：这三张报表里，哪些适合做成视图长期使用？
