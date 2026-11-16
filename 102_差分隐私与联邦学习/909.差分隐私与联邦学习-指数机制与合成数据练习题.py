# ===== 第909课：差分隐私与联邦学习-指数机制与合成数据 =====
# 知识点：
#   - 指数机制：DP 地做「选择」——按效用 exp(ε·u/(2Δu)) 抽取选项
#   - 适合离散选择：最受欢迎的商品、最优的分类阈值、合成数据的生成
#   - DP 合成数据：从噪声直方图采样生成『假个体』—— 可自由二次分析
#   - 合成数据的优势：一次生成、无限次使用（隐私预算只花一次）
#   - 效用评估：合成数据的统计量 vs 真实统计量
# 依赖：无（标准库）
import math
import random


def laplace_noise(scale, rng):
    u = rng.uniform(-0.5, 0.5)
    return -math.copysign(1.0, u) * scale * math.log(1 - 2 * abs(u) + 1e-18)


def noisy_histogram(data, categories, epsilon, rng):
    from collections import Counter
    counts = Counter(data)
    return {c: counts.get(c, 0) + laplace_noise(1.0 / epsilon, rng)
            for c in categories}


def exponential_mechanism(categories, utilities, epsilon, sensitivity, rng):
    """DP 地选择效用最高的类别（减最大值防溢出）。"""
    u_max = max(utilities)
    weights = [math.exp(epsilon * (u - u_max) / (2 * sensitivity))
               for u in utilities]
    total = sum(weights)
    r, acc = rng.random(), 0.0
    for c, w in zip(categories, weights):
        acc += w / total
        if r < acc:
            return c
    return categories[-1]


def synthetic_from_histogram(noisy_hist, n, rng):
    """把噪声直方图变成合法分布后采样 n 个『合成个体』。"""
    clipped = {k: max(0.0, v) for k, v in noisy_hist.items()}
    total = sum(clipped.values())
    probs = {k: v / total for k, v in clipped.items()}
    keys = list(probs)
    cum = []
    acc = 0.0
    for k in keys:
        acc += probs[k]
        cum.append(acc)
    samples = []
    for _ in range(n):
        r = rng.random()
        idx = 0
        while idx < len(cum) - 1 and r > cum[idx]:
            idx += 1
        samples.append(keys[idx])
    return samples


rng = random.Random(102)

print("== 场景：最受欢迎的课程类别 ==")
categories = ["编程", "设计", "营销", "数据"]
data = ["编程"] * 210 + ["设计"] * 95 + ["营销"] * 60 + ["数据"] * 135
from collections import Counter
true_counts = Counter(data)
print(f"  真实票数: {dict(true_counts)}")

print("\n== 指数机制：DP 地选『最佳类别』==")
print(f"  {'ε':>6}{'选中编程的频率':>16}{'平均效用损失':>12}")
for eps in (0.1, 0.5, 2.0, 8.0):
    wins = 0
    utility_loss = 0.0
    true_best = max(categories, key=lambda c: true_counts[c])
    for _ in range(1000):
        utilities = [true_counts[c] for c in categories]
        choice = exponential_mechanism(categories, utilities, eps, 1.0, rng)
        wins += (choice == true_best)
        utility_loss += true_counts[true_best] - true_counts[choice]
    print(f"  {eps:>6.1f}{wins / 1000:>16.1%}{utility_loss / 1000:>12.2f}")
print("  ε 大 → 几乎总选最优；ε 小 → 接近均匀随机 —— 同一根杠杆")
print("  指数机制与拉普拉斯机制的换算：连续效用下两者等价")

print("\n== 敏感度对指数机制的影响 ==")
print("  效用 = 票数，删一个人的最大影响 Δu = 1（敏感性由数据结构决定）")
print("  若效用改为『利润』且单笔利润可达 1000 元 → Δu = 1000，噪声放大 1000 倍")
print("  教训：设计 DP 系统时先想清楚『最坏情况下一个人的杠杆有多大』")

print("\n== DP 合成数据 ==")
eps = 1.0
noisy = noisy_histogram(data, categories, eps, rng)
print(f"  ε={eps} 噪声直方图: {[round(noisy[c], 1) for c in categories]}")
synthetic = synthetic_from_histogram(noisy, 100000, rng)
syn_counts = Counter(synthetic)
true_dist = {c: true_counts[c] / len(data) for c in categories}
syn_dist = {c: syn_counts[c] / len(synthetic) for c in categories}
print(f"  {'类别':<8}{'真实分布':>10}{'合成分布':>10}{'绝对误差':>10}")
for c in categories:
    print(f"  {c:<8}{true_dist[c]:>10.1%}{syn_dist[c]:>10.1%}"
          f"{abs(true_dist[c] - syn_dist[c]):>10.2%}")

print("\n== 合成数据的二次分析 ==")
print(f"  直接回答『有多少人选编程』: 真实 210，噪声直方图 ≈ {noisy['编程']:.0f}")
print(f"  合成数据回答（10 万条）: ≈ {syn_counts['编程']}")
print("  合成数据的优势：预算只花一次，之后无限查询且不增加隐私成本")
print("  代价：分布偏差（长尾/稀有类别易失真）—— 高保真合成是大模型时代的课题")

print("\n== 合成数据上的统计一致性 ==")
trials = 20
errs = []
for _ in range(trials):
    noisy = noisy_histogram(data, categories, eps, rng)
    syn = synthetic_from_histogram(noisy, 50000, rng)
    sc = Counter(syn)
    err = max(abs(sc[c] / len(syn) - true_dist[c]) for c in categories)
    errs.append(err)
print(f"  20 次独立实验的最大分布误差: 均值 {sum(errs) / len(errs):.4f}, "
      f"最大 {max(errs):.4f}")
print("  噪声是随机的 → 合成数据的误差也是随机的 —— 每次预算都要重花")

print("\n== 小结 ==")
for line in (
    "  指数机制 = DP 版的 argmax：效用加权 softmax 采样",
    "  敏感度分析先于一切：一个人的最大杠杆决定噪声水平",
    "  DP 合成数据把『按查询计费』变成『一次发布』，工程上极其重要",
    "  合成数据的保真度上限受 ε 制约 —— 隐私换保真，没有免费午餐",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现指数机制的「多 winners 版」（DP top-k），比较与直接发布直方图的开销。
# 2. 把合成数据扩展到二维（类别 × 数值）：类别用指数机制、数值用拉普拉斯。
# 3. 用「 Wohlrab-Warwick 检验」思路评估合成数据的下游模型精度（如朴素贝叶斯）。
# 4. 思考：为什么 DP 合成数据无法完美保留稀有类别？这与 908 课的敏感度
#    分析有什么关系？
