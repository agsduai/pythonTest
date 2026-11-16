# ===== 第678课：随机模拟与蒙特卡洛-随机过程与马尔可夫链 =====
# 知识点：
#   - 马尔可夫性：下一状态只依赖当前状态，与历史无关
#   - 转移矩阵 P（行随机，每行和为 1）；n 步分布 = π₀ · Pⁿ
#   - 稳态分布 π 满足 πP = π；用幂迭代收敛，或解方程
#   - 吸收态：一旦进入不再离开；平均吸收时间、吸收概率是常见问题
#   - 随机游走：一维 +/-1、带边界、赌徒破产问题
#   - 蒙特卡洛模拟与解析解互相验证，是检验实现的可靠手段
# 依赖：无（标准库）
import math
import random
import statistics

print("== 两状态天气链 ==")
STATES = ("晴", "雨")
P = [[0.8, 0.2],
     [0.3, 0.7]]
print("  转移矩阵 P:")
for row, s in zip(P, STATES):
    print(f"    {s}: {row}")
print("  行和校验:", [round(sum(row), 6) for row in P])

def mat_vec(M, v):
    return [math.fsum(M[i][j] * v[j] for j in range(len(v))) for i in range(len(M))]

def mat_mul(A, B):
    n = len(A)
    return [[math.fsum(A[i][k] * B[k][j] for k in range(n)) for j in range(n)]
            for i in range(n)]

def power(M, n):
    R = [[1.0 if i == j else 0.0 for j in range(len(M))] for i in range(len(M))]
    for _ in range(n):
        R = mat_mul(R, M)
    return R

pi0 = [1.0, 0.0]        # 从「晴」出发
print("\n== n 步后的分布（解析） ==")
for n in (1, 2, 5, 10, 20):
    pn = mat_vec(power(P, n), pi0)
    print(f"  n={n:>2}: 晴={pn[0]:.5f} 雨={pn[1]:.5f}")

print("\n== 幂迭代求稳态 ==")
v = [0.5, 0.5]
for i in range(30):
    v = mat_vec(P, v)
print(f"  π = [晴 {v[0]:.6f}, 雨 {v[1]:.6f}]")
print(f"  验证 πP = π: {[round(x, 6) for x in mat_vec(P, v)]}")
print("  解析解（由 0.2π晴 = 0.3π雨）: 晴=0.6 雨=0.4 ->",
      abs(v[0] - 0.6) < 1e-6)

print("\n== 蒙特卡洛模拟验证 ==")
def simulate_chain(P, start, steps, seed):
    r = random.Random(seed)
    state = start
    counts = [0, 0]
    for _ in range(steps):
        u = r.random()
        acc = 0.0
        for j, p in enumerate(P[state]):
            acc += p
            if u < acc:
                state = j
                break
        counts[state] += 1
    return [c / steps for c in counts]

for steps in (1000, 10000, 100000):
    freq = simulate_chain(P, 0, steps, 42)
    print(f"  {steps:>7} 步: 晴={freq[0]:.4f} 雨={freq[1]:.4f} "
          f"（稳态 0.6/0.4）")

print("\n== 一维随机游走（带吸收壁 0 与 N）==")
def gambler_ruin(start, N, p=0.5, seed=0):
    """返回 (是否到达 N, 用了多少步)。"""
    r = random.Random(seed)
    x, steps = start, 0
    while 0 < x < N:
        x += 1 if r.random() < p else -1
        steps += 1
        if steps > 100000:
            break
    return x == N, steps

for p in (0.4, 0.5, 0.6):
    wins = [gambler_ruin(10, 20, p, seed=s)[0] for s in range(2000)]
    rate = sum(wins) / len(wins)
    theory = (1 - ((1-p)/p)**10) / (1 - ((1-p)/p)**20) if p != 0.5 else 0.5
    print(f"  p={p}: 模拟胜率={rate:.4f} 理论={theory:.4f}")

print("\n== 平均吸收时间 ==")
times = [gambler_ruin(10, 20, 0.5, seed=s)[1] for s in range(2000)]
print(f"  模拟均值={statistics.fmean(times):.1f} 步，理论 = i(N-i) = {10*10} 步")
print("  中位数:", statistics.median(times), "（分布右偏，均值 > 中位数）")

print("\n== 三状态链：吸收态 ==")
# 0=浏览 1=加购 2=下单(吸收) 3=离开(吸收)
P2 = [[0.6, 0.3, 0.0, 0.1],
      [0.2, 0.5, 0.2, 0.1],
      [0.0, 0.0, 1.0, 0.0],
      [0.0, 0.0, 0.0, 1.0]]

def absorbing(P, start, seed, max_steps=1000):
    r = random.Random(seed)
    s, steps = start, 0
    while steps < max_steps:
        u, acc = r.random(), 0.0
        for j, p in enumerate(P[s]):
            acc += p
            if u < acc:
                s = j
                break
        steps += 1
        if P[s][s] == 1.0:
            return s, steps
    return s, steps

outcomes = [absorbing(P2, 0, seed=s)[0] for s in range(5000)]
rate = sum(o == 2 for o in outcomes) / len(outcomes)
print(f"  从「浏览」出发最终下单概率 ≈ {rate:.4f}")
steps = [absorbing(P2, 0, seed=s)[1] for s in range(5000)]
print(f"  平均 {statistics.fmean(steps):.1f} 步进入吸收态")

print("\n== 马尔可夫链要点 ==")
for line in [
    "  稳态存在需链不可约且非周期；有吸收态时没有唯一稳态",
    "  幂迭代收敛速度由次大特征值决定（谱隙）",
    "  模拟与解析互验：不一致通常说明转移矩阵写错了",
    "   MCMC 用「构造一条以目标分布为稳态的链」来采样复杂分布",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 求解三状态链的吸收概率（解线性方程组），与模拟结果对比。
# 2. 实现带「反射壁」的随机游走，对比吸收壁的稳态行为。
# 3. 用 Metropolis-Hastings 采样标准正态分布，验证样本矩。
# 4. 思考：为什么有吸收态的链不能用幂迭代求唯一稳态？
