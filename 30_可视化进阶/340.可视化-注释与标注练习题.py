# ===== 第340课：可视化-注释与标注 =====
# 知识点：
#   - annotate：箭头指向“最值得看的那一点”（峰值、拐点）
#   - axhline/axvline：参考线（平均线、目标线）
#   - text：补充说明文字；legend 图例；title/label 必备三件套
#   - 图表叙事：让读者 3 秒内抓住重点，比画得炫更重要
# 依赖：pip install matplotlib

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

rng = np.random.default_rng(3)
days = np.arange(1, 31)
sales = rng.integers(200, 800, size=30).cumsum() / 10 + 300   # 递增趋势的日销量

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(days, sales, color="#1f77b4", marker="o", markersize=3, label="日销量")

# ---- 平均参考线 ----
mean_val = sales.mean()
ax.axhline(mean_val, color="gray", linestyle="--", alpha=0.7)
ax.text(1, mean_val + 8, f"月均值 {mean_val:.0f}", color="gray", fontsize=9)

# ---- 峰值标注：箭头 + 文本 ----
peak_idx = sales.argmax()
ax.annotate(
    f"峰值 {sales[peak_idx]:.0f}（第 {peak_idx + 1} 天）",
    xy=(days[peak_idx], sales[peak_idx]),
    xytext=(days[peak_idx] - 9, sales[peak_idx] + 25),
    arrowprops=dict(arrowstyle="->", color="red"),
    color="red",
)

# ---- 目标线与达标区间高亮 ----
ax.axhline(360, color="green", linestyle=":", label="目标 360")
ax.fill_between(days, 360, sales, where=sales >= 360, alpha=0.12, color="green")

ax.set_title("11月日销量：均值线 + 峰值标注 + 目标达成区间")
ax.set_xlabel("日期（日）")
ax.set_ylabel("销量")
ax.legend(loc="lower right")

fig.tight_layout()
fig.savefig("charts_340.png", dpi=100)
print("已保存 charts_340.png")

os.remove("charts_340.png")

# ===== 练习题 =====
# 1. 标注“最低谷”而不是峰值（argmin）。
# 2. 给 x 轴每隔 5 天画一条竖参考线（axvline + 循环）。
# 3. 思考：一张图放几个标注合适？多了会怎样？
