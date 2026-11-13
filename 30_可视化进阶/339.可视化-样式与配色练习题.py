# ===== 第339课：可视化-样式与配色 =====
# 知识点：
#   - plt.style.use：一键换整体风格（ggplot、seaborn-v0_8 等）
#   - color/linewidth/marker/alpha：单图精细控制
#   - 网格 grid(axis, alpha)：辅助读数但不抢戏
#   - 配色原则：同色系深浅表“同一维度”，对比色只留给要强调的系列
# 依赖：pip install matplotlib

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

months = ["7月", "8月", "9月", "10月", "11月"]
ours = [120, 135, 128, 160, 172]
rival = [110, 125, 140, 138, 150]

# ---- 风格系统：可用 plt.style.available 查看全部 ----
print("可用风格（部分）：", plt.style.available[:5])

fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

# 左图：默认风格 + 精细控制
axes[0].plot(months, ours, color="#2E7D32", linewidth=2.5, marker="o", label="我们")
axes[0].plot(months, rival, color="#9E9E9E", linewidth=1.5, linestyle="--", label="对手")
axes[0].grid(axis="y", alpha=0.3)
axes[0].legend()
axes[0].set_title("精细控制：突出主线、弱化对比线")

# 右图：ggplot 风格 + 强调色块
with plt.style.context("ggplot"):          # context：只在本块内生效
    axes[1].plot(months, ours, linewidth=2.5)
    axes[1].fill_between(months, ours, alpha=0.15, color="#D62728")
    axes[1].set_title("ggplot 风格 + 面积填充")

fig.tight_layout()
fig.savefig("charts_339.png", dpi=100)
print("已保存 charts_339.png")

os.remove("charts_339.png")

# ===== 练习题 =====
# 1. 用 style.context 分别尝试 "seaborn-v0_8-whitegrid" 与 "dark_background"。
# 2. 把对手线改成浅色面积图（fill_between），对比可读性。
# 3. 思考：为什么强调色一次只给一个系列？
