# ===== 第151课：数据分析-Matplotlib基础-图表实战(饼状图) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 饼状图用于展示各部分占整体的比例，接口为 plt.pie(sizes, labels=...)
#   - autopct 显示百分比，startangle 控制起始角度，explode 让某一块分离突出
#   - plt.axis("equal") 让饼图保持正圆，避免被拉伸成椭圆
#   - 百分比格式 "%1.1f%%" 表示保留一位小数并显示百分号
# 依赖：pip install matplotlib

import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

labels = ["剧情", "喜剧", "动作", "爱情", "科幻"]
sizes = [35, 22, 18, 15, 10]
colors = ["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974"]
explode = [0, 0, 0.08, 0, 0]        # 只把“动作”这一块分离出来

plt.figure(figsize=(6, 6))
plt.pie(sizes,                      # 每块的大小
        labels=labels,              # 每块的名称
        autopct="%1.1f%%",          # 百分比保留 1 位小数
        startangle=90,              # 从 12 点钟方向开始
        colors=colors,              # 自定义配色
        explode=explode,            # 突出显示某一块
        shadow=True,                # 阴影增强立体感
        wedgeprops={"edgecolor": "white"})  # 白色分隔线
plt.title("电影类型占比")
plt.axis("equal")                   # 保证饼图为正圆
plt.legend(loc="upper right", title="类型")
plt.tight_layout()
plt.savefig("genre_pie.png", dpi=300)
plt.show()

# ===== 练习题 =====
# 1. 把 sizes 换成一天的作息时间（学习、睡觉、吃饭、娱乐、运动），绘制饼图。
# 2. 让占比最大的一块分离突出，并去掉阴影。
# 3. 使用 autopct=lambda p: f"{p:.0f}%" 让百分比不显示小数，观察效果。
