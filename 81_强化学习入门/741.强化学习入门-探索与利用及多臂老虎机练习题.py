# ===== 第741课：强化学习入门-探索与利用及多臂老虎机 =====
# 知识点：
#   - 探索/利用困境 explore-exploit：试未知臂 vs 拉当前最优臂
#   - 多臂老虎机 k-armed bandit：无状态，纯「选动作 -> 得奖励」的最小 RL 问题
#   - 后悔 regret：累计「没选到最优臂」的损失，衡量策略好坏
#   - ε-greedy：以 ε 概率随机探索；衰减 ε 可从探索平滑过渡到利用
#   - UCB1：按均值 + 置信半径 sqrt(2ln t / n_i) 选臂，乐观面对不确定
#   - Thompson 采样：对每个臂维护 Beta 后验，按采样值选臂（贝叶斯）
#   - 增量式均值：Q_{n+1} = Q_n + (r - Q_n)/n，无需存全部历史
# 依赖：无（标准库）
import math
import random
import statistics

K = 5
TRUE_MEANS = [0.2, 0.5, 0.8, 0.35, 0.65]     # 3 号臂(0.8)最优
OPTIMAL = max(TRUE_MEANS)


def pull(arm, rng):
    """伯努利奖励：以 TRUE_MEANS[arm] 概率得 1，否则 0。"""
    return 1.0 if rng.random() < TRUE_MEANS[arm] else 0.0


class Bandit:
    def __init__(self, k=K):
        self.k = k
        self.counts = [0] * k
        self.means = [0.0] * k
        self.total = 0
        self.regret = 0.0

    def update(self, arm, reward):
        self.counts[arm] += 1
        n = self.counts[arm]
        self.means[arm] += (reward - self.means[arm]) / n      # 增量均值
        self.total += 1
        self.regret += OPTIMAL - TRUE_MEANS[arm]


def epsilon_greedy(b, rng, eps, decay=1.0, t=0):
    e = eps * (decay ** t)
    if rng.random() < e:
        return rng.randrange(b.k)
    return max(range(b.k), key=lambda a: b.means[a])


def ucb1(b, rng):
    for a in range(b.k):
        if b.counts[a] == 0:
            return a
    return max(range(b.k), key=lambda a:
               b.means[a] + math.sqrt(2 * math.log(b.total + 1) / b.counts[a]))


def thompson(b, rng):
    """Beta(α=成功+1, β=失败+1) 后验采样（用 random.betavariate）。"""
    samples = []
    for a in range(b.k):
        succ = b.means[a] * b.counts[a]
        fail = b.counts[a] - succ
        samples.append(rng.betavariate(succ + 1, fail + 1))
    return max(range(b.k), key=lambda a: samples[a])


def run(strategy, horizon=2000, seed=0, **kw):
    rng = random.Random(seed)
    b = Bandit(K)
    curve = []
    for t in range(horizon):
        if strategy == "greedy":
            arm = max(range(K), key=lambda a: b.means[a]) if t >= K else t
        elif strategy == "eps":
            arm = epsilon_greedy(b, rng, kw["eps"], kw.get("decay", 1.0), t)
        elif strategy == "ucb":
            arm = ucb1(b, rng)
        else:
            arm = thompson(b, rng)
        r = pull(arm, rng)
        b.update(arm, r)
        if (t + 1) % 200 == 0:
            curve.append(round(b.regret, 1))
    return b, curve


print("== 真实臂均值 ==")
print(f"  {TRUE_MEANS}  最优臂=2号, 均值={OPTIMAL}")

print("\n== 各策略 2000 步累计后悔（10 次平均）==")
strategies = [
    ("纯贪心", "greedy", {}),
    ("ε=0.01", "eps", {"eps": 0.01}),
    ("ε=0.1", "eps", {"eps": 0.1}),
    ("ε=0.1 衰减", "eps", {"eps": 0.5, "decay": 0.999}),
    ("UCB1", "ucb", {}),
    ("Thompson", "thompson", {}),
]
for name, st, kw in strategies:
    regrets = [run(st, seed=s, **kw)[0].regret for s in range(10)]
    b0, curve = run(st, seed=0, **kw)
    print(f"  {name:<14}: 平均后悔={statistics.fmean(regrets):>7.1f} "
          f"最优臂被选 {b0.counts[2]/b0.total:.0%}")
    print(f"    后悔曲线(每200步): {curve[:6]}")

print("\n== 探索率 ε 的权衡 ==")
for eps in (0.0, 0.01, 0.05, 0.1, 0.3, 0.5):
    b, _ = run("eps", seed=3, eps=eps)
    print(f"  ε={eps:<5}: 最优臂占比={b.counts[2]/b.total:>5.1%} "
          f"累计后悔={b.regret:>7.1f}")
print("  ε 太小探索不足（锁死次优臂），太大浪费太多试错")

print("\n== UCB 置信半径随时间/次数变化 ==")
for n in (1, 5, 20, 100, 500):
    t = 1000
    bonus = math.sqrt(2 * math.log(t) / n)
    print(f"  臂被拉 {n:>3} 次 -> 置信半径={bonus:.3f}（拉得越少越该再试）")

print("\n== 增量均值验证 ==")
rng = random.Random(1)
xs = [rng.random() for _ in range(100)]
m = 0.0
for n, x in enumerate(xs, 1):
    m += (x - m) / n
print(f"  增量式={m:.6f}  statistics.fmean={statistics.fmean(xs):.6f} "
      f"一致={abs(m-statistics.fmean(xs)) < 1e-12}")

print("\n== 策略对比 ==")
print(f"  {'策略':<14}{'原理':<26}{'超参':<12}{'适用'}")
for row in (("ε-greedy", "固定概率随机探索", "ε", "基线、易实现"),
            ("UCB1", "置信上界，乐观不确定", "无", "确定性、理论保证"),
            ("Thompson", "贝叶斯后验采样", "先验", "效果好、易并行"),
            ("纯贪心", "只选当前最优", "无", "不应使用（会锁死）")):
    print(f"  {row[0]:<14}{row[1]:<26}{row[2]:<12}{row[3]}")

print("\n== 与完整 RL 的关系 ==")
for line in [
    "  老虎机无状态转移；MDP 多了 s' 与延迟奖励",
    "  探索策略可直接用在 Q-learning 的动作选择上（第742课）",
    "  上下文老虎机（contextual bandit）常用于推荐/广告冷启动",
    "  后悔界 O(log T) 是好策略的标志，线性后悔说明没学到",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 ε 随 1/sqrt(t) 衰减，对比固定 ε 的累计后悔。
# 2. 给奖励加高斯噪声（非伯努利），重跑四种策略比较稳健性。
# 3. 实现 Softmax/Boltzmann 探索（按 exp(Q/τ) 概率采样）。
# 4. 思考：为什么纯贪心在初始全 0 估计时会永久锁死在某个坏臂？
