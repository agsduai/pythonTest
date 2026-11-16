# ===== 第889课：概率图模型与结构化推断-推断方法全家桶对照 =====
# 知识点：
#   - 同一个后验查询有多种解法：精确枚举 / 变量消元 / 拒绝采样 /
#     似然加权 / 吉布斯 —— 精度、成本、适用面各不相同
#   - 拒绝采样：前向采样后丢弃与证据不符的样本 —— 证据概率低时极浪费
#   - 似然加权：固定证据变量，仅采样非证据变量，用似然作权重
#   - 自重要性采样视角：多次独立估计的方差是核心指标
#   - 本课在同一网络上把五种方法跑在一起，对照均值与方差
# 依赖：无（标准库）
import math
import random
from itertools import product as iproduct


def build_sprinkler():
    parents = {"Cloudy": [], "Sprinkler": ["Cloudy"], "Rain": ["Cloudy"],
               "Wet": ["Sprinkler", "Rain"], "Slippery": ["Wet"]}
    cpt = {
        "Cloudy": {(): {"T": 0.5, "F": 0.5}},
        "Sprinkler": {("T",): {"T": 0.1, "F": 0.9}, ("F",): {"T": 0.5, "F": 0.5}},
        "Rain": {("T",): {"T": 0.8, "F": 0.2}, ("F",): {"T": 0.2, "F": 0.8}},
        "Wet": {("T", "T"): {"T": 0.99, "F": 0.01}, ("T", "F"): {"T": 0.9, "F": 0.1},
                ("F", "T"): {"T": 0.8, "F": 0.2}, ("F", "F"): {"T": 0.0, "F": 1.0}},
        "Slippery": {("T",): {"T": 0.7, "F": 0.3}, ("F",): {"T": 0.0, "F": 1.0}},
    }
    return {"parents": parents, "cpt": cpt}


def forward_sample(net, rng):
    a = {}
    for v in net["parents"]:
        p = net["cpt"][v][tuple(a[p] for p in net["parents"][v])]["T"]
        a[v] = "T" if rng.random() < p else "F"
    return a


def exact_posterior(net, query, evidence):
    nodes = list(net["parents"])
    dist = {"T": 0.0, "F": 0.0}
    for combo in iproduct(("T", "F"), repeat=len(nodes)):
        a = dict(zip(nodes, combo))
        if any(a[e] != v for e, v in evidence.items()):
            continue
        p = 1.0
        for v in nodes:
            p *= net["cpt"][v][tuple(a[pp] for pp in net["parents"][v])][a[v]]
        dist[a[query]] += p
    total = dist["T"] + dist["F"]
    return {k: v / total for k, v in dist.items()}


def rejection_sampling(net, query, evidence, n, rng):
    hits = {"T": 0, "F": 0}
    tried = 0
    while sum(hits.values()) < n:
        tried += 1
        a = forward_sample(net, rng)
        if any(a[e] != v for e, v in evidence.items()):
            continue
        hits[a[query]] += 1
    total = hits["T"] + hits["F"]
    return hits["T"] / total, tried


def likelihood_weighting(net, query, evidence, n, rng):
    num = {"T": 0.0, "F": 0.0}
    den = 0.0
    for _ in range(n):
        a = dict(evidence)
        w = 1.0
        for v in net["parents"]:
            if v in evidence:
                key = tuple(a[p] for p in net["parents"][v])
                w *= net["cpt"][v][key][evidence[v]]
            else:
                key = tuple(a[p] for p in net["parents"][v])
                p = net["cpt"][v][key]["T"]
                a[v] = "T" if rng.random() < p else "F"
        num[a[query]] += w
        den += w
    return num["T"] / den


def gibbs_sampling(net, query, evidence, n, rng, burn=300):
    """逐变量吉布斯（证据变量固定）。
    条件分布 ∝ P(v|父) × Π P(子=当前值|含 v 的父集)（马尔可夫毯）。"""
    state = dict(evidence)
    for v in net["parents"]:
        if v not in evidence:
            state[v] = rng.choice(("T", "F"))
    hits = {"T": 0, "F": 0}
    for it in range(n + burn):
        for v in net["parents"]:
            if v in evidence:
                continue
            p_t, p_f = 0.0, 0.0
            for val in ("T", "F"):
                prior = net["cpt"][v][tuple(state[p2] for p2 in net["parents"][v])][val]
                prod = 1.0
                for c, ps in net["parents"].items():
                    if v in ps:
                        key = tuple((state[c2] if c2 != v else val) for c2 in ps)
                        prod *= net["cpt"][c][key][state[c]]
                if val == "T":
                    p_t = prior * prod
                else:
                    p_f = prior * prod
            state[v] = "T" if rng.random() < p_t / (p_t + p_f + 1e-300) else "F"
        if it >= burn:
            hits[state[query]] += 1
    total = hits["T"] + hits["F"]
    return hits["T"] / total


