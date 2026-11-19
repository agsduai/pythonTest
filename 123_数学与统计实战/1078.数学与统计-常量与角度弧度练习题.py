# ===== 第1078课：数学与统计-常量与角度弧度 =====
# 知识点：
#   - math.pi 圆周率、math.e 自然常数，比手写 3.14 精确
#   - sin/cos/tan 接收"弧度"，日常的"度"要先用 radians() 转换
#   - degrees() 把弧度转回角度；直角三角函数用于算坡度、投影
#   - 实际场景：圆周长/面积、坡道长度、钟表指针夹角

# 案例一：圆的周长与面积
import math

r = 5
print(f"半径 {r} 的圆：周长 {2 * math.pi * r:.2f}，面积 {math.pi * r ** 2:.2f}")
# 对比手写 3.14 的误差
print(f"用 3.14 算面积：{3.14 * r ** 2:.2f}（少了 {math.pi * r ** 2 - 3.14 * r ** 2:.4f}）")

# 案例二：角度转弧度求三角函数
# 场景：30 度坡道，前进 10 米实际升高多少
angle_deg = 30
ramp_len = 10
height = ramp_len * math.sin(math.radians(angle_deg))
print(f"30° 坡道前进 {ramp_len} 米，升高 {height:.2f} 米")

# 案例三：直角三角形已知斜边和角度求边
# 场景：梯子靠墙，梯子 5 米、与地面夹角 65 度
ladder, deg = 5, 65
wall_height = ladder * math.sin(math.radians(deg))
ground_dist = ladder * math.cos(math.radians(deg))
print(f"梯子顶端高度 {wall_height:.2f} 米，底部距墙 {ground_dist:.2f} 米")

# 案例四：钟表指针夹角
# 场景：3:40 时时针与分针的夹角
hour, minute = 3, 40
minute_angle = minute * 6          # 分针每分钟 6°
hour_angle = hour * 30 + minute * 0.5  # 时针每小时 30°，每分钟再走 0.5°
angle = abs(hour_angle - minute_angle)
angle = min(angle, 360 - angle)    # 取劣角
print(f"{hour}:{minute} 时夹角：{angle}°")

# 案例五：反三角算角度
# 场景：知道对边和斜边，求角度
opposite, hypotenuse = 4, 5
angle_rad = math.asin(opposite / hypotenuse)
print(f"角度：{math.degrees(angle_rad):.1f}°")  # 约 53.1°

# ===== 练习题 =====
# 1. 用 math.pi 计算直径 10 米圆桌的周长与面积，保留 2 位小数。
# 2. 写函数 tan_slope(rise, run)：由升高和水平距离算坡度角度（atan + degrees），坡道升高 3 米、水平 4 米应为约 36.87°。
# 3. 计算 60° 三角函数对照表：sin/cos/tan 各打印一行（用 radians 转换），sin(60°) 应约 0.866。
