# ===== 第885课：概率图模型与结构化推断-高斯混合与EM算法 =====
# 知识点：
#   - 隐变量模型：观测数据由哪个分量生成是「看不见的」
#   - 似然对隐变量求和后没有闭式解 -> EM 算法：交替期望(E)与最大化(M)
#   - E 步：用当前参数算每个样本来自各分量的「责任」responsibility
#   - M 步：按责任加权重新估计均值/方差/混合比例 —— 都是解析解
#   - EM 保证对数似然单调不减（可观测单调上升验证），但只保证局部最优
#   - k-means 是 EM 的硬分配极限（方差→0 时责任变成 one-hot）
# 依赖：无（标准库）
import math
import random


def normal_pdf(x, mu, var):
    if var <= 1e-12:
        return 0.0
    return math.exp(-(x - mu) ** 2 / (2 * var)) / math.sqrt(2 * math.pi * var)


def make_data(rng, n=300):
    """真实参数：两分量 N(2.0, 0.5²) 权重0.35 与 N(6.0, 1.2²) 权重0.65。"""
    data = []
    for _ in range(n):
        if rng.random() < 0.35:
            data.append(rng.gauss(2.0, math.sqrt(0.5)))
        else:
            data.append(rng.gauss(6.0, math.sqrt(1.2)))
    return data


def log_likelihood(data, weights, mus, vars_):
    total = 0.0
    for x in data:
        p = sum(w * normal_pdf(x, m, v)
                for w, m, v in zip(weights, mus, vars_))
        total += math.log(max(p, 1e-300))
    return total


def em_gmm(data, k=2, rng=None, iters=30, init=None):
    if init is None:
        mus = [min(data) + (max(data) - min(data)) * (i + 1) / (k + 1)
               for i in range(k)]
    else:
        mus = list(init)
    weights = [1.0 / k] * k
    variances = [1.0] * k
    history = []
    for it in range(iters):
        # ---- E 步：责任 ----
        resp = []
        for x in data:
            probs = [w * normal_pdf(x, m, v)
                     for w, m, v in zip(weights, mus, variances)]
            total = sum(probs)
            resp.append([p / total for p in probs])
        # ---- M 步 ----
        nk = [sum(r[i] for r in resp) for i in range(k)]
        weights = [n / len(data) for n in nk]
        mus = [sum(r[i] * x for r, x in zip(resp, data)) / max(nk[i], 1e-9)
               for i in range(k)]
        variances = [sum(r[i] * (x - mus[i]) ** 2
                         for r, x in zip(resp, data)) / max(nk[i], 1e-9)
                     for i in range(k)]
        ll = log_likelihood(data, weights, mus, variances)
        history.append(ll)
    return weights, mus, variances, history, resp


rng = random.Random(31)
data = make_data(rng)
print("== 数据（真值已知）==")
print(f"  n = {len(data)}，真值：分量A N(2.0, 0.5²) 占 35%，分量B N(6.0, 1.2²) 占 65%")
mean_all = sum(data) / len(data)
print(f"  样本均值 = {mean_all:.3f}（双峰直方图：")
buckets = {}
for x in data:
    buckets[round(x)] = buckets.get(round(x), 0) + 1
for b in sorted(buckets):
    print(f"    {b:>4} {'#' * int(buckets[b] / max(buckets.values()) * 45)} {buckets[b]}")

print("\n== EM 迭代过程 ==")
weights, mus, vars_, ll_hist, resp = em_gmm(data, 2, rng, iters=30)
print(f"  {'迭代':>4}{'对数似然':>12}{'μ1':>8}{'μ2':>8}{'w1':>7}")
for i in (0, 1, 2, 3, 5, 9, 29):
    if i < len(ll_hist):
        print(f"  {i:>4}{ll_hist[i]:>12.3f}{mus[0] if mus[0] < mus[1] else mus[1]:>8.3f}"
              f"{mus[1] if mus[0] < mus[1] else mus[0]:>8.3f}"
              f"{weights[0] if mus[0] < mus[1] else weights[1]:>7.3f}")
mono = all(ll_hist[i + 1] >= ll_hist[i] - 1e-9 for i in range(len(ll_hist) - 1))
print(f"  对数似然单调不减: {mono}（EM 的理论保证）")

print("\n== 恢复的参数 vs 真值 ==")
order = sorted(range(2), key=lambda i: mus[i])
for i in order:
    print(f"  分量{chr(ord('A') + i)}: 权重 {weights[i]:.3f}, "
          f"均值 {mus[i]:.3f}, 方差 {vars_[i]:.3f}")
print("  真值:        权重 0.350, 均值 2.000/6.000, 方差 0.500/1.440")
print("  隐变量被 EM『隐式地填补』出来 —— 没有任何样本带标签")

print("\n== 初始化敏感性 ==")
print(f"  {'初始μ':<24}{'收敛后μ1,μ2':>22}{'最终LL':>10}")
for init in ([3.0, 4.0], [2.0, 6.0], [0.0, 3.0], [1.0, 1.5]):
    w2, m2, v2, h2, _ = em_gmm(data, 2, rng, iters=60, init=init)
    print(f"  {str(init):<24}{str([round(x, 2) for x in sorted(m2)]):>22}{h2[-1]:>10.3f}")
print("  EM 只保证局部最优：坏初始化可能陷入「两个分量挤在一起」的鞍点")

print("\n== 与 k-means 的关系 ==")
# 硬分配版：责任 one-hot（最近的均值）
mus_km = [2.0, 6.0]
for it in range(20):
    assign = [min(range(2), key=lambda i: abs(x - mus_km[i])) for x in data]
    for i in range(2):
        members = [x for x, a in zip(data, assign) if a == i]
        if members:
            mus_km[i] = sum(members) / len(members)
soft_share = [sum(r[i] for r in resp) / len(data) for i in range(2)]
km_share = [assign.count(i) / len(data) for i in range(2)]
print(f"  EM 软分配占比:  {soft_share}")
print(f"  k-means 硬分配: {km_share}")
print("  EM 是『带不确定性的 k-means』：方差大时边界样本两边都算一点")

print("\n== 小结 ==")
for line in (
    "  EM = 看不见的标签先用当前参数猜（E），再按猜的结果更新参数（M）",
    "  每一步都在优化同一个目标（对数似然），因此单调收敛",
    "  局部最优 + 初始化敏感 -> 多次随机重启是标准操作",
    "  GMM/隐变量是概率图模型的「无监督」主力，888 课用 EM 数据反学结构",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 k=3 的 EM 并用「随机重启 20 次」选最优解，报告分布。
# 2. 实现 MAP-EM：给方差加逆伽马先验、均值加正态先验，防止小分量方差爆炸。
# 3. 用 EM 拟合拉普拉斯混合（换成 Laplace 密度），比较与高斯混合的拟合差异。
# 4. 思考：为什么 EM 每步似然必增？如果 E 步的责任算错一步会发生什么？
