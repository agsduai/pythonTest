# ===== 第344课：可视化-综合案例-销售仪表盘 =====
# 知识点：
#   - 综合运用：子图布局（338）+ 配色（339）+ 标注（340）+ 双轴（341）+ 分布图（342）
#   - 产出：一张 2×2 仪表盘 —— 趋势/结构/健康度/分布一次讲完
#   - 数据来自 pandas（第28章），图表回到 matplotlib —— 两者本是一家人
# 依赖：pip install matplotlib numpy pandas

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

# ---- 数据：90 天、4 品类的订单模拟 ----
rng = np.random.default_rng(11)
dates = pd.date_range("2026-09-01", periods=90, freq="D")
daily = pd.DataFrame(
    rng.integers(200, 900, size=(90, 4)),
    index=dates,
    columns=["数码", "服饰", "食品", "图书"],
)
daily["合计"] = daily.sum(axis=1)

fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
fig.suptitle("季度销售仪表盘", fontsize=15)

# ---- 图1：每日销售趋势 + 7日均线 ----
ax = axes[0][0]
ax.plot(daily.index, daily["合计"], color="#BBB", linewidth=0.8, label="每日")
ax.plot(daily.index, daily["合计"].rolling(7).mean(), color="#D62728", linewidth=2, label="7日均线")
ax.set_title("每日销售趋势")
ax.legend(fontsize=8)

# ---- 图2：品类结构（柱状）----
ax = axes[0][1]
totals = daily[["数码", "服饰", "食品", "图书"]].sum()
bars = ax.bar(totals.index, totals.values, color=["#4C78A8", "#F58518", "#54A24B", "#B279A2"])
ax.bar_label(bars, fmt="%d", fontsize=8)
ax.set_title("品类销售额对比")

# ---- 图3：双轴 —— 销量 vs 客单价 ----
ax = axes[1][0]
ax2 = ax.twinx()
ax.bar(range(3), [daily["合计"][:30].mean(), daily["合计"][30:60].mean(), daily["合计"][60:].mean()],
       color="#4C78A8", alpha=0.8)
ax.set_xticks(range(3), ["9月", "10月", "11月"])
ax2.plot(range(3), [312, 328, 345], color="#D62728", marker="o", label="客单价")
ax.set_ylabel("月销售额", color="#4C78A8")
ax2.set_ylabel("客单价", color="#D62728")
ax2.legend(fontsize=8)
ax.set_title("月度销量（柱）与客单价（线）")

# ---- 图4：客单价分布（直方图）----
ax = axes[1][1]
orders_amount = rng.gamma(shape=2, scale=160, size=1000)     # 常见的右偏订单金额
ax.hist(orders_amount, bins=30, color="#54A24B", edgecolor="white")
ax.axvline(np.median(orders_amount), color="red", linestyle="--",
           label=f"中位数 {np.median(orders_amount):.0f} 元")
ax.set_title("订单金额分布")
ax.legend(fontsize=8)

fig.tight_layout()
fig.savefig("dashboard_344.png", dpi=120)
print("已生成 dashboard_344.png（2×2 仪表盘）")

os.remove("dashboard_344.png")

# ===== 练习题 =====
# 1. 把图1 的均线周期改成 14 天，观察趋势是否更平滑。
# 2. 给仪表盘加第五张图：品类占比饼图（提示：改用 3×2 布局）。
# 3. 思考：仪表盘四张图的排序逻辑是什么？（先结论还是先细节）
