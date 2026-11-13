# ===== 第328课：Pandas进阶-分组聚合进阶 =====
# 知识点：
#   - agg：一次拿多个统计量，还能自定义函数
#   - transform：聚合结果“贴回”每一行 —— 不改变表形状
#   - pd.cut：连续值分箱打标签（工资档位、年龄段）
#   - 经典应用：组内比较（工资是否高于本部门均值）
# 依赖：pip install pandas

import pandas as pd

df = pd.DataFrame({
    "姓名": ["小明", "小红", "小刚", "小丽", "小强", "小芳"],
    "部门": ["技术", "技术", "市场", "市场", "技术", "市场"],
    "工资": [15000, 18000, 9000, 12000, 14000, 11000],
})

# ---- agg：多统计量一次拿全 ----
print(df.groupby("部门")["工资"].agg(["count", "mean", "max"]).round(1), end="\n\n")

# 自定义聚合：最高与最低的差距
print("组内极差：", df.groupby("部门")["工资"].agg(lambda s: s.max() - s.min()).to_dict(), sep="")

# ---- transform：组统计贴回每行（行数不变）----
df["部门均值"] = df.groupby("部门")["工资"].transform("mean").round(1)
df["高于本部门均值"] = df["工资"] > df["部门均值"]
print(df[["姓名", "部门", "工资", "部门均值", "高于本部门均值"]], end="\n\n")

# ---- cut：连续值分箱 ----
bins = [0, 10000, 15000, 99999]
labels = ["1万以下", "1-1.5万", "1.5万以上"]
df["档位"] = pd.cut(df["工资"], bins=bins, labels=labels)
print("档位分布：", df["档位"].value_counts().to_dict())

# ===== 练习题 =====
# 1. 统计每个档位的人数与平均工资（groupby("档位")）。
# 2. 用 transform 找出“本部门工资最高的人”。
# 3. 思考：agg 与 transform 返回的形状差在哪？
