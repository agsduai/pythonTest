# ===== 第874课：贝叶斯推断与采样方法-综合案例-贝叶斯估计引擎 =====
# 知识点：
#   - 综合本章：共轭解析(867) + 网格(868) + MCMC(869) + 后验预测检查(PPC)
#   - 引擎 = 模型注册表：bernoulli / poisson / normal 三种模型统一接口
#   - 统一输出：后验参数、均值、可信区间、预测分布、后验预测 p 值
#   - PPC：从后验预测生成模拟数据，比较统计量 —— 检查模型是否「像」数据
#   - 贝叶斯工作流：建模 -> 拟合 -> 诊断 -> 预测检查 -> 再建模
# 依赖：无（标准库）
import math
import random


def grid_ci(weights, xs, level=0.95):
    total = sum(weights)
    cum, lo, hi = 0.0, None, None
    tail = (1 - level) / 2
    for x, w in zip(xs, weights):
        cum += w / total
        if lo is None and cum >= tail:
            lo = x
        if cum >= 1 - tail:
            hi = x
            break
    return lo, hi


class BayesEngine:
    """统一接口的迷你贝叶斯估计引擎。"""

    def __init__(self, rng):
        self.rng = rng
        self.reports = []

    # ---- 模型 1：伯努利（Beta-Bernoulli 共轭解析）----
    def fit_bernoulli(self, data, prior=(1.0, 1.0)):
        a = prior[0] + sum(data)
        b = prior[1] + len(data) - sum(data)
        xs = [i / 1000 for i in range(1, 1000)]
        logw = [((a - 1) * math.log(x) + (b - 1) * math.log(1 - x)) for x in xs]
        mx = max(logw)
        w = [math.exp(v - mx) for v in logw]
        mean = a / (a + b)
        lo, hi = grid_ci(w, xs)
        predictive = lambda n=1: 1.0 if self.rng.random() < mean else 0.0
        return {"name": "bernoulli", "posterior": f"Beta({a:g},{b:g})",
                "mean": mean, "ci": (lo, hi), "param": (a, b),
                "predictive": predictive}

    # ---- 模型 2：泊松（Gamma-Poisson 共轭解析）----
    def fit_poisson(self, data, prior=(1.0, 1.0)):
        alpha = prior[0] + sum(data)
        rate = prior[1] + len(data)
        xs = [i / 20 for i in range(1, 600)]
        logw = [(alpha - 1) * math.log(x) - rate * x for x in xs]
        mx = max(logw)
        w = [math.exp(v - mx) for v in logw]
        mean = alpha / rate
        lo, hi = grid_ci(w, xs)
        predictive = lambda n=1: poisson_sample(mean, self.rng)
        return {"name": "poisson", "posterior": f"Gamma({alpha:g},{rate:g})",
                "mean": mean, "ci": (lo, hi), "param": (alpha, rate),
                "predictive": predictive}

    # ---- 模型 3：已知方差的正态均值（Normal-Normal 共轭）----
    def fit_normal(self, data, sigma=10.0, prior=(20.0, 50.0)):
        n = len(data)
        prec0 = 1 / prior[1] ** 2
        prec = prec0 + n / sigma ** 2
        mean = (prior[0] * prec0 + sum(data) / sigma ** 2) / prec
        sd = 1 / math.sqrt(prec)
        lo, hi = mean - 1.96 * sd, mean + 1.96 * sd
        predictive = lambda n=1: self.rng.gauss(mean, sd)
        return {"name": "normal", "posterior": f"N({mean:.2f},{sd:.3f}²)",
                "mean": mean, "ci": (lo, hi), "param": (mean, sd),
                "predictive": predictive}

    # ---- 后验预测检查（PPC）----
    def posterior_predictive_check(self, fit, data, stat_fn, sims=500):
        observed = stat_fn(data)
        sim_stats = []
        for _ in range(sims):
            sim = [fit["predictive"]() for _ in range(len(data))]
            sim_stats.append(stat_fn(sim))
        sim_stats.sort()
        below = sum(1 for s in sim_stats if s <= observed) / sims
        return observed, below, sim_stats[len(sim_stats) // 2]

    def report(self, title, fit, data, stat_fns):
        lo, hi = fit["ci"]
        print(f"  [{title}]")
        print(f"    数据 n={len(data)}，后验 = {fit['posterior']}")
        print(f"    后验均值 = {fit['mean']:.4f}   95%可信区间 = [{lo:.4f}, {hi:.4f}]")
        for stat_name, fn in stat_fns:
            observed, pval, median_sim = self.posterior_predictive_check(fit, data, fn)
            flag = "OK" if 0.05 < pval < 0.95 else "可疑"
            print(f"    PPC[{stat_name}]: 观测 {observed:.3f} | 模拟中位 {median_sim:.3f} "
                  f"| 后验预测p值 {pval:.3f} [{flag}]")


def poisson_sample(lam, rng):
    """Knuth 法泊松采样。"""
    L = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


print("== 引擎初始化 ==")
rng = random.Random(9)
engine = BayesEngine(rng)

print("\n== 数据生成（真值已知）==")
conv_data = [1 if rng.random() < 0.12 else 0 for _ in range(200)]
call_data = [poisson_sample(4.0, rng) for _ in range(30)]
score_data = [rng.gauss(72, 10) for _ in range(50)]
print(f"  bernoulli: n=200（真实 p=0.12）")
print(f"  poisson:   n=30（真实 λ=4.0）观测均值 = {sum(call_data) / len(call_data):.2f}")
print(f"  normal:    n=50（真实 μ=72）观测均值 = {sum(score_data) / len(score_data):.2f}")

print("\n== 模型 1：伯努利 ==")
fit1 = engine.fit_bernoulli(conv_data)
engine.report("转化率估计", fit1, conv_data,
              [("均值", lambda d: sum(d) / len(d))])

print("\n== 模型 2：泊松 ==")
fit2 = engine.fit_poisson(call_data, prior=(2.0, 1.0))
engine.report("来电率估计", fit2, call_data,
              [("均值", lambda d: sum(d) / len(d)),
               ("方差", lambda d: sum((x - sum(d) / len(d)) ** 2 for x in d) / len(d))])

print("\n== 模型 3：正态 ==")
fit3 = engine.fit_normal(score_data, sigma=10.0, prior=(60.0, 20.0))
engine.report("平均分估计", fit3, score_data,
              [("均值", lambda d: sum(d) / len(d)),
               ("标准差", lambda d: math.sqrt(sum((x - sum(d) / len(d)) ** 2 for x in d) / len(d)))])

print("\n== PPC 怎么读 ==")
for line in (
    "  后验预测 p 值 ≈ 0.5：观测统计量落在模拟分布中间 -> 模型拟合良好",
    "  p 值接近 0 或 1：数据比模型能生成的更极端 -> 模型有系统性偏差",
    "  泊松模型常在『方差』统计量上失败（真实数据过散）-> 提示换负二项模型",
    "  PPC 是贝叶斯的『残差图』：不完美也要知道差在哪",
):
    print("  -", line)

print("\n== 预测示例 ==")
n_new = 100
pred_conv = sum(fit1["predictive"]() for _ in range(n_new))
pred_calls = [fit2["predictive"]() for _ in range(n_new)]
pred_score = [fit3["predictive"]() for _ in range(n_new)]
print(f"  未来 100 用户的模拟转化数 = {pred_conv}（期望 ≈ {fit1['mean'] * 100:.1f}）")
print(f"  未来 100 天来电均值 = {sum(pred_calls) / n_new:.2f}（期望 ≈ {fit2['mean']:.2f}）")
print(f"  未来 100 人得分均值 = {sum(pred_score) / n_new:.2f}（期望 ≈ {fit3['mean']:.2f}）")

print("\n== 小结 ==")
for line in (
    "  引擎 = 统一接口 + 模型注册：新增模型只需实现 fit 与 predictive",
    "  共轭模型解析精确，非共轭模型可换成网格/MCMC 后端（接口不变）",
    "  PPC 把『拟合好坏』变成可检验的量，是贝叶斯工作流的核心诊断",
    "  决策要基于预测分布而非点估计 —— 这是贝叶斯方法的独特收益",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给引擎增加 binomial 模型（n 次试验 k 成功，Gamma-Poisson 类似地解析），
#    用 PPC 验证。
# 2. 实现 PPC 的「多重统计量版」：同时检查均值/方差/最大值，输出 3 个 p 值。
# 3. 把 fit_poisson 的后端换成第 869 课的 MCMC（log 后验），对比区间宽度。
# 4. 思考：为什么后验预测 p 值不应该像经典 p 值那样以 0.05 硬判？双重使用
#    数据的风险在哪里？
