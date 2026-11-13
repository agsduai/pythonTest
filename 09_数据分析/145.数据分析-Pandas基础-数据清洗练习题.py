# ===== 第145课：数据分析-Pandas基础-数据清洗 =====
# 课程来源：B站 BV1sHU9BmEne
# 依赖：pip install pandas
# 知识点：
#   - 缺失值检测：isnull()/isna()、notnull()
#   - 缺失值统计：df.isnull().sum()
#   - 删除缺失值：dropna(how=...)、dropna(subset=[...])
#   - 填充缺失值：fillna()，可用固定值、均值、ffill 前向填充、bfill 后向填充
#   - 重复值处理：duplicated()、drop_duplicates(subset=[...])
#   - 其他清洗：replace() 替换值、astype() 转换类型

import pandas as pd

df = pd.DataFrame({
    "姓名": ["张三", "李四", "王五", "李四", None],
    "年龄": [23, None, 25, 23, 30],
    "城市": ["北京", "上海", None, "上海", "广州"],
    "成绩": [88, 92, 79, 92, 60],
})

print("原始数据：")
print(df)

print("\n缺失值分布（True 表示缺失）：")
print(df.isnull())

print("\n每列缺失值数量：")
print(df.isnull().sum())

print("\n删除任意含缺失值的行：")
print(df.dropna())

print("\n只检查“年龄”列，删除年龄缺失的行：")
print(df.dropna(subset=["年龄"]))

print("\n用均值填充年龄，用“未知”填充城市：")
print(df.fillna({"年龄": df["年龄"].mean(), "城市": "未知"}))

print("\n用前一行的值填充年龄（前向填充）：")
print(df["年龄"].ffill())

print("\n删除完全重复的行：")
print(df.drop_duplicates())

print("\n按“姓名”去重，保留第一次出现的行：")
print(df.drop_duplicates(subset=["姓名"], keep="first"))

print("\n把城市“北京”替换为“北京市”：")
print(df.replace({"城市": {"北京": "北京市"}}))

# ===== 练习题 =====
# 1. 统计每列缺失值数量，并删除“姓名”为空的行。
# 2. 用平均年龄填充年龄缺失值，用“未知”填充城市缺失值，打印清洗结果。
# 3. 按“姓名”去重并保留第一次出现的记录，再把成绩列转换为整数类型。
