# ===== 第342课：可视化-直方图与箱线图 =====
# 知识点：
#   - 直方图 hist：看“分布形态”（正态？偏态？双峰？）
#   - 箱线图 boxplot：中位数/四分位/离群值 一图看尽
#   - bins 数量影响观感：太少糊成一团，太琐碎噪
#   - 与第319课对照：mean/std 是数字摘要，分布图是“全景照片”
# 依赖：pip install matplotlib numpy

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

rng = np.random.default_rng(5)
scores = np.concatenate([
    rng.normal(72, 8, 400),          # 大多数人
    rng.normal(93, 3, 40),           # 少数“学霸”造成右侧凸起
])

fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

# ---- 直方图：分布形态 ----
axes[0].hist(scores, bins=25, color="#4C78A8", edgecolor="white")
axes[0].axvline(scores.mean(), color="red", linestyle="--", label=f"均值 {scores.mean():.1f}")
axes[0].axvline(np.median(scores), color="orange", linestyle=":", label=f"中位数 {np.median(scores):.1f}")
axes[0].set_title("成绩分布直方图（右偏：被学霸拉高均值）")
axes[0].set_xlabel("分数")
axes[0].legend()

# ---- 箱线图：三组对比 + 离群值 ----
data = [rng.normal(72, 8, 200), rng.normal(78, 6, 200), rng.normal(70, 14, 200)]
bp = axes[1].boxplot(data, tick_labels=["一班", "二班", "三班"], patch_artist=True)
for patch, color in zip(bp["boxes"], ["#8CD17D", "#4C78A8", "#F58518"]):
    patch.set_facecolor(color)
axes[1].set_title("三班成绩箱线图（点 = 离群值）")

fig.tight_layout()
fig.savefig("charts_342.png", dpi=100)
print("已保存 charts_342.png")
print(f"均值 {scores.mean():.1f} vs 中位数 {np.median(scores):.1f} → 均值被高分离群值拉高")

os.remove("charts_342.png")

# ===== 练习题 =====
# 1. 把 bins 改成 5 和 100，观察“过粗/过细”的问题。
# 2. 用箱线图对比“数学”和“语文”两科（自造数据）。
# 3. 思考：均值和中位数哪个更能代表“普通人水平”？结合本图说明。
