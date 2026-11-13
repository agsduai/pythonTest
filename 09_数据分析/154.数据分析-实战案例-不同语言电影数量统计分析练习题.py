# ===== 第154课：数据分析-实战案例-不同语言电影数量统计分析 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - Series.value_counts() 统计每个语言出现的次数，默认按次数降序排列
#   - 分组统计也可用 groupby("language").size()，两者结果一致
#   - plt.bar / plt.barh 展示不同语言的电影数量对比
#   - 类别较多时横向柱状图更易读，排序后趋势更直观
# 依赖：pip install pandas matplotlib

import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

movies = pd.DataFrame({
    "title": ["肖申克的救赎", "霸王别姬", "千与千寻", "泰坦尼克号", "盗梦空间",
              "无间道", "大话西游", "楚门的世界", "寄生虫", "海上钢琴师"],
    "language": ["英语", "汉语", "日语", "英语", "英语",
                 "汉语", "汉语", "英语", "韩语", "意大利语"],
})

counts = movies["language"].value_counts()          # 按数量从多到少排序
print(counts)

plt.figure(figsize=(8, 4.5))
bars = plt.bar(counts.index, counts.values, width=0.6, color="#55A868")
for bar, value in zip(bars, counts.values):
    plt.text(bar.get_x() + bar.get_width() / 2,
             bar.get_height() + 0.05,
             str(value), ha="center", va="bottom")

plt.title("不同语言电影数量统计", fontsize=14)
plt.xlabel("语言")
plt.ylabel("电影数量（部）")
plt.ylim(0, counts.max() + 1)
plt.tight_layout()
plt.savefig("movies_per_language.png", dpi=300)
plt.show()

# ===== 练习题 =====
# 1. 增加几部不同语言的电影，重新统计并画出柱状图。
# 2. 改用 barh 绘制横向柱状图，并给柱顶加上数量标注。
# 3. 计算各语言电影数量占总数的百分比（counts / counts.sum()），保留两位小数。
