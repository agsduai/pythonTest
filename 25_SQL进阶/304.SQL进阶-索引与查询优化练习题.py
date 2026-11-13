# ===== 第304课：SQL进阶-索引与查询优化 =====
# 知识点：
#   - 没索引 → 全表扫描 SCAN；有索引 → 定点查找 SEARCH（哈希/B树思想，第253课）
#   - EXPLAIN QUERY PLAN：看 SQL 的“执行计划”
#   - 索引的代价：占磁盘、拖慢写入 —— 只给常查的列建
#   - 建索引一行：CREATE INDEX idx_表_列 ON 表(列)

import sqlite3
import time

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE log (id INTEGER PRIMARY KEY, user_id INTEGER, msg TEXT)")

# 造 5 万条日志
conn.executemany(
    "INSERT INTO log (user_id, msg) VALUES (?, ?)",
    [(i % 500, f"日志{i}") for i in range(50_000)],
)
conn.commit()

# ---- 建索引前：全表扫描 ----
plan = conn.execute(
    "EXPLAIN QUERY PLAN SELECT * FROM log WHERE user_id = 42"
).fetchall()
print("建索引前的执行计划：", plan)

start = time.perf_counter()
for _ in range(50):
    conn.execute("SELECT * FROM log WHERE user_id = 42").fetchall()
t_no_index = time.perf_counter() - start
print(f"无索引查 50 次：{t_no_index:.4f} 秒")

# ---- 建索引 ----
conn.execute("CREATE INDEX idx_log_user ON log(user_id)")
plan = conn.execute(
    "EXPLAIN QUERY PLAN SELECT * FROM log WHERE user_id = 42"
).fetchall()
print("建索引后的执行计划：", plan)

start = time.perf_counter()
for _ in range(50):
    conn.execute("SELECT * FROM log WHERE user_id = 42").fetchall()
t_index = time.perf_counter() - start
print(f"有索引查 50 次：{t_index:.4f} 秒")

# ---- 索引的代价：写入变慢 ----
start = time.perf_counter()
for i in range(2000):
    conn.execute("INSERT INTO log (user_id, msg) VALUES (?, ?)", (1, "x"))
t_write = time.perf_counter() - start
print(f"有索引写 2000 条：{t_write:.4f} 秒（索引越高写越慢）")

conn.close()

# 经验法则：
#   WHERE / JOIN / ORDER BY 常用的列 → 建索引
#   唯一约束列（手机号、邮箱）→ 建唯一索引
#   几乎不查的表 → 不建

# ===== 练习题 =====
# 1. 给 msg 列建索引，再用 EXPLAIN 验证 LIKE '%日志%' 是否用得上。
#    （提示：前置 % 通常用不上索引，体会“最左匹配”）
# 2. 把 50 次查询改成 500 次，放大差距。
# 3. 思考：为什么 PRIMARY KEY 天然就是索引？
