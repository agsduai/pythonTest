# ===== 第140课：数据分析-Pandas初体验-DataFrame =====
# 课程来源：B站 BV1sHU9BmEne
# 依赖：pip install pandas
# 知识点：
#   - DataFrame 是带行索引和列名的二维表格
#   - 构造方式：字典、二维列表、字典列表
#   - 查看行索引 index、列名 columns、形状 shape
#   - 增加列、修改列、删除列（drop）、重命名列（rename）
#   - 列运算默认按列向量化执行

import pandas as pd

# 用“字典列表”构造：每个字典是一行
df = pd.DataFrame([
    {"姓名": "张三", "部门": "研发", "工资": 12000},
    {"姓名": "李四", "部门": "市场", "工资": 9000},
    {"姓名": "王五", "部门": "研发", "工资": 15000},
    {"姓名": "赵六", "部门": "财务", "工资": 10000},
], index=["e01", "e02", "e03", "e04"])      # 自定义行索引

print(df)
print("行索引：", df.index.tolist())
print("列名：", df.columns.tolist())

# 选择一列（Series）与多列（DataFrame）
print("\n姓名列：")
print(df["姓名"])
print("\n姓名和工资两列：")
print(df[["姓名", "工资"]])

# 新增列：按列进行向量化计算
df["年薪"] = df["工资"] * 12
# 修改列：每人涨薪 500
df["工资"] = df["工资"] + 500
# 删除列：columns 指定要删除的列
df = df.drop(columns=["年薪"])
# 重命名列
df = df.rename(columns={"工资": "月薪"})
print("\n处理后的表：")
print(df)

# 转置：行列互换
print("\n转置后的表：")
print(df.T)

# ===== 练习题 =====
# 1. 构造包含 4 名学生（学号索引、姓名、年龄、城市）的 DataFrame 并打印。
# 2. 为 DataFrame 新增“总分”列，删除“城市”列，再把“姓名”重命名为“学生姓名”。
# 3. 使用 df.T 查看转置结果，并用 df["年龄"].mean() 计算平均年龄。
