# ===== 第149课：数据分析-Matplotlib基础-图表信息详解 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 画布 figure 与坐标区 axes；figsize 控制画布尺寸，dpi 控制输出清晰度
#   - 图表要素：标题 title、轴标签 xlabel/ylabel、刻度 ticks、图例 legend、网格 grid、数据标注
#   - 多折线对比：多次调用 plot，再用 legend 区分不同数据系列
#   - 布局与保存：tight_layout 防止标签被裁切，savefig 导出图片
# 依赖：pip install matplotlib

import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

months = ["1月", "2月", "3月", "4月", "5月", "6月"]
beijing = [2, 5, 12, 20, 26, 30]
shanghai = [5, 7, 11, 17, 22, 26]

plt.figure(figsize=(8, 5), dpi=100)                  # 画布大小与分辨率
plt.plot(months, beijing, marker="o", color="#1f77b4", label="北京")
plt.plot(months, shanghai, marker="s", linestyle="--", color="#ff7f0e", label="上海")

plt.title("上半年平均气温对比", fontsize=14)          # 标题及字号
plt.xlabel("月份", fontsize=11)                       # x 轴标签
plt.ylabel("气温（℃）", fontsize=11)                  # y 轴标签
plt.xticks(rotation=0)                               # x 轴刻度文字（可旋转防重叠）
plt.yticks([0, 10, 20, 30, 40])                      # 自定义 y 轴刻度
plt.legend(loc="upper left")                         # 图例及位置
plt.grid(True, linestyle=":", alpha=0.6)             # 网格线
plt.annotate("最高点", xy=(6, 30), xytext=(4.2, 33),
             arrowprops=dict(arrowstyle="->"))        # 箭头标注：xy 指向点，xytext 是文字位置
plt.tight_layout()                                   # 自动调整布局，避免标签被裁切
plt.savefig("temperature_compare.png", dpi=300)      # 保存图片
plt.show()

# ===== 练习题 =====
# 1. 说出 title、xlabel、ylabel、legend、grid 各自的作用。
# 2. 把图例移到右下角，并给两条折线分别设置不同的线宽 linewidth。
# 3. 用 annotate 标注上海 6 月的气温点，并解释 xy 与 xytext 的区别。
