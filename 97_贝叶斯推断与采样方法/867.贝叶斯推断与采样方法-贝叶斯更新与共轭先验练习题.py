# ===== 第867课：贝叶斯推断与采样方法-贝叶斯更新与共轭先验 =====
# 知识点：
#   - 贝叶斯定理：posterior ∝ likelihood × prior
#   - 共轭先验：先验与后验属同一分布族 -> 更新只需「数参数」，无需数值积分
#   - Beta-Bernoulli：Beta(a,b) + k成功/n失败 -> Beta(a+k, b+n-k)
#   - Gamma-Poisson：Gamma(α,rate β) + 观测总和k/次数n -> Gamma(α+k, β+n)
#   - 后验均值同时融合先验与数据：小样本时先验权重自然更大
# 依赖：无（标准库）
import math


def beta_pdf(x, a, b):
    if x <= 0 or x >= 1:
        return 0.0
    logp = ((a - 1) * math.log(x) + (b - 1) * math.log(1 - x)
            - (math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)))
    return math.exp(logp)


def beta_mean(a, b):
    return a / (a + b)


def beta_mode(a, b):
    if a <= 1 or b <= 1:
        return None
    return (a - 1) / (a + b - 2)


def beta_credible(a, b, level=0.95, grid=2000):
    """网格法求等尾可信区间。"""
    xs = [(i + 0.5) / grid for i in range(grid)]
    pdfs = [beta_pdf(x, a, b) for x in xs]
    total = sum(pdfs)
    cum, lo, hi = 0.0, None, None
    tail = (1 - level) / 2
    for x, p in zip(xs, pdfs):
        cum += p / total
        if lo is None and cum >= tail:
            lo = x
        if cum >= 1 - tail:
            hi = x
            break
    return lo, hi


def gamma_pdf(x, alpha, rate):
    if x <= 0:
        return 0.0
    logp = ((alpha - 1) * math.log(x) - rate * x
            + alpha * math.log(rate) - math.lgamma(alpha))
    return math.exp(logp)


print("== 抛硬币：Beta-Bernoulli 共轭更新 ==")
a0, b0 = 2.0, 2.0                      # 先验 Beta(2,2)：微弱地偏好公平
flips = [1, 1, 0, 1, 1, 1, 1, 0, 1, 1]  # 10 次观测，8 正 2 反
print(f"  先验 Beta({a0:.0f},{b0:.0f})，后验均值先验 = {beta_mean(a0, b0):.3f}")
print(f"  观测序列 = {flips}（正面 {sum(flips)}/{len(flips)}）")
print(f"  {'观测数':>6}{'后验参数':>16}{'后验均值':>10}{'95%可信区间'}")
a, b = a0, b0
for i in range(1, len(flips) + 1):
    a += flips[i - 1]
    b += 1 - flips[i - 1]
    lo, hi = beta_credible(a, b)
    print(f"  {i:>6}  Beta({a:.0f},{b:.0f})    {beta_mean(a, b):>8.3f}   [{lo:.3f}, {hi:.3f}]")
print("  更新是增量的：多来一个数据点，a 或 b 加一即可")

print("\n== 先验强度 = 伪样本数 ==")
for a0x, b0x, label in ((1, 1, "均匀先验(0.5+0.5个样本)"),
                        (10, 10, "较强先验(10+10个样本)"),
                        (50, 50, "强先验(50+50个样本)")):
    a = a0x + 8
    b = b0x + 2
    print(f"  {label:<22} 后验均值 = {beta_mean(a, b):.3f}")
print("  观测同样是 8/10，先验越强后验越保守 —— 这是特性不是缺陷")

print("\n== 网格近似先看一眼后验形状 ==")
a, b = 10.0, 4.0
for x in (0.4, 0.6, 0.714, 0.8):
    print(f"  Beta(10,4) 在 p={x}: 密度 = {beta_pdf(x, a, b):.3f}")
print(f"  后验均值 = {beta_mean(a, b):.3f}，众数 = {beta_mode(a, b):.3f}（右偏分布：均值 < 众数）")

print("\n== 泊松：Gamma-Poisson 共轭 ==")
alpha0, beta0 = 2.0, 1.0               # 先验 Gamma(2, rate=1)：先验均值 2
calls = [3, 2, 4, 1, 2]                # 5 天的客服电话数
k = sum(calls)
n = len(calls)
alpha_post, beta_post = alpha0 + k, beta0 + n
print(f"  先验 Gamma(α={alpha0}, rate={beta0})，先验均值 = {alpha0 / beta0}")
print(f"  观测 {calls}：总和 {k}，天数 {n}")
print(f"  后验 Gamma(α={alpha_post}, rate={beta_post}) -> λ 后验均值 = "
      f"{alpha_post / beta_post:.3f}")
lo_grid = [gamma_pdf(x, alpha_post, beta_post) for x in
           [i / 10 for i in range(1, 80)]]
peak = (lo_grid.index(max(lo_grid)) + 1) / 10
print(f"  后验密度峰值 ≈ {peak}（解析众数 (α-1)/β = {(alpha_post - 1) / beta_post:.3f}）")

print("\n== 预测分布 ==")
print(f"  下一天来电数的后验预测 = 负二项分布，均值 = α/rate = {alpha_post / beta_post:.2f}")
print(f"  与观测平均 {k / n:.2f} 对比：先验把估计从 2.4 拉向 2.0 一点")

print("\n== 小结 ==")
for line in (
    "  共轭先验把贝叶斯更新变成参数代数：加计数即可，无需数值方法",
    "  Beta/Gamma 分别是 Bernoulli/Poisson 的天然搭档，Normal-Normal 对见练习",
    "  后验参数 = 先验参数 + 数据计数，「伪样本」解释了先验强度",
    "  下一课：没有共轭形式时怎么办 —— 网格近似",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Normal-Normal 共轭：已知方差的正态均值更新（精度相加），验证后验均值
#    是先验均值与样本均值的精度加权平均。
# 2. 实现「顺序更新 = 一次批量更新」实验：把数据逐条更新与一次算完对比参数。
# 3. 用 Beta(0.5, 0.5)（Jeffreys 先验）重做抛硬币例，对比三种先验的 95% 区间宽度。
# 4. 思考：为什么「无信息先验」在样本大时几乎不影响结论？共轭先验的主要
#    局限是什么？
