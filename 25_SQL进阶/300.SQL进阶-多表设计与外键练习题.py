# ===== 第300课：SQL进阶-多表设计与外键 =====
# 知识点：
#   - 为什么拆多张表：消除重复、各自维护、按需关联（复习第203课）
#   - FOREIGN KEY 外键：保证“从表的引用一定存在”
#   - SQLite 默认不校验外键！必须每连接执行 PRAGMA foreign_keys = ON
#   - 一对多：一个班级 ↔ 多个学生

import sqlite3

conn = sqlite3.connect(":memory:")
conn.execute("PRAGMA foreign_keys = ON")       # 打开外键校验
conn.executescript("""
CREATE TABLE class (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE student (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    class_id INTEGER REFERENCES class(id)
);
""")

conn.execute("INSERT INTO class (name) VALUES ('一班')")
conn.execute("INSERT INTO class (name) VALUES ('二班')")
conn.executemany(
    "INSERT INTO student (name, class_id) VALUES (?, ?)",
    [("小明", 1), ("小红", 1), ("小刚", 2)],
)
conn.commit()

# 正常插入：引用存在的班级
conn.execute("INSERT INTO student (name, class_id) VALUES ('小丽', 2)")

# 外键校验：引用不存在的班级 → 直接拒绝
try:
    conn.execute("INSERT INTO student (name, class_id) VALUES ('小黑', 99)")
except sqlite3.IntegrityError as exc:
    print("外键拦截：", exc)

# 忘记开 PRAGMA 的后果（新连接默认关闭校验）
conn2 = sqlite3.connect(":memory:")
conn2.executescript("CREATE TABLE t (x INTEGER REFERENCES class(id));")
conn2.execute("CREATE TABLE class (id INTEGER PRIMARY KEY)")
conn2.execute("INSERT INTO t VALUES (999)")     # 没报错！因为没开校验
print("不开 PRAGMA 时，脏数据悄悄进来了：", conn2.execute("SELECT * FROM t").fetchall())

conn.close()
conn2.close()

# ===== 练习题 =====
# 1. 给 student 加 score 表（student_id, subject, value），外键指向 student。
# 2. 验证：向 score 插入不存在的学生 id 会被拦截。
# 3. 思考：什么时候“不拆表”反而更好？（提示：数据量小、永远一对一）
