# ===== 第139课：数据分析-Pandas初体验 =====
# 课程来源：B站 BV1sHU9BmEne
# 依赖：pip install pandas
# 知识点：
#   - pandas 的两大核心数据结构：DataFrame（二维表）和 Series（一维列）
#   - 导入约定：import pandas as pd
#   - 快速查看数据：head()、tail()、shape、columns、index、dtypes
#   - 描述性统计：describe()；表结构信息：info()
#   - pandas 支持读取 csv、Excel、json 等多种数据源

import pandas as pd

# 用字典内联构造 DataFrame：键是列名，值是列数据
df = pd.DataFrame({
    "姓名": ["张三", "李四", "王五", "赵六", "钱七"],
    "年龄": [23, 25, 22, 28, 24],
    "城市": ["北京", "上海", "北京", "广州", "上海"],
    "成绩": [88, 92, 79, 95, 85],
})

print(df)                                   # 打印整张表
print("形状（行, 列）：", df.shape)          # (5, 4)
print("列名：", df.columns.tolist())
print("索引：", df.index.tolist())
print("每列的数据类型：")
print(df.dtypes)

print("\n前 3 行：")
print(df.head(3))                           # 默认取前 5 行

print("\n后 2 行：")
print(df.tail(2))                           # 取末尾 2 行

print("\n数值列描述性统计：")
print(df.describe())                        # 计数、均值、标准差、最值、四分位数

print("\n表结构信息：")
df.info()                                   # 行数、列名、非空数量、类型、内存

# 取出一列得到 Series，再做简单计算
scores = df["成绩"]
print("\n平均成绩：", scores.mean())
print("最高成绩：", scores.max())

# ===== 练习题 =====
# 1. 构造 4 名同学的数据（姓名、年龄、成绩），打印整张表和它的形状。
# 2. 使用 head(2)、tail(2) 和 describe() 查看数据的不同侧面。
# 3. 新增“是否及格”列（成绩 >= 60 为“是”，否则为“否”），并统计及格人数。
