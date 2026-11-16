# ===== 第873课：贝叶斯推断与采样方法-贝叶斯A/B检验与Thompson采样 =====
# 知识点：
#   - A/B 检验的贝叶斯版：两个 Beta 后验，直接问 P(B>A) 与期望损失
#   - 与频率派 t 检验（681 课）的区别：回答「B 更好的概率」而非「拒绝原假设」
#   - Thompson 采样：每轮从各臂后验各抽一个样本，选样本值最大的臂
#   - 探索与利用自动平衡：不确定的臂后验宽 -> 仍有概率被选中
#   - 遗憾值(regret) = 最优臂期望 × 轮数 - 实际累计奖励
# 依赖：无（标准库）
import math
import random


def beta_grid_quantile(a, b, level=0.95, grid=2000):
    xs = [(i + 0.5) / grid for i in range(grid)]
    logw = []
    for x in xs:
        if x <= 0 or x >= 1:
            logw.append(-math.inf)
        else:
            logw.append((a - 1) * math.log(x) + (b - 1) * math.log(1 - x))
    mx = max(logw)
    w = [math.exp(v - mx) for v in logw]
    total = sum(w)
    cum, lo, hi = 0.0, None, None
    tail = (1 - level) / 2
    for x, ww in zip(xs, w):
        cum += ww / total
        if lo is None and cum >= tail:
            lo = x
        if cum >= 1 - tail:
            hi = x
            break
    return lo, hi


def prob_b_beats_a(sa, fa, sb, fb, draws=20000, rng=None):
    """P(θB > θA)：从两个后验各抽样本比较。"""
    wins = 0
    for _ in range(draws):
        if rng.betavariate(sb, fb) > rng.betavariate(sa, fa):
            wins += 1
    return wins / draws


print("== 场景：两个按钮的转化率 ==")
rng = random.Random(4)
pA, pB = 0.10, 0.13
nA = nB = 1000
convA = sum(1 for _ in range(nA) if rng.random() < pA)
convB = sum(1 for _ in range(nB) if rng.random() < pB)
print(f"  真实转化率 A={pA} B={pB}（B 更好）")
print(f"  观测: A {convA}/{nA} = {convA / nA:.3f}   B {convB}/{nB} = {convB / nB:.3f}")

aA, bA = 1 + convA, 1 + nA - convA
aB, bB = 1 + convB, 1 + nB - convB
loA, hiA = beta_grid_quantile(aA, bA)
loB, hiB = beta_grid_quantile(aB, bB)
print(f"  A 后验 Beta({aA},{bA}): 95%区间 [{loA:.3f}, {hiA:.3f}], 均值 {aA / (aA + bA):.3f}")
print(f"  B 后验 Beta({aB},{bB}): 95%区间 [{loB:.3f}, {hiB:.3f}], 均值 {aB / (aB + bB):.3f}")
p_win = prob_b_beats_a(aA, bA, aB, bB, rng=rng)
print(f"  P(B > A) = {p_win:.1%}")
exp_lift = aB / (aB + bB) - aA / (aA + bA)
print(f"  期望提升 = {exp_lift:.3f}（绝对）")
print("  决策口径：P(B>A) 超过阈值(如 95%) 即切换 —— 与 p 值是两种语言")

print("\n== Thompson 采样：多臂老虎机 ==")


def thompson(true_ps, horizon=1000, runs=40, seed=7):
    regret_all, win_all = [], []
    for run in range(runs):
        rng_t = random.Random(seed * 1000 + run)
        a = [1.0] * len(true_ps)
        b = [1.0] * len(true_ps)
        reward = 0.0
        for _ in range(horizon):
            samples = [rng_t.betavariate(a[i], b[i]) for i in range(len(a))]
            arm = max(range(len(a)), key=lambda j: samples[j])
            r = 1.0 if rng_t.random() < true_ps[arm] else 0.0
            a[arm] += r
            b[arm] += 1 - r
            reward += r
        regret = horizon * max(true_ps) - reward
        regret_all.append(regret)
        win_all.append(reward / horizon)
    return regret_all, win_all


