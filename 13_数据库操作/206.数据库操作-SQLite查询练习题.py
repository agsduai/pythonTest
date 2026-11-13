# ===== 第206课：数据库操作-SQLite查询 =====
# 知识点：
#   - SELECT 列 FROM 表 WHERE 条件 ORDER BY 列 [DESC] LIMIT n
#   - fetchone() 取一条 / fetchall() 取全部 / fetchmany(n) 取 n 条
#   - sqlite3.Row：让结果既能按下标又能按列名访问
#   - 聚合与分组：COUNT / SUM / AVG + GROUP BY
#   - 模糊查询：LIKE '%关键字%'

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row          # 行对象支持按列名取值
cursor = conn.cursor()
cursor.execute(
    "CREATE TABLE movie (id INTEGER PRIMARY KEY, title TEXT, year INT, score REAL)"
)
cursor.executemany(
    "INSERT INTO movie (title, year, score) VALUES (?, ?, ?)",
    [
        ("流浪地球", 2019, 7.9), ("哪吒", 2019, 8.4), ("你好李焕英", 2021, 7.7),
        ("长津湖", 2021, 7.6), ("满江红", 2023, 7.0), ("奥本海默", 2023, 8.8),
    ],
)
conn.commit()

# 按列名访问查询结果
row = cursor.execute("SELECT * FROM movie WHERE title = '哪吒'").fetchone()
print(row["title"], row["year"], row["score"])

# 条件 + 排序 + 截取
rows = cursor.execute(
    "SELECT title, score FROM movie WHERE score >= 7.7 ORDER BY score DESC LIMIT 3"
).fetchall()
for r in rows:
    print(r["title"], r["score"])

# 模糊查询
rows = cursor.execute("SELECT title FROM movie WHERE title LIKE '%球%'").fetchall()
print("模糊查询：", [r["title"] for r in rows])

# 聚合 + 分组
rows = cursor.execute(
    "SELECT year, COUNT(*) AS cnt, AVG(score) AS avg_score "
    "FROM movie GROUP BY year ORDER BY year"
).fetchall()
for r in rows:
    print(f"{r['year']} 年：{r['cnt']} 部，平均分 {r['avg_score']:.1f}")

conn.close()

# ===== 练习题 =====
# 1. 查询 2021 年的电影，按分数从高到低输出。
# 2. 统计平均分超过 7.7 的年份（提示：GROUP BY + HAVING）。
# 3. 用 fetchmany(2) 分三批取出全部 6 条记录。
# 4. 思考：fetchall 和“直接遍历 cursor”分别适合什么场景？
