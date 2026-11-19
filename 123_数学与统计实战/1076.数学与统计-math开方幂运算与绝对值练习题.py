# ===== 第1076课：数学与统计-math开方幂运算与绝对值 =====
# 知识点：
#   - import math：math.sqrt() 开平方、math.pow() 幂运算，结果都是 float
#   - abs() 是内置函数不需要 math；** 也能算幂（2**3 = 8）
#   - sqrt 负数会报 ValueError，先判断再算
#   - 实际场景：勾股定理算距离、面积反推边长

# 案例一：开平方与幂运算
import math

print(f"√16 = {math.sqrt(16)}")          # 4.0
print(f"2 的 10 次方：{math.pow(2, 10)}")  # 1024.0
print(f"** 运算符：{2 ** 10}")            # 1024（整数）
print(f"|−8| = {abs(-8)}")

# 案例二：勾股定理算两点距离
# 场景：外卖骑手到商家的直线距离
import math

ax, ay = 0, 0
bx, by = 3, 4
distance = math.sqrt((bx - ax) ** 2 + (by - ay) ** 2)
print(f"两点距离：{distance}")  # 5.0

# 案例三：已知面积反推边长
# 场景：正方形地砖，面积 22.5 平方米，边长多少
area = 22.5
side = math.sqrt(area)
print(f"边长：{side:.3f} 米")

# 案例四：sqrt 的负数陷阱
def safe_sqrt(x):
    if x < 0:
        print(f"{x} 不能开平方（负数），返回 None")
        return None
    return math.sqrt(x)

print(f"safe_sqrt(9)：{safe_sqrt(9)}")
print(f"safe_sqrt(-9)：{safe_sqrt(-9)}")

# 案例五：立方根 —— 负数要用 ** 处理
volume = 27
print(f"立方根：{volume ** (1/3)}")  # 3.0（近似）
print(f"负数立方根：{-27 ** (1/3):.4f}")  # 注意 ** 优先级：-27**(1/3) 是 -(27**(1/3))

# ===== 练习题 =====
# 1. 用 math.sqrt 计算 5、12、13 组成的直角三角形斜边（两直角边 5 和 12），结果应为 13。
# 2. 写函数 circle_radius(area)：由圆面积反推半径（r = sqrt(area/pi)），面积 78.5 时半径约 5.0。
# 3. 用 pow 或 ** 打印 2 的 1~10 次方列表，并说明为什么数学上用 math.pow 而日常更常用 **。