arms = [0.08, 0.10, 0.13, 0.09]
regrets, wins = thompson(arms)
best_arm = arms.index(max(arms))
print(f"  4 臂真实转化率 {arms}（最优臂 {best_arm}，p={max(arms)}）")
print(f"  Thompson 1000 轮 × 40 次: 平均累计遗憾 = {sum(regrets) / len(regrets):.1f}")
print(f"  平均选中率整体 = {sum(wins) / len(wins):.3f}（理论上限 {max(arms)}）")

print("\n== 与 ε-greedy 的对比 ==")


def epsilon_greedy(true_ps, horizon=1000, eps=0.1, runs=40, seed=7):
    regret_all = []
    for run in range(runs):
        rng_t = random.Random(seed * 1000 + run)
        K = len(true_ps)
        wins = [0.0] * K
        plays = [0] * K
        reward = 0.0
        for t in range(horizon):
            if rng_t.random() < eps or min(plays) == 0:
                arm = rng_t.randrange(K)
            else:
                arm = max(range(K), key=lambda j: wins[j] / max(plays[j], 1))
            r = 1.0 if rng_t.random() < true_ps[arm] else 0.0
            wins[arm] += r
            plays[arm] += 1
            reward += r
        regret_all.append(horizon * max(true_ps) - reward)
    return regret_all


reg_greedy = epsilon_greedy(arms)
print(f"  ε-greedy(ε=0.1) 平均累计遗憾 = {sum(reg_greedy) / len(reg_greedy):.1f}")
print(f"  Thompson        平均累计遗憾 = {sum(regrets) / len(regrets):.1f}")
print("  Thompson 的探索量随不确定性自动衰减；ε-greedy 永远固定浪费 ε 轮在已知差臂上")

print("\n== 早期停止：期望损失判据 ==")


def expected_loss(aA, bA, aB, bB, rng, draws=5000):
    """选 B 的期望损失 = E[max(θA - θB, 0)]。"""
    loss = 0.0
    for _ in range(draws):
        loss += max(rng.betavariate(aA, bA) - rng.betavariate(aB, bB), 0.0)
    return loss / draws


print(f"  {'A样本':>10}{'B样本':>10}{'P(B>A)':>9}{'选B的期望损失':>14}")
for na, nb in ((100, 100), (300, 300), (1000, 1000), (3000, 3000)):
    rng_s = random.Random(na * 7 + nb)
    ca = sum(1 for _ in range(na) if rng_s.random() < 0.10)
    cb = sum(1 for _ in range(nb) if rng_s.random() < 0.13)
    pa, fa = 1 + ca, 1 + na - ca
    pb, fb = 1 + cb, 1 + nb - cb
    pw = prob_b_beats_a(pa, fa, pb, fb, draws=2000, rng=rng_s)
    el = expected_loss(pa, fa, pb, fb, rng_s)
    print(f"  {na:>10}{nb:>10}{pw:>9.1%}{el:>14.4f}")
print("  样本越少 P(B>A) 越模糊、期望损失越大 —— 贝叶斯方法天然给出『继续等多久』")

print("\n== 小结 ==")
for line in (
    "  贝叶斯 A/B 直接输出决策量：P(B>A)、期望损失、可信区间",
    "  Thompson 采样把『探索-利用』编码进采样：宽后验天然吸引探索",
    "  遗憾值是老虎机算法的统一计分板；Thompson 在实践中几乎总是强基线",
    "  对照 681 课：频率派回答『差异显著吗』，贝叶斯回答『该选谁』",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「A 与 B 互胜概率矩阵」：3 个版本两两算 P(i>j)，输出胜率表。
# 2. 给 Thompson 加最小探索保底：每臂至少 20 次后才允许纯贪心采样，观察
#    小样本期遗憾变化。
# 3. 实现贝叶斯序贯检验：每 100 样本检查一次 P(B>A)，≥99% 即停，统计平均
#    样本量与错误率（真实 B 更差时误停的频率）。
# 4. 思考：为什么 Thompson 采样没有 ε 的超参数？它把探索预算分配给谁的
#    依据是什么？
