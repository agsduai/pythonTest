# ===== 第142课：数据分析-Pandas基础-数据读取与写入 =====
# 课程来源：B站 BV1sHU9BmEne
# 依赖：pip install pandas openpyxl（Excel 读写部分需要 openpyxl）
# 知识点：
#   - 读取 CSV：pd.read_csv()，常用参数 sep、encoding、dtype、usecols、nrows
#   - 写入 CSV：df.to_csv()，常用参数 index=False、encoding="utf-8-sig"
#   - 读取 Excel：pd.read_excel()；写入 Excel：df.to_excel()（需要 openpyxl）
#   - 中文 CSV 用 utf-8-sig 编码，可避免 Excel 打开时乱码
#   - 文件路径可以是相对路径，也可以是绝对路径

import pandas as pd

# 先用内联数据构造 DataFrame，避免依赖外部数据文件
df = pd.DataFrame({
    "学号": ["001", "002", "003"],
    "姓名": ["张三", "李四", "王五"],
    "成绩": [88, 92, 79],
})

# 写入 CSV：index=False 表示不把行索引写进文件
# 生成的文件共 4 行：第 1 行是表头“学号,姓名,成绩”，后 3 行是数据
df.to_csv("students.csv", index=False, encoding="utf-8-sig")
print("已写入 students.csv")

# 读取 CSV：dtype={"学号": str} 防止“001”被解析成数字 1
df2 = pd.read_csv("students.csv", dtype={"学号": str}, encoding="utf-8-sig")
print(df2)
print(df2.dtypes)

# 只读取需要的列和前 2 行
part = pd.read_csv(
    "students.csv",
    usecols=["姓名", "成绩"],
    nrows=2,
    encoding="utf-8-sig",
)
print("\n只读取姓名和成绩两列的前 2 行：")
print(part)

# 写入与读取 Excel（需要 openpyxl，取消下面两行注释即可测试）
# df.to_excel("students.xlsx", index=False, sheet_name="成绩表")
# excel_df = pd.read_excel("students.xlsx", sheet_name="成绩表")

# ===== 练习题 =====
# 1. 把示例 DataFrame 写入 scores.csv（不保存索引），再用 read_csv 读回并打印。
# 2. 读取 students.csv 时只保留“姓名”“成绩”两列，并且只读前 2 行。
# 3. 安装 openpyxl 后，把数据写入 Excel 的“成绩表”工作表，再读取该工作表。
