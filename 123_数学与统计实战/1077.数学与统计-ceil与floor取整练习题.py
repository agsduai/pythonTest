# ===== 第1077课：数学与统计-ceil与floor取整 =====
# 知识点：
#   - math.ceil()：向上取整（不管小数多大都进 1）；math.floor()：向下取整
#   - int() 直接截断小数（向零取整），正数等同 floor，负数不同
#   - round() 是"四舍五入"，但 .5 会往偶数舍（银行家舍入）
#   - 实际场景：按人分出租车（向上）、整箱采购（向上）、地板面积（向下）

# 案例一：三种取整对比
import math

x = 3.2
print(f"ceil({x}) = {math.ceil(x)}")    # 4 向上
print(f"floor({x}) = {math.floor(x)}")  # 3 向下
print(f"int({x}) = {int(x)}")           # 3 截断
print(f"round({x}) = {round(x)}")       # 3 四舍五入

# 负数时 int 与 floor 不一样
y = -3.2
print(f"ceil({y}) = {math.ceil(y)}, floor({y}) = {math.floor(y)}, int({y}) = {int(y)}")

# 案例二：打车分车 —— 向上取整
# 场景：17 个人，每辆车坐 4 人，需要几辆车
people, per_car = 17, 4
cars = math.ceil(people / per_car)
print(f"{people} 人需要 {cars} 辆车")  # 4.25 -> 5 辆

# 案例三：整箱采购 —— 向上取整到整箱
# 场景：需要 130 瓶水，一箱 24 瓶
need, per_box = 130, 24
boxes = math.ceil(need / per_box)
print(f"需要买 {boxes} 箱（{boxes * per_box} 瓶，多出 {boxes * per_box - need} 瓶）")

# 案例四：地板砖数量 —— 先向下看能铺满几块
# 场景：7.8 米长的墙，每块砖 1.2 米
wall, tile = 7.8, 1.2
full_tiles = math.floor(wall / tile)
print(f"能完整铺 {full_tiles} 块，剩余 {wall - full_tiles * tile:.2f} 米需切割")

# 案例五：round 的 .5 陷阱
print(f"round(2.5) = {round(2.5)}")   # 2 不是 3！往偶数舍
print(f"round(3.5) = {round(3.5)}")   # 4 往偶数舍
print("要严格的四舍五入可用 int(x + 0.5)（正数）或 decimal 模块")

# ===== 练习题 =====
# 1. 55 个学生每 8 人一组，用 ceil 算需要几组、floor 算能组满几组，分别打印。
# 2. 写函数 minutes_fee(minutes)：停车 1 小时内 5 元，之后每满半小时 2 元（用 ceil 按 0.5 小时计），停 95 分钟应收费 5 + 2*2 = 9 元。
# 3. 用 round、ceil、floor 分别处理 [2.5, 3.5, -2.5, -3.5]，输出三个结果列表并比较差异。
