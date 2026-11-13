# ===== 第143课：数据分析-Pandas基础-数据查询与选择 =====
# 课程来源：B站 BV1sHU9BmEne
# 依赖：pip install pandas
# 知识点：
#   - 选列：df["列名"] 得到 Series，df[["列1", "列2"]] 得到 DataFrame
#   - loc：按“行/列标签”选择，切片包含终点
#   - iloc：按“行/列位置”选择，切片不包含终点
#   - at / iat：快速读取单个值（标签 / 位置）
#   - 行标签取决于索引，默认是 0、1、2……

import pandas as pd

# 使用自定义行索引，便于演示 loc
df = pd.DataFrame({
    "姓名": ["张三", "李四", "王五", "赵六"],
    "城市": ["北京", "上海", "广州", "深圳"],
    "成绩": [88, 92, 79, 95],
}, index=["s01", "s02", "s03", "s04"])

print(df)

print("\n选择一列（Series）：")
print(df["成绩"])

print("\n选择多列（DataFrame）：")
print(df[["姓名", "成绩"]])

print("\nloc 按标签取一行：")
print(df.loc["s02"])

print("\nloc 按标签取单值：", df.loc["s02", "成绩"])

print("\nloc 标签切片（包含 s03）：")
print(df.loc["s01":"s03", ["姓名", "成绩"]])

print("\niloc 按位置取第一行：")
print(df.iloc[0])

print("\niloc 取第一行第三列：", df.iloc[0, 2])

print("\niloc 位置切片（不含第 3 行）：")
print(df.iloc[1:3, 0:2])

print("\nat 快速取单值：", df.at["s04", "城市"])
print("iat 快速取单值：", df.iat[3, 1])

# ===== 练习题 =====
# 1. 构造带学号索引的学生表，分别用 df["姓名"] 和 df[["姓名", "成绩"]] 取列。
# 2. 用 loc 取出学号为 s02 的整行，以及 s01 到 s03 的“姓名”和“成绩”两列。
# 3. 用 iloc 取出第 2 行、第 2 到第 3 行，以及第 4 行第 2 列的值，并与 loc 的结果对比。
