# ===== 第676课：随机模拟与蒙特卡洛-概率分布与采样 =====
# 知识点：
#   - 逆变换采样：由 CDF⁻¹(U) 生成任意分布的样本，U ~ Uniform(0,1)
#   - 指数分布 F(x)=1-e^(-λx) -> x = -ln(1-U)/λ
#   - Box-Muller：两个均匀数生成两个独立标准正态数
#   - 离散分布按累积权重二分查找（bisect），O(log k)
#   - 拒绝采样：用易采样的提议分布包住目标分布，按接受率过滤
#   - 样本矩（均值/方差/分位数）随 N 增大收敛到理论值（大数定律）
# 依赖：无（标准库）
import bisect
import math
import random
import statistics

print("== 逆变换采样：指数分布 ==")
def sample_exp(rng, lam):
    return -math.log1p(-rng.random()) / lam      # log1p 更稳（第653课）

r = random.Random(11)
for lam in (0.5, 2.0):
    xs = [sample_exp(r, lam) for _ in range(20000)]
    print(f"  λ={lam}: 理论均值={1/lam:.3f} 样本均值={statistics.fmean(xs):.3f} "
          f"理论方差={1/lam**2:.3f} 样本方差={statistics.pvariance(xs):.3f}")

print("\n== Box-Muller：标准正态 ==")
def sample_normals(rng, n):
    out = []
    for _ in range((n + 1) // 2):
        u1, u2 = rng.random(), rng.random()
        z0 = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
        z1 = math.sqrt(-2 * math.log(u1)) * math.sin(2 * math.pi * u2)
        out.extend([z0, z1])
    return out[:n]

zs = sample_normals(random.Random(5), 20000)
print(f"  均值={statistics.fmean(zs):.4f} (理论 0)  方差={statistics.pvariance(zs):.4f} (理论 1)")
for k in (1, 2, 3):
    frac = sum(abs(z) <= k for z in zs) / len(zs)
    theory = {1: 0.6827, 2: 0.9545, 3: 0.9973}[k]
    print(f"  |Z| <= {k}σ: 样本={frac:.4f} 理论={theory:.4f}")

print("\n== 离散分布：累积权重 + bisect ==")
class Discrete:
    def __init__(self, weights, rng):
        self.values = list(weights)
        self.rng = rng
        total = sum(weights.values())
        self.cum, acc = [], 0.0
        for v, w in weights.items():
            acc += w / total
            self.cum.append(acc)

    def sample(self):
        u = self.rng.random()
        i = bisect.bisect_left(self.cum, u)
        return self.values[i]

d = Discrete({"A": 5, "B": 3, "C": 1, "D": 1}, random.Random(9))
draws = [d.sample() for _ in range(20000)]
from collections import Counter
cnt = Counter(draws)
print(f"  权重 {{A:5,B:3,C:1,D:1}} -> 频率 {dict(cnt)}")
for k, w in {"A": 5/10, "B": 3/10, "C": 1/10, "D": 1/10}.items():
    print(f"    {k}: 样本={cnt[k]/len(draws):.4f} 理论={w:.4f}")

print("\n== 拒绝采样：半圆密度 f(x)=2/π·√(1-x²), x∈[-1,1] ==")
def rejection_sample(rng, n):
    out = []
    trials = 0
    while len(out) < n:
        trials += 1
        x = rng.uniform(-1, 1)
        y = rng.uniform(0, 2 / math.pi)        # 提议：矩形上界
        if y <= 2 / math.pi * math.sqrt(1 - x * x):
            out.append(x)
    return out, len(out) / trials

xs, acc_rate = rejection_sample(random.Random(21), 10000)
print(f"  接受率={acc_rate:.3f}（理论 = 面积比 ≈ {math.pi/4:.3f}）")
print(f"  样本均值={statistics.fmean(xs):.4f}（理论 0，对称性）")
print(f"  样本二阶矩={statistics.fmean(x*x for x in xs):.4f}（理论 0.25）")

print("\n== 大数定律：样本均值收敛 ==")
r = random.Random(77)
xs_all = [r.random() for _ in range(50000)]
print(f"  {'N':<9}{'样本均值':<14}{'与 0.5 的差'}")
for n in (10, 100, 1000, 10000, 50000):
    m = statistics.fmean(xs_all[:n])
    print(f"  {n:<9}{m:<14.6f}{abs(m - 0.5):.6f}")

print("\n== 中心极限定理（均值的分布变窄）==")
for n in (1, 5, 30):
    means = [statistics.fmean(random.Random(1000 + i * 31 + n).random()
                              for _ in range(n)) for i in range(2000)]
    print(f"  每次取 {n:>2} 个均匀数求均值: 标准差={statistics.pstdev(means):.4f} "
          f"理论={1 / math.sqrt(12 * n):.4f}")

print("\n== 采样陷阱 ==")
for line in [
    "  U=0 时 -ln(1-U) 才安全；直接 -ln(1-U) 在 U→1 会精度损失",
    "  拒绝采样的接受率太低会浪费算力，要选贴近目标的提议分布",
    "  伪随机数有周期，超大规模实验用 PCG/Xoshiro 等现代 RNG",
    "  相关性检验：连续样本不该有可预测的自相关",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 用逆变换采样实现幂律分布 f(x)=2x (0<x<1)，验证均值 2/3。
# 2. 实现重要性采样估计 π，对比简单投点的方差大小。
# 3. 给 Discrete 加别名方法（Alias Method），把单次采样降到 O(1)。
# 4. 思考：为什么拒绝采样的效率取决于「提议分布与目标分布的贴合度」？
