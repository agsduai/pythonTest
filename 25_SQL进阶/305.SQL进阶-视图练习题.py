# ===== 第305课：SQL进阶-视图 =====
# 知识点：
#   - 视图 VIEW：把一条常用查询“存成虚拟表”，随用随取
#   - 视图不存数据：每次查询视图 = 实时执行它的 SELECT
#   - 收益：复杂口径写一次、到处复用；报表口径统一不跑偏
#   - 修改/删除：CREATE OR REPLACE / DROP VIEW

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE class (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE student (id INTEGER PRIMARY KEY, name TEXT, class_id INTEGER);
CREATE TABLE score (student_id INTEGER, subject TEXT, value REAL);
""")
conn.execute("INSERT INTO class VALUES (1, '一班'), (2, '二班')")
conn.executemany("INSERT INTO student (name, class_id) VALUES (?, ?)",
                 [("小明", 1), ("小红", 1), ("小刚", 2)])
conn.executemany(
    "INSERT INTO score VALUES (?, ?, ?)",
    [(1, "语文", 92), (1, "数学", 88), (2, "语文", 75),
     (2, "数学", 95), (3, "语文", 60), (3, "数学", 65)],
)
conn.commit()

# ---- 把“班级平均分”这个常用口径固化成视图 ----
conn.execute("""
    CREATE VIEW class_avg AS
    SELECT class.name AS 班级,
           COUNT(student.id) AS 人数,
           ROUND(AVG(score.value), 1) AS 平均分
    FROM class
    LEFT JOIN student ON student.class_id = class.id
    LEFT JOIN score ON score.student_id = student.id
    GROUP BY class.id
""")
conn.commit()

# 用视图像用表一样简单
for r in conn.execute("SELECT * FROM class_avg"):
    print(dict(r))

# 视图上还能继续 WHERE / ORDER BY
rows = conn.execute(
    "SELECT 班级 FROM class_avg WHERE 平均分 >= 80 ORDER BY 平均分 DESC"
).fetchall()
print("达标班级：", [r["班级"] for r in rows])

# 视图是实时的：插入新成绩后，视图立刻反映
conn.execute("INSERT INTO score VALUES (3, '英语', 100)")
conn.commit()
print("插入了 100 分后：", [tuple(r) for r in conn.execute("SELECT * FROM class_avg")])

# 删除视图
conn.execute("DROP VIEW class_avg")
print("删除后再查会报错吗？", end=" ")
try:
    conn.execute("SELECT * FROM class_avg")
except sqlite3.OperationalError as exc:
    print("是 ——", exc)

conn.close()

# ===== 练习题 =====
# 1. 建一个“学生平均分榜”视图，包含姓名与平均分，按分排序查询。
# 2. 思考：视图和“把查询结果存进一张真实表”各有什么优缺点？
# 3. 进阶：SQLite 也支持 EXPLAIN VIEW 吗？查查文档，比较与 MySQL 的差异。
