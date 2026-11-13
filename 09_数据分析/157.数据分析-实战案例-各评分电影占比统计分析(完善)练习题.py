# ===== 第157课：数据分析-实战案例-各评分电影占比统计分析(完善) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 完善饼图：在百分比之外同时显示电影数量，信息更完整
#   - autopct 可以接收自定义函数，函数参数是百分比 pct
#   - pctdistance 控制百分比文字到圆心的距离，labeldistance 控制标签距离
#   - explode 突出关键分段，legend 统一展示各分段含义，避免引线拥挤
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

bins = [0, 6, 7, 8, 9, 10]
labels = ["6分以下", "6-7分", "7-8分", "8-9分", "9-10分"]
groups = pd.cut(movies["rating"], bins=bins, labels=labels, include_lowest=True)
counts = groups.value_counts().sort_index()

def autopct_with_count(values):
    """返回一个 autopct 函数：同时显示百分比和对应数量。"""
    total = sum(values)
    def inner(pct):
        count = int(round(pct * total / 100.0))
        return f"{pct:.1f}%\n({count}部)"
    return inner

# 突出占比最大的分段，让视觉重点更明确
explode = [0.06 if value == counts.max() else 0 for value in counts.values]

plt.figure(figsize=(8, 7))
plt.pie(counts.values,
        labels=counts.index,
        autopct=autopct_with_count(counts.values),
        startangle=90, explode=explode,
        colors=["#C44E52", "#DD8452", "#CCB974", "#55A868", "#4C72B0"],
        pctdistance=0.72,               # 百分比文字离圆心稍远
        labeldistance=1.08,             # 标签放在饼图外侧
        wedgeprops={"edgecolor": "white", "linewidth": 1})
plt.title("各评分电影占比统计（完善版）", fontsize=14)
plt.axis("equal")
plt.legend(loc="upper right", bbox_to_anchor=(1.25, 1.0), title="评分区间")
plt.tight_layout()
plt.savefig("rating_pie_improved.png", dpi=300, bbox_inches="tight")
plt.show()

# ===== 练习题 =====
# 1. 修改 autopct_with_count，让数量显示为“共 N 部”而不是“(N部)”。
# 2. 调整 pctdistance 与 labeldistance，观察文字位置的变化并说明作用。
# 3. 思考：饼图分段过多时为什么不适合继续用饼图？可以换成什么图？
