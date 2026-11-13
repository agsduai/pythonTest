# ===== 第150课：数据分析-Matplotlib基础-图表实战(柱状图) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 柱状图用于比较不同类别的数值大小，接口为 plt.bar(x, height)
#   - 常用参数：width 柱宽、color 颜色、edgecolor 边框、label 图例
#   - 横向柱状图 plt.barh(y, width)，类别名称较长时更易阅读
#   - 通过 plt.text 在柱顶标注数值；xticks(rotation=...) 防止类别名重叠
# 依赖：pip install matplotlib

import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

languages = ["Python", "Java", "C++", "JavaScript", "Go"]
counts = [128, 96, 58, 74, 41]

plt.figure(figsize=(8, 5))
bars = plt.bar(languages, counts, width=0.6, color="#4C72B0", edgecolor="white")

for bar, value in zip(bars, counts):                 # 遍历每个柱子，在柱顶写数值
    plt.text(bar.get_x() + bar.get_width() / 2,       # 柱子中心的 x 坐标
             bar.get_height() + 2,                    # 柱顶稍上方
             str(value), ha="center", va="bottom", fontsize=10)

plt.title("编程语言课程报名人数", fontsize=14)
plt.xlabel("语言")
plt.ylabel("人数")
plt.xticks(rotation=15)                              # 类别名略作旋转，避免挤在一起
plt.ylim(0, 150)                                     # 顶部留出数值标注空间
plt.tight_layout()
plt.savefig("language_bar.png", dpi=300)
plt.show()

# 横向柱状图变体：类别名很长时更合适
# plt.figure(figsize=(8, 5))
# plt.barh(languages, counts, color="#55A868")
# plt.title("编程语言课程报名人数（横向）")
# plt.xlabel("人数")
# plt.tight_layout()
# plt.show()

# ===== 练习题 =====
# 1. 把 counts 换成本班同学喜欢的运动项目人数，绘制柱状图并标注数值。
# 2. 用 barh 绘制横向柱状图，并按人数从高到低排序后再画。
# 3. 给柱子设置不同的颜色列表，并添加图例说明"报名人数"。
