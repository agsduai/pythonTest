# ===== 第301课：SQL进阶-JOIN连接查询 =====
# 知识点：
#   - INNER JOIN：只保留两边都匹配的行
#   - LEFT JOIN：左表全保留，右表匹配不上的补 NULL
#   - JOIN ... ON 指定关联条件；别名让 SQL 更短
#   - 场景：学生表 + 班级表，把编号翻译成班级名

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE class (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE student (id INTEGER PRIMARY KEY, name TEXT, class_id INTEGER);
""")
conn.execute("INSERT INTO class VALUES (1, '一班'), (2, '二班'), (3, '三班')")
conn.executemany(
    "INSERT INTO student (name, class_id) VALUES (?, ?)",
    [("小明", 1), ("小红", 1), ("小刚", 2), ("小丽", 2), ("小黑", 99)],
)
conn.commit()

# ---- INNER JOIN：两边都匹配才出现 ----
print("== INNER JOIN ==")
rows = conn.execute("""
    SELECT student.name AS 学生, class.name AS 班级
    FROM student INNER JOIN class ON student.class_id = class.id
""").fetchall()
for r in rows:
    print(" ", dict(r))
print("（小黑的 class_id=99 匹配不到班级，被过滤掉了）")

# ---- LEFT JOIN：左表全保留 ----
print("== LEFT JOIN ==")
rows = conn.execute("""
    SELECT student.name AS 学生, class.name AS 班级
    FROM student LEFT JOIN class ON student.class_id = class.id
""").fetchall()
for r in rows:
    print(" ", dict(r))

# ---- 反向查：每个班有哪些学生（左表=班级）----
print("== 班级 → 学生（三班没人也显示）==")
rows = conn.execute("""
    SELECT class.name AS 班级, student.name AS 学生
    FROM class LEFT JOIN student ON class.id = student.class_id
""").fetchall()
for r in rows:
    print(" ", dict(r))

# ---- JOIN + WHERE + ORDER BY 组合 ----
print("== 一班的学生，按名字排 ==")
rows = conn.execute("""
    SELECT student.name AS 学生
    FROM student JOIN class ON student.class_id = class.id
    WHERE class.name = '一班'
    ORDER BY student.name
""").fetchall()
print(" ", [r["学生"] for r in rows])

conn.close()

# ===== 练习题 =====
# 1. 查“没有学生的班级”（提示：LEFT JOIN + IS NULL）。
# 2. 三表 JOIN：学生 → 班级 → 任课老师（自建 teacher 表）。
# 3. 思考：INNER JOIN 和“WHERE 两表 id 相等”的写法结果一样吗？哪种更清晰？
