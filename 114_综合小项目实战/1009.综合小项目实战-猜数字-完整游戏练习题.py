# ===== 第1009课：综合小项目实战-猜数字——完整游戏 =====
# 知识点：
#   - random.randint(a, b) 生成 [a, b] 范围内的随机整数
#   - 条件判断反馈提示：大了/小了/猜对了
#   - 次数统计与最佳记录
#   - 循环 + break 控制游戏流程
#   - 异常处理：用户输入非数字时的容错
# 依赖：无（标准库）
import random


def play_round(answer, rng, max_attempts=10):
    """玩一局猜数字。返回 (是否猜对, 尝试次数)。"""
    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        # 模拟用户输入（实际程序用 input()）
        guess = rng.randint(1, 100)

        if guess == answer:
            return True, attempts
        elif guess < answer:
            pass                               # 提示 "小了"
        else:
            pass                               # 提示 "大了"

        # 超过 7 次还没猜到就算输
        if attempts >= 7:
            break
    return False, attempts


def play_interactive(answer):
    """交互版（需要终端输入）。"""
    attempts = 0
    print(f"  我心里想了一个 1-100 的数字，你有 7 次机会猜它！")
    while attempts < 7:
        attempts += 1
        text = input(f"  第{attempts}次猜测: ").strip()
        try:
            guess = int(text)
        except ValueError:
            print(f"    '{text}' 不是数字，请输入 1-100 的整数")
            continue
        if guess < 1 or guess > 100:
            print(f"    {guess} 超出范围 (1-100)")
            continue
        if guess == answer:
            print(f"    ✓ 恭喜！你用了 {attempts} 次猜对了，答案是 {answer}")
            return True
        elif guess < answer:
            print(f"    小了")
        else:
            print(f"    大了")
    print(f"    7 次没猜到，答案是 {answer}")
    return False


print("== 猜数字游戏（模拟版，计算机自己猜）==")
rng = random.Random(178)
answer = rng.randint(1, 100)
print(f"  答案是 {answer}")
won, attempts = play_round(answer, rng)
print(f"  模拟结果: {'猜对' if won else '没猜到'}，用了 {attempts} 次")

print("\n== 策略演示：二分法猜数字 ==")
answer = 73
low, high = 1, 100
attempts = 0
while low <= high:
    attempts += 1
    guess = (low + high) // 2
    if guess == answer:
        print(f"  猜中！答案 {answer}，用了 {attempts} 次")
        break
    elif guess < answer:
        print(f"  第{attempts}次猜 {guess} -> 小了，范围缩小到 [{guess + 1}, {high}]")
        low = guess + 1
    else:
        print(f"  第{attempts}次猜 {guess} -> 大了，范围缩小到 [{low}, {guess - 1}]")
        high = guess - 1
print("  二分法最多需要 log₂(100) ≈ 7 次 —— 每次猜中间值是最优策略")

print("\n== 统计：1000 局二分法 ==")
total_attempts = 0
max_used = 0
for _ in range(1000):
    ans = rng.randint(1, 100)
    low, high = 1, 100
    count = 0
    while low <= high:
        count += 1
        guess = (low + high) // 2
        if guess == ans:
            break
        elif guess < ans:
            low = guess + 1
        else:
            high = guess - 1
    total_attempts += count
    max_used = max(max_used, count)
print(f"  1000 局平均 {total_attempts / 1000:.1f} 次，最多 {max_used} 次")
print("  理论最优 = ceil(log₂100) = 7 次 —— 每局都不超过")

# ===== 练习题 =====
# 1. 把游戏的范围改为 1-1000，计算二分法需要几次。
# 2. 实现「难度选择」：简单=范围 1-50 且 10 次，普通=1-100 且 7 次，困难=1-500 且 9 次。
# 3. 实现「计分系统」：越少次数得分越高（如 10 - 次数）× 100 分。
# 4. 思考：二分法为什么是猜数字的最优策略？如果提示改为「差了多少」呢？
