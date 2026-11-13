# ===== 第306课：SQL进阶-数据导入导出 =====
# 知识点：
#   - CSV → SQLite：DictReader + executemany 批量入库（第284课 + 第13章）
#   - SQLite → CSV：游标迭代 + DictWriter 写出
#   - 事务批提交：每 N 条 commit 一次（复习第208课）
#   - 这套“进出库”是数据分析/报表任务的固定起手式

import csv
import os
import sqlite3

# ---- 1. 准备源 CSV ----
with open("students_306.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["姓名", "班级", "分数"])
    for i in range(1, 21):
        writer.writerow([f"学生{i}", f"{(i - 1) % 3 + 1}班", 60 + (i * 7) % 40])

# ---- 2. CSV 导入 SQLite ----
conn = sqlite3.connect("school_306.db")
conn.execute("CREATE TABLE IF NOT EXISTS student (name TEXT, class TEXT, score INT)")

with open("students_306.csv", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    batch = []
    for i, row in enumerate(reader, 1):
        batch.append((row["姓名"], row["班级"], int(row["分数"])))
        if i % 10 == 0:                     # 每 10 条提交一次
            conn.executemany(
                "INSERT INTO student VALUES (?, ?, ?)", batch)
            conn.commit()
            batch = []
    if batch:                               # 收尾
        conn.executemany("INSERT INTO student VALUES (?, ?, ?)", batch)
        conn.commit()

total = conn.execute("SELECT COUNT(*) FROM student").fetchone()[0]
print(f"入库完成，共 {total} 条")

# ---- 3. SQL 分析：每班人数与平均分 ----
rows = conn.execute("""
    SELECT class AS 班级, COUNT(*) AS 人数, ROUND(AVG(score), 1) AS 平均分
    FROM student GROUP BY class ORDER BY 班级
""").fetchall()
for r in rows:
    print(" ", tuple(r))

# ---- 4. 查询结果导出 CSV ----
with open("summary_306.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["班级", "人数", "平均分"])
    writer.writerows(rows)
print(open("summary_306.csv", encoding="utf-8-sig").read())

conn.close()
os.remove("students_306.csv")
os.remove("summary_306.csv")
os.remove("school_306.db")

# ===== 练习题 =====
# 1. 导入时增加“脏数据防御”：分数不是数字的行跳过并计数。
# 2. 用第191课的生成器思路，把“读 CSV→入库”改成流式处理超大文件。
# 3. 思考：为什么每 10 条 commit 一次比每条 commit 快？比最后一次性 commit 稳在哪？
