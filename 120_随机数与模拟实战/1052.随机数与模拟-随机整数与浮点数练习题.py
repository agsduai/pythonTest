# ===== 第1052课：随机数与模拟-随机整数与浮点数 =====
# 知识点：
#   - random.random()：0 <= x < 1 的随机小数；randint(a, b)：a~b 之间闭区间整数
#   - randrange(start, stop, step)：不含 stop，可指定步长（偶数/整十数）
#   - uniform(a, b)：a~b 之间随机小数（也含端点）
#   - 每次运行结果都不同——这是"随机"的本质

# 案例一：基础随机数
import random

print(f"随机小数 [0,1)：{random.random():.4f}")
print(f"随机整数 [1,10]：{random.randint(1, 10)}")     # 两头都含
print(f"随机小数 [1.5, 5.5]：{random.uniform(1.5, 5.5):.2f}")

# 案例二：randrange 与步长
# 场景：随机生成偶数座位号、整十价格
print(f"随机偶数：{random.randrange(0, 20, 2)}")       # 0~18 的偶数
print(f"整十价格：{random.randrange(10, 100, 10)}")    # 10~90 的整十数

# 案例三：掷骰子模拟
# 场景：模拟一次掷骰子和十次掷骰子
def roll_dice():
    return random.randint(1, 6)

rolls = [roll_dice() for _ in range(10)]
print(f"单次掷骰：{roll_dice()}，十次结果：{rolls}")

# 案例四：生成验证码数字
# 场景：6 位短信验证码
code = "".join(str(random.randint(0, 9)) for _ in range(6))
print(f"验证码：{code}")

# 案例五：随机折扣模拟
# 场景：大转盘抽奖，折扣 5~9.9 折
discount = random.uniform(0.5, 0.99)
print(f"抽到折扣：{discount:.2f}，100 元商品折后 {100 * discount:.2f} 元")

# ===== 练习题 =====
# 1. 生成 5 个 1~100 的随机整数放入列表并打印；再打印其中的最大值和最小值。
# 2. 用 randrange 生成 3 个 0~90（含 0 不含 100）之间步长为 5 的随机数（即 5 的倍数）。
# 3. 写函数 roll_pair()：模拟掷两颗骰子返回点数和，调用 5 次打印每次的两个点数与总和。
