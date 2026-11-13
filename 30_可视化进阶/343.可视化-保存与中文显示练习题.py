# ===== 第343课：可视化-保存与中文显示 =====
# 知识点：
#   - 中文乱码根因：matplotlib 默认字体不含中文 → rcParams 换成系统字体
#   - 负号显示：axes.unicode_minus=False
#   - savefig：dpi 控制清晰度，bbox_inches="tight" 裁掉白边
#   - 常用格式：png（网页/PPT）、svg（无损缩放）、pdf（打印）
#   - 全局配置建议集中到项目公共模块，不要每张图抄一遍
# 依赖：pip install matplotlib

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- 中文与负号：两行标准配置 ----
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]   # Windows 微软雅黑；Mac 用 PingFang SC
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(6, 3.5))
ax.plot(["1月", "2月", "3月", "4月"], [10, -5, 8, 12], marker="o", label="环比变化")
ax.set_title("中文标题与负号 −5 都正常显示")
ax.legend()
fig.tight_layout()

# ---- 三种格式保存 ----
fig.savefig("chart_343.png", dpi=150, bbox_inches="tight")   # 位图：dpi 越高越清晰
fig.savefig("chart_343.svg")                                  # 矢量：无限缩放
fig.savefig("chart_343.pdf")                                  # 打印友好
print("已保存 png / svg / pdf 三种格式")

# ---- dpi 与清晰度 ----
fig.savefig("chart_343_small.png", dpi=50)                    # 低清：文件更小
print("150dpi：", os.path.getsize("chart_343.png"), "字节 | 50dpi：",
      os.path.getsize("chart_343_small.png"), "字节")

for f in ("chart_343.png", "chart_343.svg", "chart_343.pdf", "chart_343_small.png"):
    os.remove(f)

# 字体查找技巧：系统里有哪些可用中文字体
from matplotlib import font_manager

fonts = {f.name for f in font_manager.fontManager.ttflist if "YaHei" in f.name or "SimHei" in f.name}
print("本机可用中文字体：", sorted(fonts) or "（无，需安装或改用其他字体名）")

# ===== 练习题 =====
# 1. 把字体换成 SimHei（黑体）再画一张，对比观感。
# 2. 生成 dpi=300 的 PNG，用看图软件放大对比 150dpi。
# 3. 思考：为什么负号需要单独设置？（提示：unicode_minus 用的是 Unicode 减号）
