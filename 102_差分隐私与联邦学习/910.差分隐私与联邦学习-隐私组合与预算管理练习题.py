# ===== 第910课：差分隐私与联邦学习-隐私组合与预算管理 =====
# 知识点：
#   - 顺序组合：同一数据上跑 k 个 ε-DP 机制 → 总保证 (Σε)-DP
#   - 并行组合：数据不相交的分区上各用 ε → 总保证仍是 ε
#   - 隐私预算账本（ledger）：把 ε 当钱花，花光为止
#   - 高级组合：(Σε·coth 之类的更紧界) 与 RDP，教学版用顺序/并行即可
#   - DP-SGD 思想：每个样本截断贡献 + 加噪 → 隐私预算随训练轮数累积
# 依赖：无（标准库）
import math
import random


class BudgetLedger:
    """隐私预算账本。"""

    def __init__(self, total_epsilon):
        self.total = total_epsilon
        self.spent = []

    def charge(self, label, epsilon):
        if epsilon > self.remaining():
            raise ValueError(f"预算不足：剩余 {self.remaining():.3f}，请求 {epsilon:.3f}")
        self.spent.append((label, epsilon))
        return True

    def remaining(self):
        return self.total - sum(e for _, e in self.spent)

    def report(self):
        print(f"    {'查询':<24}{'ε':>8}")
        for label, e in self.spent:
            print(f"    {label:<24}{e:>8.3f}")
        print(f"    {'合计':<24}{sum(e for _, e in self.spent):>8.3f}"
              f" / {self.total:.3f}")


def laplace_noise(scale, rng):
    u = rng.uniform(-0.5, 0.5)
    return -math.copysign(1.0, u) * scale * math.log(1 - 2 * abs(u) + 1e-18)


def dp_mean_clipped(values, lo, hi, epsilon, rng):
    """DP 均值：截断到 [lo,hi] 后求和噪声/计数噪声。"""
    clipped = [min(hi, max(lo, v)) for v in values]
    sum_sens = hi - lo                     # 截断后单样本最大贡献
    count_sens = 1.0
    sum_noisy = sum(clipped) + laplace_noise(sum_sens / (epsilon / 2), rng)
    count_noisy = len(clipped) + laplace_noise(count_sens / (epsilon / 2), rng)
    return sum_noisy / max(count_noisy, 1.0)


rng = random.Random(103)

print("== 顺序组合：预算会被累加 ==")
print("  同一数据集上先发直方图(ε1)再算均值(ε2) → 总保证 (ε1+ε2)-DP")
print("  串行 = 加法；这就是『预算』概念的数学来源")

print("\n== 并行组合：分区数据互不相交 ==")
regions = {"华东": ["华东"] * 120, "华南": ["华南"] * 80, "华北": ["华北"] * 60}
eps_each = 0.5
print("  每个地区的直方图各用 ε=0.5，但数据互不相交")
print("  → 任何人只属于一个分区 → 整体仍是 ε=0.5-DP")
print("  工程含义：按用户分桶发布，不增加总预算")

print("\n== 预算账本实战 ==")
ledger = BudgetLedger(total_epsilon=2.0)
salaries = [random.Random(1).gauss(8000, 2000) for _ in range(500)]
salaries = [max(2000, min(20000, s)) for s in salaries]
try:
    print("  查询 1: DP 均值工资 (ε=0.5)")
    ledger.charge("DP 均值工资", 0.5)
    m1 = dp_mean_clipped(salaries, 2000, 20000, 0.5, rng)
    print(f"    结果 ≈ {m1:.0f} 元（真实 {sum(salaries) / len(salaries):.0f}）")
    print("  查询 2: DP 最高工资所在区间 (ε=0.8)")
    ledger.charge("DP 最高区间", 0.8)
    print("    结果: [10000, 15000] 区间")
    print("  查询 3: DP 均值再来一次 (ε=0.5)")
    ledger.charge("DP 均值第 2 次", 0.5)
    m2 = dp_mean_clipped(salaries, 2000, 20000, 0.5, rng)
    print(f"    结果 ≈ {m2:.0f} 元")
    print("  查询 4: 还想再查一次 (ε=0.5)")
    ledger.charge("DP 均值第 3 次", 0.5)
