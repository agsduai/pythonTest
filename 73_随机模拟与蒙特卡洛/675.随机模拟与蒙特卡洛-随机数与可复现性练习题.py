# ===== 第675课：随机模拟与蒙特卡洛-随机数与可复现性 =====
# 知识点：
#   - random.Random(seed) 是独立实例；模块级 random 是共享全局实例
#   - 同一种子 + 同一调用序列 = 逐位可复现，模拟实验必须记录 seed
#   - random / secrets / numpy 的 RNG 互不兼容，别混用
#   - 常用分布：uniform、gauss/normalvariate、expovariate、choice/choices、shuffle
#   - 系统级熵用 secrets（令牌/密钥），模拟用 random（可复现）
#   - 蒙特卡洛误差 ∝ 1/√N：样本翻 4 倍，误差才减半
# 依赖：无（标准库）
import math
import random
import secrets
import statistics

print("== 种子与可复现性 ==")
seq1 = [random.Random(42).random() for _ in range(3)]
r = random.Random(42)
seq2 = [r.random() for _ in range(3)]
print("  每次新建 Random(42):", [round(x, 6) for x in seq1])
print("  同一实例连续取 3 个:", [round(x, 6) for x in seq2])
print("  注意：两种写法不同！前者是 3 次「第一个数」，要复用同一实例")

r1, r2 = random.Random(7), random.Random(7)
a = [(r1.random(), r1.randint(1, 100)) for _ in range(5)]
b = [(r2.random(), r2.randint(1, 100)) for _ in range(5)]
print("  同 seed 同调用序列完全一致:", a == b)
print("  序列:", [round(x, 3) for x, _ in a])

print("\n== 全局状态 vs 独立实例 ==")
random.seed(1)
g1 = random.random()
random.seed(1)
g2 = random.random()
print(f"  seed(1) 重置后同为 {g1:.6f} == {g2:.6f}: {g1 == g2}")
print("  但库函数若也用全局 random，会偷偷推进序列 -> 模拟要用独立实例")

print("\n== 常用分布 ==")
r = random.Random(2026)
samples = {
    "uniform(0,10)": [r.uniform(0, 10) for _ in range(5)],
    "gauss(0,1)": [round(r.gauss(0, 1), 3) for _ in range(5)],
    "expovariate(2)": [round(r.expovariate(2), 3) for _ in range(5)],
    "randint(1,6)": [r.randint(1, 6) for _ in range(10)],
}
for name, vals in samples.items():
    print(f"  {name:<16}: {vals}")

print("\n== choice / choices / sample / shuffle ==")
r = random.Random(3)
items = ["A", "B", "C", "D"]
print("  choice       :", r.choice(items))
print("  choices(k=8) :", r.choices(items, k=8))
print("  choices(带权):", r.choices(items, weights=[5, 3, 1, 1], k=8))
print("  sample(不重复):", r.sample(items, 3))
deck = list(range(10))
r.shuffle(deck)
print("  shuffle      :", deck)

print("\n== 用蒙特卡洛估 π（误差 ∝ 1/√N）==")
def estimate_pi(n, seed=1):
    r = random.Random(seed)
    inside = sum(1 for _ in range(n)
                 if r.random() ** 2 + r.random() ** 2 <= 1)
    return 4 * inside / n

print(f"  {'N':<10}{'估计 π':<14}{'绝对误差':<14}{'理论 1/√N 量级'}")
for n in (100, 1000, 10000, 100000):
    pi = estimate_pi(n)
    print(f"  {n:<10}{pi:<14.6f}{abs(pi - math.pi):<14.6f}{1 / math.sqrt(n):<14.4f}")
print("  N ×100 -> 误差约 /10，收敛很慢，这是蒙特卡洛的固有代价")

print("\n== 多次独立重复的标准误 ==")
runs = [estimate_pi(2000, seed=s) for s in range(30)]
print(f"  30 次独立估计: 均值={statistics.fmean(runs):.5f} "
      f"标准差={statistics.pstdev(runs):.5f}")
print(f"  理论标准误 ≈ stdev/√N_single ≈ {statistics.pstdev(runs):.5f}")
print("  报告结果要带置信区间，不能只给一个点估计")

print("\n== random vs secrets ==")
print("  random  : 伪随机、可复现、快 -> 模拟、抽样、游戏")
print("  secrets : 系统熵、不可预测  -> 令牌、密码、会话 ID")
print("  secrets.token_hex(8):", secrets.token_hex(8))
print("  secrets.randbelow(100):", secrets.randbelow(100))
print("  反例：用 random 生成重置令牌可被预测（第20章安全）")

print("\n== 实验记录规范 ==")
for line in [
    "  记录 seed、样本数 N、RNG 类型与库版本，否则无法复现",
    "  每个实验用独立 Random 实例，避免相互推进序列",
    "  并行实验要按「流编号」派生种子，别共用同一个 RNG",
    "  结论用多次重复的标准误/置信区间表达，而非单次结果",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 用 random.Random 派生 10 个独立子流，验证彼此序列不相关。
# 2. 估计「随机三点构成锐角三角形」的概率，并给出 95% 置信区间。
# 3. 对比 random.gauss 与「12 个均匀数之和减 6」的正态近似质量。
# 4. 思考：为什么并行蒙特卡洛不能让所有进程共用同一个 seed？
