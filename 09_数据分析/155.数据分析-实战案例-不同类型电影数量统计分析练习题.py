# ===== 第155课：数据分析-实战案例-不同类型电影数量统计分析 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 一部电影可能有多个类型，字段形如 "剧情/犯罪"，需要先拆分再统计
#   - Series.str.split("/") 按分隔符拆成列表，explode() 把列表展开成多行
#   - value_counts() 统计每个类型出现的次数，默认降序
#   - plt.bar 展示类型数量对比，xticks(rotation=45) 防止标签重叠
# 依赖：pip install pandas matplotlib

import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

movies = pd.DataFrame({
    "title": ["肖申克的救赎", "霸王别姬", "千与千寻", "泰坦尼克号", "盗梦空间",
              "无间道", "大话西游", "楚门的世界", "疯狂动物城", "流浪地球"],
    "genres": ["剧情/犯罪", "剧情/爱情", "动画/奇幻", "剧情/爱情", "剧情/科幻",
               "剧情/犯罪", "喜剧/爱情", "剧情/科幻", "动画/喜剧", "科幻/冒险"],
})

# 先拆分为多个类型，再展开成一行一个类型，最后统计数量
genre_counts = movies["genres"].str.split("/").explode().value_counts()
print(genre_counts)

plt.figure(figsize=(9, 5))
bars = plt.bar(genre_counts.index, genre_counts.values,
               width=0.6, color="#C44E52")
for bar, value in zip(bars, genre_counts.values):
    plt.text(bar.get_x() + bar.get_width() / 2,
             bar.get_height() + 0.05,
             str(value), ha="center", va="bottom")

plt.title("不同类型电影数量统计", fontsize=14)
plt.xlabel("类型")
plt.ylabel("电影数量（部）")
plt.xticks(rotation=45)
plt.ylim(0, genre_counts.max() + 0.8)
plt.tight_layout()
plt.savefig("movies_per_genre.png", dpi=300)
plt.show()

# ===== 练习题 =====
# 1. 再添加 3 部电影，其中有的电影带两个以上类型，重新统计。
# 2. 计算类型数量的占比，并用饼图展示（提示：plt.pie）。
# 3. 思考：如果不先 explode，直接对 "剧情/犯罪" 计数会得到什么结果？
