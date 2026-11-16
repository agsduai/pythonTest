# ===== 第868课：贝叶斯推断与采样方法-网格近似与后验计算 =====
# 知识点：
#   - 不是所有模型都有共轭形式 -> 通用方法：把参数空间切成细网格
#   - 网格近似三步：先验网格 × 逐点似然 -> 归一化 -> 后验网格
#   - 后验的一切（均值/中位数/区间/预测）都是网格上的加权和
#   - HDI（最高密度区间）：按密度从高到低累积到 95% 的区间，可不等尾
#   - 精度只受网格分辨率限制；维度高时网格指数爆炸（这是它的死穴）
# 依赖：无（标准库）
import math
import time


def binom_pmf(k, n, p):
    if p <= 0 or p >= 1:
        return 0.0
    return math.comb(n, k) * p ** k * (1 - p) ** (n - k)


def grid_posterior(k, n, prior_fn, lo=0.0, hi=1.0, points=2001):
    """p 的网格后验：返回 (xs, weights)。"""
    xs = [lo + (hi - lo) * i / (points - 1) for i in range(points)]
    weights = []
    for x in xs:
        like = binom_pmf(k, n, x)
        weights.append(prior_fn(x) * like)
    total = sum(weights)
    return xs, [w / total for w in weights]


def summarize(xs, weights, level=0.95):
    """加权均值、中位数、等尾区间。"""
    mean = sum(x * w for x, w in zip(xs, weights))
    cum = 0.0
    median = lo = hi = None
    tail = (1 - level) / 2
    for x, w in zip(xs, weights):
        cum += w
        if lo is None and cum >= tail:
            lo = x
        if median is None and cum >= 0.5:
            median = x
        if cum >= 1 - tail:
            hi = x
            break
    return mean, median, (lo, hi)


def hdi(xs, weights, level=0.95):
    """最高密度区间：按密度降序累积。"""
    order = sorted(range(len(xs)), key=lambda i: -weights[i])
    total = sum(weights)
    acc, chosen = 0.0, set()
    for i in order:
        chosen.add(i)
        acc += weights[i]
        if acc >= level:
            break
    picked = [xs[i] for i in chosen]
    return min(picked), max(picked)


print("== 模型：有偏硬币，观测 8/10 正面 ==")
k, n = 8, 10

print("\n== 三种先验下的后验 ==")
priors = {
    "均匀 Beta(1,1)":      lambda x: 1.0,
    "Jeffreys Beta(.5,.5)": lambda x: 0.0 if x <= 0 or x >= 1 else
        math.exp(-0.5 * math.log(x) - 0.5 * math.log(1 - x)),
    "强信息 Beta(6,6)":    lambda x: 0.0 if x <= 0 or x >= 1 else x ** 5 * (1 - x) ** 5,
}
print(f"  {'先验':<22}{'后验均值':>9}{'中位数':>9}{'95%等尾':>16}{'95%HDI':>16}")
for label, pf in priors.items():
    xs, w = grid_posterior(k, n, pf)
    mean, med, (lo, hi) = summarize(xs, w)
    hlo, hhi = hdi(xs, w)
    print(f"  {label:<22}{mean:>9.3f}{med:>9.3f}   [{lo:.3f},{hi:.3f}]   [{hlo:.3f},{hhi:.3f}]")
print("  数据 8/10 占主导：三种先验的后验差别不大 —— 大样本稀释先验")

print("\n== 对照共轭解析解 ==")
xs, w = grid_posterior(k, n, lambda x: 1.0)
mean_grid, _, _ = summarize(xs, w)
mean_exact = (1 + k) / (1 + n)          # Beta(1,1) 先验 -> Beta(9,3)
print(f"  网格均值 = {mean_grid:.5f}，解析均值 = {mean_exact:.5f}，"
      f"差 = {abs(mean_grid - mean_exact):.1e}（网格分辨率决定）")

print("\n== 后验预测：下一次正面概率 ==")
pred = sum(x * w for x, w in zip(xs, w))
print(f"  E[p|data] 即预测概率 = {pred:.4f}")
print(f"  与朴素频率 8/10 = 0.8 对比：均匀先验的 Beta(9,3) 后验把它拉低")

print("\n== 奇怪形状也照算：人工双峰密度 ==")


def bimodal_density(x):
    """两种机理叠加的似然：观测既可能来自 p≈0.2，也可能来自 p≈0.8。"""
    return math.exp(-((x - 0.2) / 0.05) ** 2) + math.exp(-((x - 0.8) / 0.05) ** 2)


xs2 = [i / 2000 for i in range(2001)]
raw = [bimodal_density(x) for x in xs2]
total2 = sum(raw)
w2 = [v / total2 for v in raw]
m2, med2, ci2 = summarize(xs2, w2)
h2 = hdi(xs2, w2)
print(f"  双峰密度均值 = {m2:.3f}（在两峰之间，却不是任何一峰）")
print(f"  等尾 95% = [{ci2[0]:.3f}, {ci2[1]:.3f}]  vs  HDI = [{h2[0]:.3f}, {h2[1]:.3f}]")
print("  双峰时 HDI 应拆成两段；等尾区间会包含低密度区 —— 结论必须配合密度图")
print("  网格法只关心『每个格点的密度』，形状再怪都能照常归一化")

print("\n== 网格法成本 ==")
for points in (101, 501, 2001, 5001):
    t0 = time.perf_counter()
    grid_posterior(k, n, lambda x: 1.0, points=points)
    print(f"  {points:>5} 格点 -> {(time.perf_counter() - t0) * 1000:.1f} ms")
print("  1 维很便宜；2 维平方、10 维 10^20 —— 高维必须用 MCMC（869 课）")

print("\n== 小结 ==")
for line in (
    "  网格近似 = 贝叶斯计算的『穷举基准』，结果精确到网格步长",
    "  任何奇怪的后验形状都能处理，且每一步都可解释",
    "  HDI 与等尾区间在偏态/多峰后验下差异显著",
    "  维度一高就爆炸 -> 869 课的 MCMC 用随机采样换掉穷举",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现两参数网格：Bernoulli 换成「正态均值 μ 已知 σ=1、观测 5 个样本」，
#    网格 100×100，验证成本与均值精度。
# 2. 实现真正的 HDI（允许多段区间）：对上面双峰后验输出两段 HDI。
# 3. 用网格法计算 P(p > 0.75 | data)，并与 Beta(9,3) 解析值（网格积分验证）对照。
# 4. 思考：网格法的后验预测分布怎么算？为什么它天然比点估计更适合决策？
