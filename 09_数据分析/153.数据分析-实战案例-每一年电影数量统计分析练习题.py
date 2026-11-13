# ===== 第153课：数据分析-实战案例-每一年电影数量统计分析 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - groupby("year").size() 按年份分组，统计每组的电影数量
#   - sort_index() 让年份按时间顺序排列，避免图表的 x 轴乱序
#   - plt.bar 绘制年度数量柱状图；xticks(rotation=45) 防止年份标签重叠
#   - 柱顶用 plt.text 标注数量，读图时无需对照 y 轴
# 依赖：pip install pandas matplotlib

import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

movies = pd.DataFrame({
    "title": ["霸王别姬", "肖申克的救赎", "大话西游", "泰坦尼克号", "楚门的世界",
              "千与千寻", "无间道", "盗梦空间", "星际穿越", "让子弹飞",
              "疯狂动物城", "流浪地球"],
    "year": [1993, 1994, 1995, 1997, 1998, 2001, 2002, 2010, 2014, 2010, 2016, 2019],
})

# 按年份分组统计数量，并按年份排序
counts = movies.groupby("year").size().sort_index()
print(counts)

plt.figure(figsize=(9, 4.5))
plt.bar(counts.index.astype(str), counts.values, width=0.6, color="#4C72B0")
for year, value in zip(counts.index.astype(str), counts.values):
    plt.text(year, value + 0.05, str(value), ha="center", va="bottom", fontsize=10)

plt.title("每年电影数量统计", fontsize=14)
plt.xlabel("年份")
plt.ylabel("电影数量（部）")
plt.xticks(rotation=45)                    # 年份标签旋转，避免相互遮挡
plt.ylim(0, counts.max() + 1.5)            # 顶部留白给数值标注
plt.tight_layout()
plt.savefig("movies_per_year.png", dpi=300)
plt.show()

# ===== 练习题 =====
# 1. 给数据补充两部同一年份的电影，重新统计并画图。
# 2. 把柱状图换成折线图（plt.plot），比较哪种更适合展示年份趋势。
# 3. 用 counts.idxmax() 找出电影数量最多的年份，并打印出来。
