# ===== 第146课：数据分析-Pandas基础-数据排序 =====
# 课程来源：B站 BV1sHU9BmEne
# 依赖：pip install pandas
# 知识点：
#   - sort_values(by=...)：按一列或多列的值排序
#   - ascending：True 升序（默认）、False 降序，多列时可传列表
#   - na_position="last"/"first"：缺失值排在末尾或开头
#   - inplace=True：原地排序；否则返回新的 DataFrame
#   - sort_index()：按行索引排序；head() 取排序后的前几行

import pandas as pd

df = pd.DataFrame({
    "姓名": ["张三", "李四", "王五", "赵六", "钱七"],
    "部门": ["研发", "市场", "研发", "财务", "市场"],
    "工资": [12000, 9000, 15000, 10000, 9000],
    "奖金": [2000, None, 3000, 1500, None],
})

print("原始数据：")
print(df)

print("\n按工资升序：")
print(df.sort_values("工资"))

print("\n按工资降序：")
print(df.sort_values("工资", ascending=False))

print("\n先按部门升序，再按工资降序：")
print(df.sort_values(["部门", "工资"], ascending=[True, False]))

print("\n缺失值排在最后：")
print(df.sort_values("奖金", na_position="last"))

print("\n工资最高的前 2 人：")
print(df.sort_values("工资", ascending=False).head(2))

# inplace=True：直接修改原 DataFrame，不返回新对象
df.sort_values("工资", ascending=False, inplace=True)
print("\n原地排序后的索引顺序：")
print(df.index.tolist())
print(df)

# sort_index()：恢复为按索引排序
print("\n按索引排序：")
print(df.sort_index())

# ===== 练习题 =====
# 1. 按“工资”降序排列员工表，打印工资最高的前 3 行。
# 2. 先按“部门”升序、再按“工资”降序排序，观察多列排序的效果。
# 3. 按“奖金”降序排序并让缺失值排在最后，再按索引恢复原顺序。
