# ===== 第763课：信息论与编码-熵与信息量 =====
# 知识点：
#   - 自信息 I(x) = -log2 P(x)：越不可能的事件信息量越大
#   - 熵 H(X) = -Σ p(x)·log2 p(x)：平均不确定性，单位 bit
#   - 二元熵 H(p) 在 p=0.5 时最大 1 bit，p=0/1 时为 0
#   - 联合熵 H(X,Y)、条件熵 H(Y|X) = H(X,Y) - H(X)
#   - 互信息 I(X;Y) = H(X) + H(Y) - H(X,Y)：知道 X 后 Y 减少多少不确定性
#   - 交叉熵 / KL 散度：衡量两个分布的差异，是机器学习损失的基础
# 依赖：无（标准库）
import math
from collections import Counter


def log2(p):
    return math.log2(p) if p > 0 else 0.0     # 约定 0·log0 = 0


def entropy(probs):
    return -sum(p * log2(p) for p in probs if p > 0)


def entropy_from_samples(samples):
    n = len(samples)
    counts = Counter(samples)
    return entropy([c/n for c in counts.values()]), dict(counts)


def joint_entropy(pairs):
    return entropy_from_samples(pairs)[0]


def conditional_entropy(pairs):
    """H(Y|X) = H(X,Y) - H(X)。"""
    hxy = entropy_from_samples(pairs)[0]
    xs = [x for x, _ in pairs]
    hx = entropy_from_samples(xs)[0]
    return hxy - hx


def mutual_information(pairs):
    """I(X;Y) = H(X) + H(Y) - H(X,Y)。"""
    xs = [x for x,_ in pairs]; ys = [y for _,y in pairs]
    hx, hy = entropy_from_samples(xs)[0], entropy_from_samples(ys)[0]
    hxy = entropy_from_samples(pairs)[0]
    return hx + hy - hxy


def kl_divergence(p, q):
    """KL(p||q) = Σ p·log(p/q)，非对称、非负。"""
    return sum(pi * log2(pi/qi) for pi, qi in zip(p, q) if pi > 0)


def cross_entropy(p, q):
    return -sum(pi * log2(qi) for pi, qi in zip(p, q) if pi > 0)


print("== 自信息 ==")
for p, label in ((1.0,"必然"),(0.5,"抛硬币"),(0.125,"3 个硬币全正"),(1/1024,"千分之一")):
    print(f"  P={p:<10.6f} {label:<14} I={-log2(p):>8.3f} bit")

print("\n== 二元熵函数 H(p) ==")
print(f"  {'p':<8}{'H(p)':<10}")
for p in (0.0, 0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 1.0):
    h = entropy([p, 1-p])
    print(f"  {p:<8.2f}{h:<10.4f}")
print("  p=0.5 最大 1 bit；分布越偏斜熵越小 -> 越可预测")

print("\n== 从样本估计熵 ==")
for name, data in (("全相同", "AAAAAAAAAA"),
                   ("均匀分布", "ABCDABCDAB"),
                   ("偏斜", "AAAAAAAABC"),
                   ("中文文本", "信息论信息论熵")):
    h, counts = entropy_from_samples(data)
    print(f"  {name:<10}: 熵={h:.3f} bit/符号, 分布={dict(sorted(counts.items()))}")

print("\n== 联合/条件熵与互信息 ==")
# 构造 X,Y 相关的联合样本
pairs = [("晴","出门"),("晴","出门"),("晴","在家"),
         ("雨","在家"),("雨","在家"),("雨","在家")]
print("  样本:", pairs)
print(f"  H(X)   = {entropy_from_samples([x for x,_ in pairs])[0]:.3f} bit")
print(f"  H(Y)   = {entropy_from_samples([y for _,y in pairs])[0]:.3f} bit")
print(f"  H(X,Y) = {joint_entropy(pairs):.3f} bit")
print(f"  H(Y|X) = {conditional_entropy(pairs):.3f} bit（知道天气后还剩多少不确定）")
print(f"  I(X;Y) = {mutual_information(pairs):.3f} bit")

print("\n== 独立变量互信息应≈0 ==")
indep = [(x,y) for x in "01" for y in "01"] * 10
print(f"  I(X;Y) = {mutual_information(indep):.6f} bit")

print("\n== 交叉熵与 KL 散度 ==")
p = [0.5, 0.25, 0.25]
for name, q in (("真实分布", [0.5,0.25,0.25]), ("近似", [0.4,0.3,0.3]),
                ("错误", [0.1,0.1,0.8])):
    ce, kl = cross_entropy(p,q), kl_divergence(p,q)
    print(f"  q={q}: H(p,q)={ce:.4f}  KL(p||q)={kl:.4f}")
print(f"  H(p) = {entropy(p):.4f}，交叉熵 = H(p) + KL >= H(p)")
print("  KL 非对称:", round(kl_divergence([0.9,0.1],[0.5,0.5]),3),
      "vs", round(kl_divergence([0.5,0.5],[0.9,0.1]),3))

print("\n== 熵的上界 ==")
for n in (2, 4, 8, 26, 256):
    h = entropy([1/n]*n)
    print(f"  {n:>3} 个等概率符号: H=log2({n})={h:.3f} bit")
print("  均匀分布熵最大；任何分布 H <= log2|X|")

print("\n== 英文文本信息率（示意）==")
text = "this is a simple example of information theory"
h, _ = entropy_from_samples(text)
print(f"  字符级熵≈{h:.2f} bit/字符（理论英文约 4.0~4.7，因未建模上下文而偏高）")
print("  考虑 n-gram / 语言模型后估计会更低 -> 可压缩空间更大")

print("\n== 应用 ==")
for line in [
    "  压缩：熵是无损压缩的理论下界（第764课 Huffman）",
    "  通信：信道容量 = 最大互信息（第770课）",
    "  ML：交叉熵损失、决策树用信息增益（= 互信息）选特征",
    "  安全：口令熵衡量暴力破解难度（第699课）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 计算决策树里「信息增益 = H(Y) - H(Y|X)」并在示例数据上验证。
# 2. 证明/验证 KL(p||q) >= 0 且仅 p=q 时取等。
# 3. 用 2-gram 模型重估英文文本熵，对比字符级估计。
# 4. 思考：为什么「0·log0 = 0」这个约定在熵定义里是必要的？
