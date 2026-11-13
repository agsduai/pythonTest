# ===== 第341课：可视化-组合图与双轴 =====
# 知识点：
#   - 一张图叠加两种图表：柱状（量）+ 折线（率），讲一个完整故事
#   - twinx() 双 y 轴：两个量纲差异大的序列共用一个 x 轴
#   - 双轴要“明示轴名 + 颜色对应”，否则读者分不清哪根轴是谁的
# 依赖：pip install matplotlib

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

months = ["7月", "8月", "9月", "10月", "11月"]
revenue = [120, 135, 128, 160, 172]                       # 销售额（万元）
growth = [8, 12.5, -5.2, 25, 7.5]                          # 环比增长率（%）

fig, ax1 = plt.subplots(figsize=(9, 4.5))

# 左轴：销售额柱状
bars = ax1.bar(months, revenue, color="#4C78A8", width=0.55, label="销售额（万元）")
ax1.set_ylabel("销售额（万元）", color="#4C78A8")
ax1.tick_params(axis="y", labelcolor="#4C78A8")
ax1.bar_label(bars, fmt="%g", padding=2)                   # 柱顶标数值

# 右轴：增长率折线（twinx 共享 x 轴）
ax2 = ax1.twinx()
ax2.plot(months, growth, color="#D62728", marker="o", linewidth=2, label="环比增长（%）")
ax2.set_ylabel("环比增长（%）", color="#D62728")
ax2.tick_params(axis="y", labelcolor="#D62728")
ax2.axhline(0, color="#D62728", alpha=0.25, linestyle=":")

# 图例合并：两根轴的句柄拼在一起
handles = [bars, ax2.lines[0]]
ax1.legend(handles, [h.get_label() for h in handles], loc="upper left")

ax1.set_title("销售额（柱）与环比增长（线）：双轴组合图")
fig.tight_layout()
fig.savefig("charts_341.png", dpi=100)
print("已保存 charts_341.png")

os.remove("charts_341.png")

# ===== 练习题 =====
# 1. 把增长率换成“利润率”，调整右轴刻度范围让两条线少打架。
# 2. 给负增长月份的柱子改成红色（提示：循环判断后逐柱 set_color）。
# 3. 思考：什么情况下双轴是“坏图表”？（提示：两轴刻度可随意缩放制造假相关）
