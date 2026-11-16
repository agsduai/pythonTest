# ===== 第908课：差分隐私与联邦学习-差分隐私定义与拉普拉斯机制 =====
# 知识点：
#   - 差分隐私（DP）：改变任何一个人的数据，输出分布几乎不变
#   - ε-DP：对相邻数据集 D, D'，所有输出子集 S 满足 P(M(D)∈S) ≤ e^ε·P(M(D')∈S)
#   - 全局敏感度 Δf：删/加一个人最多能改变查询结果多少
#   - 拉普拉斯机制：真值 + Laplace(Δf/ε) 噪声 -> 严格 ε-DP
#   - 噪声与隐私的杠杆：ε 越小越隐私、噪声越大；这是数学保证而非工程 tricks
# 依赖：无（标准库）
import math
import random
from collections import Counter


def laplace_noise(scale, rng):
    """逆变换法采样 Laplace(scale)：u∈(-0.5,0.5) -> -sign·b·ln(1-2|u|)。"""
    u = rng.uniform(-0.5, 0.5)
    return -math.copysign(1.0, u) * scale * math.log(1 - 2 * abs(u) + 1e-18)


def dp_histogram(data, categories, epsilon, rng):
    """直方图发布：每桶计数 + Laplace(1/ε) 噪声（敏感度=1）。"""
    counts = Counter(d for d in data if d in categories)
    scale = 1.0 / epsilon
    noisy = {}
    for c in categories:
        noisy[c] = counts.get(c, 0) + laplace_noise(scale, rng)
    return noisy


def clip_nonnegative(noisy):
    return {k: max(0.0, v) for k, v in noisy.items()}


rng = random.Random(101)

print("== 差分隐私定义 ==")
print("  相邻数据集：只差一个人的两个数据集 D 与 D'")
print("  要求：对所有输出 S，P[M(D)∈S] ≤ e^ε · P[M(D')∈S]")
print("  ε 越小 → 两个分布越像 → 个人隐私越强；ε 通常取 0.1~10")

print("\n== 敏感度：查询的『杠杆』==")


def sensitivity_demo(values):
    """计数查询敏感度 = 1；求和查询敏感度 = 最大单值。"""
    counts = len(values)
    max_val = max(values)
    return 1, max_val


salaries = [3000, 5000, 8000, 12000, 20000]
d1, d2 = sensitivity_demo(salaries)
print(f"  数据: {salaries}")
print(f"  『有多少人』查询: 敏感度 = {d1}（加/删一人恰变化 1）")
print(f"  『工资总和』查询: 敏感度 = {d2}（删掉最高工资的人）")
print("  敏感度大 → 需要的噪声大 → 无界求和必须先截断（clip）")

print("\n== DP 直方图发布 ==")
data = ["感冒"] * 120 + ["流感"] * 80 + ["肺炎"] * 45 + ["骨折"] * 30
categories = ["感冒", "流感", "肺炎", "骨折"]
true_counts = Counter(data)
print(f"  真实计数: {dict(true_counts)}")
for eps in (2.0, 0.5, 0.1):
    noisy = dp_histogram(data, categories, eps, rng)
    err = sum(abs(noisy[c] - true_counts[c]) for c in categories)
    print(f"  ε={eps:>4}: 噪声后 {[round(noisy[c]) for c in categories]}  绝对误差 {err:.1f}")
print("  ε 小 → 噪声大 → 误差大 —— 隐私-效用杠杆的定量展示")

print("\n== 拉普拉斯分布的形状 ==")
print(f"  {'分位数':>10}{'scale=1/ε(ε=0.5)':>20}")
lap = sorted(laplace_noise(2.0, rng) for _ in range(5000))
for q in (0.1, 0.25, 0.5, 0.75, 0.9):
    v = lap[int(q * 4999)]
    print(f"  {q:>10.2f}{v:>20.2f}")
print("  重尾：1% 的输出可能偏差 ±10 —— 隐私来自这些『大偏移』")

print("\n== 用实验验证 DP 保证（经验比值）==")
print("  相邻数据集：包含某人的感冒 121 例 vs 不含的 120 例")
print(f"  {'输出区间':<20}{'P[D]':>10}{'P[D既]':>10}{'比值':>10}{'e^0.5 上限':>12}")


def hist_count_fixed(data, rng, eps):
    """固定 category 的 DP 计数。"""
    return sum(1 for d in data if d == "感冒") + laplace_noise(1 / eps, rng)


base = ["感冒"] * 120 + ["流感"] * 80
neighbor = ["感冒"] * 121 + ["流感"] * 80
eps = 0.5
trials = 4000
bins = [(140, 150), (150, 160), (160, 170)]
for lo, hi in bins:
    c1 = sum(1 for _ in range(trials) if lo <= hist_count_fixed(base, rng, eps) < hi)
    c2 = sum(1 for _ in range(trials) if lo <= hist_count_fixed(neighbor, rng, eps) < hi)
    ratio = (c2 + 1) / (c1 + 1)
    print(f"  [{lo},{hi}){'':<12}{c1 / trials:>10.3f}{c2 / trials:>10.3f}"
          f"{ratio:>10.2f}{math.exp(eps):>12.2f}")
print("  经验比值 ≤ e^ε（个别波动来自有限采样）—— 这就是 ε-DP 的直观含义")
print("  攻击者无法从输出分布反推『某人是否在数据集里』")

print("\n== 高维直方图 + 后处理 ==")
noisy = dp_histogram(data, categories, 0.5, rng)
cleaned = clip_nonnegative(noisy)
total_true = len(data)
scale = total_true / sum(cleaned.values())
print(f"  原始噪声输出: {[round(noisy[c], 1) for c in categories]}")
print(f"  截断负值并按总人数归一: {[round(cleaned[c] * scale) for c in categories]}")
print("  关键定理：对 DP 输出做任何后处理仍然是 DP（后处理不变性）")

print("\n== 汇总查询链（预习 910 课的预算）==")
print("  每个查询消耗 ε；同一数据上 k 个查询的总预算 = Σε（顺序组合）")
print("  预算有限 → 每个查询的 ε 变小 → 噪声变大 → 查询要省着用")

print("\n== 小结 ==")
for line in (
    "  DP 的定义是对『输出分布』的约束，与具体攻击无关 —— 数学化隐私",
    "  拉普拉斯机制 = 真值 + Laplace(敏感度/ε)，一行实现强保证",
    "  敏感度是杠杆：截断/投影把大敏感度查询化成小敏感度",
    "  后处理不变性让工程加工自由发挥而不破坏保证",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「DP 均值」：先截断到 [lo,hi]（敏感度=(hi-lo)/n），再加噪声。
# 2. 实现「报告噪声最大值」（Report Noisy Max）：DP 地选最高分类别，避免
#    发布整个直方图。
# 3. 用指数机制（909 课预告）重做最优类别选择，对比方差。
# 4. 思考：为什么「加固定噪声」或「随机删 1% 数据」不是 DP？它们与 DP 的
#    本质区别是什么？
