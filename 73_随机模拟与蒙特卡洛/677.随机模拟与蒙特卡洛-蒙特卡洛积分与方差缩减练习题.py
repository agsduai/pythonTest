# ===== 第677课：随机模拟与蒙特卡洛-蒙特卡洛积分与方差缩减 =====
# 知识点：
#   - 蒙特卡洛积分：∫ f ≈ (b-a)·mean(f(U_i))，误差 ∝ σ/√N
#   - 对偶变量 antithetic：用 U 与 1-U 配对，负相关可显著降方差
#   - 控制变量 control variate：减去已知期望的相关量，f - c·(g - E[g])
#   - 分层采样 stratification：把区间等分，每层各取样本，避免聚簇
#   - 重要性采样：按 |f| 的形状采样并加权，减少「白投」的样本
#   - 收敛诊断：跑多个独立批次，看估计值标准误是否随 N 按 1/√N 下降
# 依赖：无（标准库）
import math
import random
import statistics


def f(x):
    return math.sin(math.pi * x)          # ∫₀¹ = 2/π ≈ 0.63662

EXACT = 2 / math.pi


def mc_plain(n, seed):
    r = random.Random(seed)
    return statistics.fmean(f(r.random()) for _ in range(n))


def mc_antithetic(n, seed):
    r = random.Random(seed)
    vals = []
    for _ in range(n // 2):
        u = r.random()
        vals.extend([f(u), f(1 - u)])
    return statistics.fmean(vals)


def mc_control(n, seed):
    """用 g(x)=x 作控制变量，E[g]=1/2，f 与 g 正相关。"""
    r = random.Random(seed)
    xs = [r.random() for _ in range(n)]
    ys = [f(x) for x in xs]
    # 最优系数 c = Cov(f,g)/Var(g)，这里用样本估计
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    cov = statistics.fmean((x - mx) * (y - my) for x, y in zip(xs, ys))
    var = statistics.fmean((x - mx) ** 2 for x in xs)
    c = cov / var if var else 0
    return statistics.fmean(y - c * (x - 0.5) for x, y in zip(xs, ys)), c


def mc_stratified(n, seed, strata=10):
    r = random.Random(seed)
    vals = []
    for k in range(strata):
        lo, hi = k / strata, (k + 1) / strata
        for _ in range(n // strata):
            vals.append(f(r.uniform(lo, hi)))
    return statistics.fmean(vals)


print(f"== 目标 ∫₀¹ sin(πx) dx = {EXACT:.8f} ==")
print(f"  {'方法':<14}{'估计':<14}{'误差':<14}{'30 次估计标准差'}")
methods = {
    "普通 MC": lambda s: mc_plain(2000, s),
    "对偶变量": lambda s: mc_antithetic(2000, s),
    "控制变量": lambda s: mc_control(2000, s)[0],
    "分层采样": lambda s: mc_stratified(2000, s),
}
for name, fn in methods.items():
    est = statistics.fmean(fn(s) for s in range(30))
    spread = statistics.pstdev([fn(s) for s in range(30)])
    print(f"  {name:<14}{est:<14.7f}{abs(est - EXACT):<14.7f}{spread:.7f}")

print("\n== 控制变量的最优系数 ==")
_, c = mc_control(20000, 0)
print(f"  样本估计 c={c:.4f}（理论 Cov(f,x)/Var(x) 约 1.2~1.3）")
print("  c 越接近最优，方差缩减越明显；c=0 即退化为普通 MC")

print("\n== 误差随 N 的收敛 ==")
for n in (100, 500, 2000, 10000):
    errs = [abs(mc_plain(n, s) - EXACT) for s in range(50)]
    print(f"  N={n:<7} 平均绝对误差={statistics.fmean(errs):.6f}  "
          f"√N×误差={math.sqrt(n)*statistics.fmean(errs):.4f}（应大致恒定）")

print("\n== 重要性采样（估计 ∫₀¹ √x dx = 2/3）==")
# 按 p(x)=1/(2√x) 采样（即 x=U²），权重 f/p = √x / (1/(2√x)) = 2x
def importance(n, seed):
    r = random.Random(seed)
    return statistics.fmean(2 * (r.random() ** 2) for _ in range(n))

def plain_sqrt(n, seed):
    r = random.Random(seed)
    return statistics.fmean(math.sqrt(r.random()) for _ in range(n))

print(f"  理论值 = {2/3:.8f}")
for n in (1000, 10000):
    a = statistics.fmean(plain_sqrt(n, s) for s in range(20))
    b = statistics.fmean(importance(n, s) for s in range(20))
    print(f"  N={n:<7} 普通={a:.6f}(spread={statistics.pstdev([plain_sqrt(n,s) for s in range(20)]):.6f})  "
          f"重要性={b:.6f}(spread={statistics.pstdev([importance(n,s) for s in range(20)]):.6f})")
print("  按被积函数形状采样，方差明显更小")

print("\n== 高维优势（维数灾难的反面）==")
for d in (1, 2, 5, 10):
    # 估计 d 维单位立方体里 |x|² < d/3 的概率示意（仅展示网格点数对比）
    grid = 10 ** d
    print(f"  d={d:>2}: 确定性网格 {grid:.0e} 点 vs MC 固定 10^5 点，与维度无关")
print("  确定性求积误差 ∝ N^(-r/d)，维度升高迅速失效；MC 恒为 1/√N")

print("\n== 方差缩减选型 ==")
for line in [
    "  对偶变量: 零成本，f 单调时效果最好",
    "  控制变量: 需要已知期望且相关的辅助量",
    "  分层采样: 实现简单，对平滑函数稳定有效",
    "  重要性采样: 收益最大但选错提议分布会方差爆炸",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给 mc_stratified 增加「按层方差分配样本数」的自适应分层。
# 2. 用对偶变量 + 控制变量组合，测量方差是否进一步下降。
# 3. 估计 5 维单位球体积，对比 MC 与网格法的可行性。
# 4. 思考：为什么高维积分里 MC 反而优于确定性网格？
