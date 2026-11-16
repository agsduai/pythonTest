# ===== 第869课：贝叶斯推断与采样方法-MetropolisHastings MCMC =====
# 知识点：
#   - MCMC：构造一条马尔可夫链，其平稳分布 = 目标分布 -> 用样本代表后验
#   - Metropolis-Hastings：提议 q(x'|x)，按 min(1, p(x')q(x)/p(x)q(x')) 接受
#   - 对称提议（随机游走）时接受率简化为 p(x')/p(x)
#   - 关键诊断：接受率（0.2~0.5 合理）、burn-in 丢弃、混合是否覆盖多峰
#   - 与网格法对比：不穷举但带噪声；高维的救命稻草
# 依赖：无（标准库）
import math
import random


def logsumexp(a, b):
    m = max(a, b)
    if m == -math.inf:
        return m
    return m + math.log(math.exp(a - m) + math.exp(b - m))


def log_target(x):
    """双峰目标：两个高斯峰 (±2, 窄) 叠加（常数因子对 MH 无影响）。"""
    return logsumexp(-(x - 2.0) ** 2 / 0.5, -(x + 2.0) ** 2 / 0.5)


def metropolis(logp, x0, n, sigma, rng, burn=1000):
    """随机游走 MH：返回 (样本, 接受率)。"""
    x, lp = x0, logp(x0)
    samples, accepted = [], 0
    for i in range(n + burn):
        prop = x + rng.gauss(0.0, sigma)
        lp_prop = logp(prop)
        if math.log(rng.random() + 1e-300) < lp_prop - lp:
            x, lp = prop, lp_prop
            accepted += 1
        if i >= burn:
            samples.append(x)
    return samples, accepted / (n + burn)


rng = random.Random(0)

print("== 目标分布：双峰 exp(-(x-2)²/0.5) + exp(-(x+2)²/0.5) ==")
print("  峰在 ±2，两个峰互不相连 —— 考验链的跨峰能力")

print("\n== 提议步长 σ 对链行为的影响 ==")
print(f"  {'σ':>6}{'接受率':>9}{'均值':>9}{'正侧样本占比':>14}")
for sigma in (0.3, 1.0, 3.0, 8.0):
    samples, acc = metropolis(log_target, 2.0, 20000, sigma, rng, burn=1000)
    pos_ratio = sum(1 for s in samples if s > 0) / len(samples)
    mean = sum(samples) / len(samples)
    print(f"  {sigma:>6.1f}{acc:>9.2%}{mean:>9.3f}{pos_ratio:>14.1%}")
print("  σ 太小 -> 接受率高但走不远；σ 太大 -> 接受率低；σ≈峰宽时最平衡")
print("  双峰对称 -> 均值应 ≈ 0，正侧占比 ≈ 50%（跨峰成功才会对称）")

print("\n== 轨迹可视化（每 40 个样本取 1 个）==")
samples, acc = metropolis(log_target, 2.0, 4000, 2.0, rng, burn=1000)
print("  " + "".join("|" if s > 0 else "." for s in samples[::40]))

print("\n== 直方图 vs 目标密度 ==")
bins = {}
for s in samples:
    b = round(s)
    bins[b] = bins.get(b, 0) + 1
peak = max(bins.values())
for b in range(-4, 5):
    cnt = bins.get(b, 0)
    bar = "#" * int(cnt / peak * 40)
    density = math.exp(log_target(b))
    print(f"  {b:>3} {bar:<40} 样本 {cnt:>4} | 密度 {density:.4f}")
print("  直方图形状与密度形状一致（比例不同，MH 只需相对密度）")

print("\n== 单峰目标：与网格真值对照 ==")


def log_normal_target(x):
    return -x * x / 2.0                       # 标准正态


samples_n, acc_n = metropolis(log_normal_target, 0.0, 50000, 2.4, rng, burn=1000)
m = sum(samples_n) / len(samples_n)
v = sum((s - m) ** 2 for s in samples_n) / len(samples_n)
print(f"  N(0,1) 真值: 均值 0, 方差 1")
print(f"  MH 估计:     均值 {m:.4f}, 方差 {v:.4f}（自相关使有效样本数 < 总数）")

print("\n== burn-in 与自相关 ==")
print(f"  前 100 个样本均值 = {sum(samples_n[:100]) / 100:.3f}（可能偏离起点附近）")
print(f"  全部样本均值      = {m:.3f}")
lag1 = sum((samples_n[i] - m) * (samples_n[i - 1] - m)
           for i in range(1, 2000)) / 1999 / v
print(f"  相邻样本相关系数 ≈ {lag1:.2f}（随机游走 MH 的固有自相关，需 thinning）")

print("\n== 小结 ==")
for line in (
    "  MH 只需要能算 log 目标密度 —— 黑盒友好，这正是它流行的原因",
    "  接受率与步长互相牵制；自适应 MH 会把接受率调到 ~0.234（高维）",
    "  多峰分布要求提议足够大才能跨峰；否则链会被困在单峰",
    "  burn-in、thinning、多链对比是使用 MCMC 的基本卫生习惯",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现独立 MH：提议 q(x') = N(0,1) 与目标无关，推导接受率公式并验证。
# 2. 实现自适应步长：每 500 步根据接受率放大/缩小 σ（目标 0.44），观察混合改善。
# 3. 用 MH 采样第 868 课的双峰后验，并与网格密度对比直方图。
# 4. 思考：为什么 MH 的接受公式里只需要密度「成比例」而不需要归一化常数？
