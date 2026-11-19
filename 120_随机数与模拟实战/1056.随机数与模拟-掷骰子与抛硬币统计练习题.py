# ===== 第1056课：随机数与模拟-掷骰子与抛硬币统计 =====
# 知识点：
#   - 大量重复随机实验后统计频率，频率会逼近理论概率（大数定律）
#   - 抛硬币：choice(["正", "反"]) 或 randint(0, 1)
#   - 统计计数用 dict + get()，或 str.count / list.count
#   - 模拟是"用代码做实验"，对比理论值是最常用的验证手段

# 案例一：抛硬币 1000 次
import random

random.seed(10)  # 固定种子便于复现讨论
flips = [random.choice(["正", "反"]) for _ in range(1000)]
heads = flips.count("正")
print(f"正面 {heads} 次，反面 {1000 - heads} 次，频率 {heads / 1000:.3f}")
print("理论概率 0.5，次数越多频率越接近")

# 案例二：掷骰子 6000 次，验证每面约 1/6
counts = {i: 0 for i in range(1, 7)}
for _ in range(6000):
    face = random.randint(1, 6)
    counts[face] += 1
for face, c in counts.items():
    print(f"{face} 点：{c} 次（{c / 6000:.3f}，理论 {1/6:.3f}）")

# 案例三：两颗骰子点数和 —— 和为 7 概率最高
# 理论：2 有 1 种组合，7 有 6 种组合，11 有 2 种
sum_counts = {}
for _ in range(10000):
    s = random.randint(1, 6) + random.randint(1, 6)
    sum_counts[s] = sum_counts.get(s, 0) + 1
top = sorted(sum_counts.items(), key=lambda kv: kv[1], reverse=True)[:3]
print(f"出现最多的三种点数和：{top}")  # 7 应该名列前茅

# 案例四：连续正面最长纪录
# 场景：连投硬币，最长连续出现几次正面
longest, current = 0, 0
for _ in range(1000):
    if random.random() < 0.5:
        current += 1
        longest = max(longest, current)
    else:
        current = 0
print(f"1000 次投掷中最长连续正面：{longest} 次")

# ===== 练习题 =====
# 1. 模拟抛硬币 100 次，分别用 choice 和 randint 两种方式各做一遍，打印两种方式的正面次数。
# 2. 掷骰子 600 次，统计 6 点出现的次数与频率，并与 1/6 ≈ 0.167 对比。
# 3. 写函数 gamble(n)：模拟"连续猜大猜小"游戏，胜率理论 50%，运行 n 局打印胜局数与胜率（保留 2 位小数）。
