# ===== 第205课：数据库操作-SQLite增删改 =====
# 知识点：
#   - INSERT：单条插入与 executemany 批量插入
#   - UPDATE ... WHERE：不带 WHERE 会改全表！
#   - DELETE ... WHERE：不带 WHERE 会删光全表！
#   - commit() 提交后数据才真正写入
#   - rowcount：上一条语句影响的行数

import sqlite3

conn = sqlite3.connect(":memory:")
cursor = conn.cursor()
cursor.execute("CREATE TABLE student (id INTEGER PRIMARY KEY, name TEXT, score REAL)")

# 插入单条
cursor.execute("INSERT INTO student (name, score) VALUES ('小明', 92)")
print("插入影响行数：", cursor.rowcount)     # 1

# 批量插入：占位符 ? + 元组列表
students = [("小红", 88), ("小刚", 76), ("小丽", 95), ("小强", 63)]
cursor.executemany("INSERT INTO student (name, score) VALUES (?, ?)", students)
count = cursor.execute("SELECT COUNT(*) FROM student").fetchone()[0]
print("批量插入后共：", count)

# 更新：一定要带 WHERE
cursor.execute("UPDATE student SET score = 90 WHERE name = '小刚'")
print("更新影响行数：", cursor.rowcount)

# 删除：一定要带 WHERE
cursor.execute("DELETE FROM student WHERE score < 70")
print("删除影响行数：", cursor.rowcount)

conn.commit()     # 增删改统一提交

# 验证结果
for row in cursor.execute("SELECT * FROM student ORDER BY score DESC"):
    print(row)

conn.close()

# 危险演示（不要运行）：下面两条会把全表改掉/删光
# cursor.execute("UPDATE student SET score = 0")     # 漏了 WHERE
# cursor.execute("DELETE FROM student")              # 漏了 WHERE

# ===== 练习题 =====
# 1. 插入你自己的信息，再更新自己的成绩为 100。
# 2. 编写函数 update_score(name, new_score)，完成“查询确认 + 更新”两步。
# 3. 统计删除后剩余人数，验证 COUNT(*) 的用法。
# 4. 思考：为什么强烈建议 UPDATE/DELETE 必须带 WHERE？
