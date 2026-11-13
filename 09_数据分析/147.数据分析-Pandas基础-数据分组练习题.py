# ===== 第147课：数据分析-Pandas基础-数据分组 =====
# 课程来源：B站 BV1sHU9BmEne
# 依赖：pip install pandas
# 知识点：
#   - groupby("列")：按一列或多列把数据分成若干组
#   - 分组聚合：sum()、mean()、count()、max()、min()、size()
#   - agg()：一次对多列做多种聚合
#   - as_index=False 或 reset_index()：把分组键还原成普通列
#   - 分组结果可以继续排序、筛选和绘图

import pandas as pd

df = pd.DataFrame({
    "订单号": ["A01", "A02", "A03", "B01", "B02", "B03"],
    "区域": ["华北", "华北", "华东", "华东", "华南", "华南"],
    "产品": ["A", "B", "A", "B", "A", "B"],
    "销量": [10, 15, 8, 12, 20, 6],
    "金额": [1000, 1500, 800, 1200, 2000, 600],
})

print("原始数据：")
print(df)

print("\n按区域统计总金额：")
print(df.groupby("区域")["金额"].sum())

print("\n按区域统计平均金额：")
print(df.groupby("区域")["金额"].mean())

print("\n按区域统计订单数：")
print(df.groupby("区域")["订单号"].count())

print("\n按区域和产品统计总金额：")
print(df.groupby(["区域", "产品"])["金额"].sum())

print("\n一次性计算金额的总和、均值、最大值，以及销量总和：")
print(df.groupby("区域").agg({
    "金额": ["sum", "mean", "max"],
    "销量": "sum",
}))

print("\n分组键保留为普通列：")
print(df.groupby("区域", as_index=False)["金额"].sum())

print("\n分组后按总金额降序排序：")
summary = df.groupby("区域", as_index=False)["金额"].sum()
print(summary.sort_values("金额", ascending=False))

# ===== 练习题 =====
# 1. 按“区域”统计总金额和平均金额，并打印结果。
# 2. 按“区域”和“产品”分组统计销量总和，再按销量降序排序。
# 3. 用 agg 同时计算每个区域的金额总和、均值、最大值，并用 reset_index() 还原成普通列。
