# ===== 第338课：可视化-子图与布局 =====
# 知识点：
#   - matplotlib 是第09章图表的“底层引擎”，本课补齐进阶用法
#   - subplots(r, c)：一次建好网格，axes[r][c] 定位
#   - 四种基础图表各占一格：折线/柱状/散点/饼图
#   - 本课用 Agg 后台渲染并保存 PNG（无弹窗）；自己练习可去掉 use("Agg")
#     并把 savefig 换成 plt.show()
# 依赖：pip install matplotlib

import os

import matplotlib
matplotlib.use("Agg")                      # 无界面渲染，供自动验证；交互练习可去掉
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]   # 中文显示
plt.rcParams["axes.unicode_minus"] = False              # 负号正常显示

fig, axes = plt.subplots(2, 2, figsize=(9, 7))
fig.suptitle("四种基础图表速览", fontsize=14)

# 折线图：趋势
x = list(range(1, 8))
axes[0][0].plot(x, [12, 9, 15, 11, 18, 14, 20], marker="o")
axes[0][0].set_title("折线图：趋势")

# 柱状图：对比
axes[0][1].bar(["键盘", "鼠标", "显示器"], [800, 300, 1500], color="#4C78A8")
axes[0][1].set_title("柱状图：对比")

# 散点图：相关性
xs = [160, 165, 170, 175, 180]
axes[1][0].scatter(xs, [55, 60, 66, 70, 76])
axes[1][0].set_title("散点图：身高体重")

# 饼图：占比
axes[1][1].pie([4, 3, 2, 1], labels=["A", "B", "C", "D"], autopct="%1.0f%%")
axes[1][1].set_title("饼图：占比")

fig.tight_layout()
fig.savefig("charts_338.png", dpi=100)
print("已保存 charts_338.png")

os.remove("charts_338.png")

# ===== 练习题 =====
# 1. 把布局改成 1×4 横排，观察 tight_layout 的自动调整。
# 2. 给每张子图加 xlabel/ylabel。
# 3. 思考：fig 与 axes 的关系是什么？（画布 vs 每格画笔）
