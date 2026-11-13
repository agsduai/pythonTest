# ===== 第148课：数据分析-Matplotlib基础-入门 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - Matplotlib 是 Python 最常用的静态绘图库，pyplot 提供类似 MATLAB 的绘图接口
#   - 绘图三步：准备数据 → 调用绘图函数（如 plot）→ 用 show 显示图表
#   - 中文字体：默认字体不含中文，需设置 font.sans-serif（Windows 常用 SimHei）
#   - 负号显示：设置 axes.unicode_minus=False，避免坐标轴负号显示为方块
# 依赖：pip install matplotlib

import matplotlib.pyplot as plt

# 中文与负号设置必须在绘图之前完成
plt.rcParams["font.sans-serif"] = ["SimHei"]   # Windows 自带黑体
plt.rcParams["axes.unicode_minus"] = False     # 正常显示坐标轴负号

# 准备数据：一周的最高气温
days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
temps = [22, 24, 21, 26, 28, 27, 25]

plt.figure(figsize=(8, 4))          # 创建画布，宽 8 英寸、高 4 英寸
plt.plot(days, temps)               # x 轴为星期，y 轴为温度
plt.title("一周最高气温")            # 图表标题
plt.xlabel("星期")                   # x 轴名称
plt.ylabel("温度（℃）")              # y 轴名称
plt.show()                          # 显示图表

# 说明：若在无图形界面的环境运行，可把 show() 换成 savefig("line.png")

# ===== 练习题 =====
# 1. 把示例数据换成你所在城市一周的最低气温，重新绘制折线图。
# 2. 给折线加上红色圆点标记（marker="o", color="red"），观察效果。
# 3. 把图片保存为 "temperature.png"，并说明 dpi 参数的作用。
