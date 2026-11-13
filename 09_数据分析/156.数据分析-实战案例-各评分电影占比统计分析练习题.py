# ===== 第156课：数据分析-实战案例-各评分电影占比统计分析 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 连续评分需要先分箱（分组）再统计占比，pandas 提供 pd.cut 完成分箱
#   - pd.cut(data, bins, labels) 把评分映射到指定区间；include_lowest 包含左端点
#   - value_counts().sort_index() 按分数段顺序统计数量
#   - plt.pie 展示各评分段占比，autopct 显示百分比
# 依赖：pip install pandas matplotlib

import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

movies = pd.DataFrame({
    "title": ["肖申克的救赎", "霸王别姬", "千与千寻", "泰坦尼克号", "盗梦空间",
              "无间道", "大话西游", "楚门的世界", "疯狂动物城", "流浪地球",
              "某喜剧片", "某动作片"],
    "rating": [9.7, 9.6, 9.4, 9.5, 9.4, 9.3, 9.2, 9.4, 9.2, 7.9, 6.8, 5.6],
})

# 把 0~10 分切成 5 段，include_lowest 让 0 分也能落入第一段
bins = [0, 6, 7, 8, 9, 10]
labels = ["6分以下", "6-7分", "7-8分", "8-9分", "9-10分"]
rating_groups = pd.cut(movies["rating"], bins=bins, labels=labels, include_lowest=True)
rating_counts = rating_groups.value_counts().sort_index()
print(rating_counts)

plt.figure(figsize=(7, 7))
plt.pie(rating_counts.values,
        labels=rating_counts.index,
        autopct="%1.1f%%",              # 保留一位小数的百分比
        startangle=90,
        colors=["#C44E52", "#DD8452", "#CCB974", "#55A868", "#4C72B0"],
        wedgeprops={"edgecolor": "white"})
plt.title("各评分电影占比统计", fontsize=14)
plt.axis("equal")                       # 保证饼图为正圆
plt.tight_layout()
plt.savefig("rating_pie.png", dpi=300)
plt.show()

# ===== 练习题 =====
# 1. 把分箱改为 [0, 5, 7, 9, 10]，标签自定义为“低分/中分/高分/佳作”，重新绘图。
# 2. 用 rating_counts.sum() 计算电影总数，并验证各段数量之和是否相等。
# 3. 思考：如果不做分箱，直接对评分 value_counts，饼图会出现什么问题？
