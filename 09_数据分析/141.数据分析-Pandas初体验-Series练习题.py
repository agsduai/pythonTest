# ===== 第141课：数据分析-Pandas初体验-Series =====
# 课程来源：B站 BV1sHU9BmEne
# 依赖：pip install pandas
# 知识点：
#   - Series 是带索引的一维数组，可看作 DataFrame 的一列
#   - 构造：列表、字典、标量；可用 index 指定索引、name 指定名称
#   - 常用属性：values、index、dtype、name、shape
#   - 取值与切片：s["标签"]、s.iloc[位置]、s.loc["标签"]
#   - 向量化运算、缺失值检测 isna()、计数 value_counts()

import pandas as pd

# 用列表构造，并指定索引和名称
scores = pd.Series(
    [88, 92, 79, 95],
    index=["张三", "李四", "王五", "赵六"],
    name="成绩",
)

print(scores)
print("values：", scores.values)            # 底层数据
print("index：", scores.index.tolist())     # 索引标签
print("dtype：", scores.dtype)              # 数据类型
print("name：", scores.name)                # Series 名称
print("shape：", scores.shape)              # (4,)

print("\n平均分：", scores.mean())
print("最高分：", scores.max())
print("最低分：", scores.min())

print("\n按标签取值：", scores["张三"])
print("按位置取值：", scores.iloc[0])
print("前两名：")
print(scores.iloc[:2])

print("\n每人加 5 分：")
print(scores + 5)

print("\n是否及格：")
print(scores >= 60)

# 用字典构造：字典的键会自动成为索引
cities = pd.Series({"北京": 2154, "上海": 2487, "广州": 1881}, name="人口")
print("\n城市人口：")
print(cities)

print("\n出现次数统计：")
print(pd.Series(["北京", "上海", "北京", "广州"]).value_counts())

# ===== 练习题 =====
# 1. 用列表构造一个 4 名学生的成绩 Series，索引为姓名，名称为“期末成绩”。
# 2. 打印 values、index、dtype，并计算平均分、最高分。
# 3. 用字典构造“城市-人口”Series，取出“上海”的值，并统计各城市出现的次数。
