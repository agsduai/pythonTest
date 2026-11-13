# ===== 第329课：Pandas进阶-与Excel和SQL互转 =====
# 知识点：
#   - read_excel / to_excel：DataFrame ↔ .xlsx（底层就是第23章的 openpyxl）
#   - to_sql / read_sql：DataFrame ↔ 数据库（底层 sqlite3，第13/25章）
#   - 三种载体一句话：Excel 给人看，SQL 给系统存，DataFrame 给分析用
# 依赖：pip install pandas openpyxl（数据库用内置 sqlite3）

import os
import sqlite3

import pandas as pd

df = pd.DataFrame({
    "姓名": ["小明", "小红", "小刚", "小丽"],
    "班级": ["一班", "一班", "二班", "二班"],
    "分数": [92, 85, 76, 88],
})

# ---- DataFrame → Excel → DataFrame ----
df.to_excel("pandas_329.xlsx", index=False, sheet_name="成绩")
back = pd.read_excel("pandas_329.xlsx")
print("从 Excel 读回：", back.to_dict("records"), sep="\n")

# 多 sheet 写入与读取
with pd.ExcelWriter("pandas_329.xlsx") as writer:
    df.to_excel(writer, sheet_name="成绩", index=False)
    df.groupby("班级", as_index=False)["分数"].mean().to_excel(writer, sheet_name="汇总", index=False)
print("sheet 列表：", list(pd.read_excel("pandas_329.xlsx", sheet_name=None)))   # read_excel 读完自动关闭句柄
print("汇总 sheet：", pd.read_excel("pandas_329.xlsx", sheet_name="汇总").to_dict("records"), sep="\n")

# ---- DataFrame → SQLite → DataFrame ----
conn = sqlite3.connect(":memory:")
df.to_sql("student", conn, index=False, if_exists="replace")     # 建表+入库一步完成
print("SQL 查询：", pd.read_sql(
    "SELECT 班级, COUNT(*) AS 人数, AVG(分数) AS 均分 FROM student GROUP BY 班级", conn
).round(1).to_dict("records"), sep="\n")

# pandas 反过来执行“聚合”再写回
top = pd.read_sql("SELECT * FROM student WHERE 分数 >= 85", conn)
top.to_sql("top_student", conn, index=False, if_exists="replace")
print("优秀学生表已入库：", pd.read_sql("SELECT * FROM top_student", conn).shape)

conn.close()
os.remove("pandas_329.xlsx")

# ===== 练习题 =====
# 1. 把第306课的 school.db 用 pandas 读出来做透视表。
# 2. 思考：大数据量时 read_sql 全表拉回内存合适吗？（提示：分块 chunksize）
# 3. 思考：哪类分析“在 SQL 里做”比“拉回 pandas 做”更高效？
