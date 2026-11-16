# ===== 第871课：贝叶斯推断与采样方法-变分推断与Laplace近似 =====
# 知识点：
#   - MCMC 精确但慢；变分推断(VI)快但近似 —— 用优化代替采样
#   - 思路：在简单分布族（如高斯）里找 KL(q‖p) 最小的 q
#   - Laplace 近似：在众数处用二阶泰勒展开 -> N(mode, 1/f''(mode))
#   - 黑盒 VI：重参数化 x = m + s·z，蒙特卡洛梯度下降优化 (m, log s)
#   - ELBO = E_q[log p] + 熵； maximizing ELBO 等价于最小 KL
# 依赖：无（标准库）
import math
import random


def grid_stats(logp, lo, hi, n=4000):
    """网格求众数/均值/方差（作为真值参照）。"""
    xs = [lo + (hi - lo) * i / (n - 1) for i in range(n)]
    vals = [logp(x) for x in xs]
    mx = max(vals)
    weights = [math.exp(v - mx) for v in vals]
    total = sum(weights)
    mean = sum(x * w for x, w in zip(xs, weights)) / total
    var = sum((x - mean) ** 2 * w for x, w in zip(xs, weights)) / total
    mode = xs[vals.index(mx)]
    return mode, mean, var


print("== Laplace 近似 ==")
# 目标：Beta(2,5) 的核：(1-x)·x^4, x∈(0,1)


def log_beta25(x):
    if x <= 0 or x >= 1:
        return -math.inf
    return math.log(1 - x) + 4 * math.log(x)


mode, mean_true, var_true = grid_stats(log_beta25, 1e-4, 1 - 1e-4)
print(f"  目标 Beta(2,5): 网格众数 = {mode:.4f}, 真实均值 = {mean_true:.4f}, 方差 = {var_true:.4f}")
print(f"  解析众数 (a-1)/(a+b-2) = {1 / 5:.4f}")
f2 = -1 / (mode ** 2) - 4 / ((1 - mode) ** 2)     # log 密度二阶导（解析）
print(f"  log 密度二阶导 f'' = {f2:.1f} -> Laplace 方差 ≈ {1 / -f2:.4f}")
print(f"  Laplace 近似: N(mode, {-1 / f2:.4f}) -> 均值 {mode:.4f}, 标准差 {math.sqrt(1 / -f2):.4f}")
print(f"  真实标准差 = {math.sqrt(var_true):.4f}")
print("  偏态分布在众数处的曲率比真实分布更尖 -> Laplace 会低估方差")

print("\n== 黑盒变分推断：拟合 N(m, s²) 到 p(x) ∝ exp(-x⁴/4) ==")


def logp_quartic(x):
    return -x ** 4 / 4


mode_q, mean_q, var_q = grid_stats(logp_quartic, -4, 4)
print(f"  目标（四次势阱）: 众数 {mode_q:.3f}, 均值 {mean_q:.3f}, 标准差 {math.sqrt(var_q):.3f}")

rng = random.Random(2)
m, logs = 0.0, 0.5                     # 初始 q = N(0, e^0.5²)
lr = 0.02
batch = 16
elbo_hist = []
for step in range(4000):
    gm = gs = 0.0
    elbo = 0.0
    s = math.exp(max(-2.0, min(2.0, logs)))
    for _ in range(batch):
        z = rng.gauss(0, 1)
        x = m + s * z
        g = -x ** 3                       # d logp / dx
        gm += g
        gs += g * z * s                   # 重参数化梯度
        elbo += logp_quartic(x)
    gm /= batch
    gs /= batch
    elbo = elbo / batch + math.log(s)     # ELBO = E[logp] + log s（1维熵）
    elbo_hist.append(elbo)
    m += lr * gm
    logs += 0.01 * (gs + 1.0)             # dELBO/dlog s = E[g·z·s] + 1
    logs = max(-2.0, min(2.0, logs))
s_fit = math.exp(logs)
true_sd = math.sqrt(var_q)
print(f"  VI 拟合结果: q = N(m={m:.3f}, s={s_fit:.3f})")
print(f"  目标标准差 = {true_sd:.3f} -> 单高斯逼近非高斯形状，尽力而为")
if s_fit < true_sd:
    print("  s 偏小：reverse KL(q‖p) 让 q 躲进高概率区，方差倾向被低估")
else:
    print("  s 与目标标准差接近；可加长训练或减小学习率再验证")
print(f"  ELBO 从 {elbo_hist[0]:.3f} 变到 {elbo_hist[-1]:.3f}（整体上升 = 优化在起作用）")

print("\n== 拟合形状对比（密度剖面）==")
peak_true = math.exp(logp_quartic(0.0))
for x in (-2.0, -1.0, 0.0, 1.0, 2.0):
    pt = math.exp(logp_quartic(x)) / peak_true
    pq = math.exp(-x ** 2 / (2 * s_fit ** 2))
    print(f"  x={x:>5}: 目标 {pt:.3f}   q {pq:.3f}")
print("  四次势阱的密度比高斯更『平顶』：q 在肩部偏低、远端偏高（高斯尾部指数衰减慢于四次幂）")

print("\n== VI vs MCMC 对比 ==")
for line in (
    "  VI = 优化问题（快、可扩展、有偏）；MCMC = 采样问题（慢、无偏、难诊断）",
    "  KL(q‖p) 让 VI 倾向『覆盖 p 的高概率区』而避开低概率区 -> 方差低估",
    "  大规模场景（如神经网络）几乎都用 VI/SVI；科研精算用 MCMC",
    "  Laplace 是 VI 的特例：在众数处一步到位，无需迭代",
):
    print("  -", line)

print("\n== 实用建议 ==")
for line in (
    "  先 Laplace 看一眼数量级，再决定上 VI 还是 MCMC",
    "  VI 的结果强烈依赖分布族选择；尝试两个族对比（高斯/均匀）是低成本保险",
    "  ELBO 收敛 ≠ 后验准确：务必做后验预测检查（874 课）",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Laplace 近似的通用版：数值求众数 + 有限差分求 f''，对 Beta(5,2) 应用。
# 2. 把黑盒 VI 的目标换成偏态的 Beta(2,5)，比较单高斯 q 的误差方向。
# 3. 实现「分位数化 VI」：q 为 20 个格点上的可学习离散分布（softmax 参数化），
#    观察它能否表达双峰。
# 4. 思考：为什么 KL(q‖p) 优化会「避开低概率区」而 KL(p‖q)（期望传播）不会？