except ValueError as exc:
    print(f"    -> {exc}")
ledger.report()
print("  预算用尽 = 数据不可再查询 —— 这是制度化的隐私保护")

print("\n== 重复查询的方差代价 ==")
print(f"  {'查询次数':>8}{'单次ε':>10}{'估计标准差':>12}")
values = [5000.0] * 1000                          # 常数数据，均值应为 5000
for k in (1, 4, 16):
    per_eps = 1.0 / k                             # 固定总预算 1.0 平摊
    ests = [dp_mean_clipped(values, 0, 10000, per_eps, rng) for _ in range(50)]
    m = sum(ests) / len(ests)
    sd = math.sqrt(sum((e - 5000) ** 2 for e in ests) / len(ests))
    print(f"  {k:>8}{per_eps:>10.3f}{sd:>12.1f}")
print("  总预算固定时：查询越多 → 单次 ε 越小 → 每个估计越抖")
print("  真实均值 5000：预算不变则精度必须让步 —— 没有免费午餐")

print("\n== DP-SGD 思想：训练也是查询 ==")


def dp_sgd_demo(rounds=12, epsilon_per_round=0.2, rng=None):
    """简化版：每轮发布『梯度均值』，先截断(C=4)再加噪，预算累加。"""
    w = 0.0                                        # 一维线性回归 w
    lr = 0.1
    true_w = 3.0
    clip_c = 4.0
    data = []
    for _ in range(200):
        x = rng.gauss(0, 1)
        data.append((x, true_w * x + rng.gauss(0, 0.5)))
    for r in range(rounds):
        grads = []
        for x, y in data:
            pred = w * x
            grads.append((pred - y) * x)           # 每个样本的梯度
        clipped = [max(-clip_c, min(clip_c, g)) for g in grads]
        # 均值的敏感度 = C/n；噪声 scale = (C/n)/ε
        noisy_grad = sum(clipped) / len(clipped) + \
            laplace_noise(clip_c / (epsilon_per_round * len(clipped)), rng)
        w -= lr * noisy_grad
        loss = sum((w * x - y) ** 2 for x, y in data) / len(data)
        print(f"    轮 {r + 1:>2}: w ≈ {w:.3f}  (目标 {true_w})  MSE = {loss:.3f}"
              f"  累计 ε = {epsilon_per_round * (r + 1):.2f}")
    return w


print("  DP-SGD：每轮截断梯度(C=4) + 加噪，预算随轮数线性累加")
final_w = dp_sgd_demo(rounds=5, epsilon_per_round=0.2, rng=rng)
print(f"  最终 w = {final_w:.3f}（带噪训练依然朝真值收敛，代价是精度与速度）")

print("\n== 组合规则的工程含义 ==")
for line in (
    "  给数据产品设计 API：每个端点声明它消耗多少 ε",
    "  用户级预算：每个用户的查询在自己的数据子域上（并行组合省预算）",
    "  训练级预算：轮数 × 每轮 ε = 总预算（DP-SGD 的账本）",
    "  高级组合/RDP/矩会计能给出更紧的界 —— 工业库（Opacus）的核心",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  隐私预算把『隐私』变成可记账、可审计的稀缺资源",
    "  顺序组合加法、并行组合免加 —— 设计查询拓扑能省一半预算",
    "  DP-SGD = 截断 + 噪声 + 预算记账，是差分隐私进入 ML 的主通道",
    "  911 课：联邦学习 —— 不上传原始数据的另一条隐私路线",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「稀疏向量技术」（SVT）：超过阈值的查询才消耗预算，统计可回答的
#    查询数上限。
# 2. 实现高斯机制替代拉普拉斯：(ε,δ)-DP，对比同 ε 下的噪声大小。
# 3. 设计「预算分层」：给不同用户组分配不同 ε，验证并行组合的正确性。
# 4. 思考：为什么预算必须跨查询持久化？「重启计数器」会泄露什么？