net = build_sprinkler()
rng = random.Random(61)

print("== 查询：P(Rain=T | Wet=T, Slippery=F) ==")
query, evidence = "Rain", {"Wet": "T", "Slippery": "F"}
exact = exact_posterior(net, query, evidence)
print(f"  精确枚举 = {exact['T']:.4f}")

print("\n== 单次估计对照（n=3000）==")
print(f"  {'方法':<16}{'估计值':>10}")
p, tried = rejection_sampling(net, query, evidence, 3000, rng)
print(f"  {'拒绝采样':<16}{p:>10.4f}   （丢弃 {tried - 3000} 个样本）")
p_lw = likelihood_weighting(net, query, evidence, 3000, rng)
print(f"  {'似然加权':<16}{p_lw:>10.4f}")
p_gibbs = gibbs_sampling(net, query, evidence, 3000, rng)
print(f"  {'吉布斯采样':<16}{p_gibbs:>10.4f}")

print("\n== 20 次独立重跑：均值与标准差 ==")


def mean_std(vals):
    m = sum(vals) / len(vals)
    var = sum((v - m) ** 2 for v in vals) / len(vals)
    return m, math.sqrt(var)


runs = 20
res = {"拒绝采样": [], "似然加权": [], "吉布斯": []}
for _ in range(runs):
    r, _t = rejection_sampling(net, query, evidence, 2000, rng)
    res["拒绝采样"].append(r)
    res["似然加权"].append(likelihood_weighting(net, query, evidence, 2000, rng))
    res["吉布斯"].append(gibbs_sampling(net, query, evidence, 2000, rng))
print(f"  {'方法':<16}{'均值':>10}{'标准差':>10}{'与精确差':>10}")
for name, vals in res.items():
    m, s = mean_std(vals)
    print(f"  {name:<16}{m:>10.4f}{s:>10.4f}{abs(m - exact['T']):>10.4f}")
print("  拒绝采样无偏但方差可能极大（证据罕见时样本极少）；")
print("  似然加权把证据『固化』并赋权 —— 方差通常小得多")

print("\n== 证据稀有度的杀伤力 ==")
hard_evidence = {"Wet": "T", "Sprinkler": "T", "Rain": "T"}
exact_hard = exact_posterior(net, "Cloudy", hard_evidence)
r, tried = rejection_sampling(net, "Cloudy", hard_evidence, 100, rng)
print(f"  证据 {hard_evidence}: P(Cloudy=T|e) = {exact_hard['T']:.4f}")
print(f"  拒绝采样为凑 100 个有效样本试了 {tried} 次（接受率 {100 / tried:.1%}）")
print(f"  似然加权只需 {100} 次前向（每次都算数）")
print("  证据概率 0.1% 时拒绝采样基本不可用 —— 似然加权由此而生")

print("\n== 方法选择速查 ==")
print(f"  {'方法':<14}{'精度':<10}{'成本':<20}{'适用'}")
for row in (("枚举", "精确", "O(2^n) 状态爆炸", "小网络/基准"),
            ("变量消元", "精确", "指数于树宽", "中小网络主力"),
            ("拒绝采样", "无偏", "1/接受率", "证据概率高"),
            ("似然加权", "加权无偏", "O(n)", "通用近似"),
            ("吉布斯", "渐近无偏", "混合速度", "大网络、条件好采样")):
    print(f"  {row[0]:<14}{row[1]:<10}{row[2]:<20}{row[3]}")

print("\n== 小结 ==")
for line in (
    "  精确方法受网络宽度限制；采样方法受方差限制",
    "  似然加权 = 重要性采样的图模型特化：证据直接当条件",
    "  诊断标准：多链重跑看方差 —— 单次估计没有说服力",
    "  890 课：把本章拼成医疗诊断专家系统",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「自适应似然加权」：权重过散时自动增加样本量，比较最终方差。
# 2. 把吉布斯改为「块采样」（Sprinkler+Rain 联合重采），观察混合改善。
# 3. 实现「重要性采样 + 重采样」（872 课思想）用在图模型推断上。
# 4. 思考：为什么证据变量的顺序会影响似然加权的方差？有没有最优顺序的
#    直觉规则（连接证据的变量先采样）？
