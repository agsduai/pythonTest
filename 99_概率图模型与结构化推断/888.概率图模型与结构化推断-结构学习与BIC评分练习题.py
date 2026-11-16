# ===== 第888课：概率图模型与结构化推断-结构学习与BIC评分 =====
# 知识点：
#   - 结构学习：从数据中同时学「图」与「参数」—— 比参数学习难得多
#   - 评分搜索框架：给每个图打分（似然 + 复杂度惩罚），在图空间爬山
#   - BIC = log似然 - (log N / 2)·参数数：惩罚过拟合，倾向稀疏图
#   - 三种局部操作：加边 / 删边 / 反向边（需保持无环）
#   - 等价类问题：BIC 无法区分马尔可夫等价的图（如 A→B vs B→A 常得分相同）
# 依赖：无（标准库）
import math
import random
from collections import deque


def make_true_net():
    parents = {"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"]}
    cpt = {
        "A": {(): {"T": 0.4, "F": 0.6}},
        "B": {("T",): {"T": 0.7, "F": 0.3}, ("F",): {"T": 0.2, "F": 0.8}},
        "C": {("T",): {"T": 0.5, "F": 0.5}, ("F",): {"T": 0.1, "F": 0.9}},
        "D": {("T", "T"): {"T": 0.9, "F": 0.1}, ("T", "F"): {"T": 0.6, "F": 0.4},
              ("F", "T"): {"T": 0.5, "F": 0.5}, ("F", "F"): {"T": 0.05, "F": 0.95}},
    }
    return {"parents": parents, "cpt": cpt}


def forward_sample(net, rng):
    assignment = {}
    for v in net["parents"]:
        p = net["cpt"][v][tuple(assignment[p] for p in net["parents"][v])]["T"]
        assignment[v] = "T" if rng.random() < p else "F"
    return assignment


def is_acyclic(parents, nodes):
    indeg = {v: len(parents[v]) for v in nodes}
    children = {v: [] for v in nodes}
    for v, ps in parents.items():
        for p in ps:
            children[p].append(v)
    queue = deque([v for v, d in indeg.items() if d == 0])
    seen = 0
    while queue:
        v = queue.popleft()
        seen += 1
        for w in children[v]:
            indeg[w] -= 1
            if indeg[w] == 0:
                queue.append(w)
    return seen == len(nodes)


def bic_score(data, parents):
    """BIC = 数据对数似然(按候选结构估参) - (log N / 2)·参数数。
    每个节点的参数 = 出现过的父配置数（每个配置一个自由比例参数）。"""
    n = len(data)
    ll = 0.0
    params = 0
    for v, ps in parents.items():
        counts = {}
        for row in data:
            key = tuple(row[p] for p in ps) + (row[v],)
            counts[key] = counts.get(key, 0) + 1
        configs = set(k[:-1] for k in counts)
        for config in configs:
            n_t = counts.get(config + ("T",), 0)
            n_f = counts.get(config + ("F",), 0)
            tot = n_t + n_f
            if tot == 0:
                continue
            p = n_t / tot                        # 最大似然估计
            ll += n_t * math.log(max(p, 1e-12)) + n_f * math.log(max(1 - p, 1e-12))
            params += 1
    return ll - (math.log(n) / 2) * params


def hill_climb(data, nodes, max_iter=100):
    parents = {v: [] for v in nodes}
    best = bic_score(data, parents)
    history = [("空图", best)]
    for _ in range(max_iter):
        best_op, best_score = None, best
        for a in nodes:                              # 加边
            for b in nodes:
                if a == b or a in parents[b]:
                    continue
                trial = {v: list(ps) for v, ps in parents.items()}
                trial[b].append(a)
                if not is_acyclic(trial, nodes):
                    continue
                s = bic_score(data, trial)
                if s > best_score + 1e-9:
                    best_score, best_op = s, (f"加边 {a}->{b}", trial)
        for v in nodes:                              # 删边
            for p in list(parents[v]):
                trial = {k: list(ps) for k, ps in parents.items()}
                trial[v].remove(p)
                s = bic_score(data, trial)
                if s > best_score + 1e-9:
                    best_score, best_op = s, (f"删边 {p}->{v}", trial)
        for v in nodes:                              # 反转
            for p in list(parents[v]):
                trial = {k: list(ps) for k, ps in parents.items()}
                trial[v].remove(p)
                trial[p].append(v)
                if not is_acyclic(trial, nodes):
                    continue
                s = bic_score(data, trial)
                if s > best_score + 1e-9:
                    best_score, best_op = s, (f"反转 {p}<->{v}", trial)
        if best_op is None:
            break
        label, parents = best_op
        best = best_score
        history.append((label, best))
    return parents, best, history


rng = random.Random(51)
true_net = make_true_net()
nodes = ["A", "B", "C", "D"]

print("== 真实网络与数据生成 ==")
print("  真实结构: A -> B, A -> C, B -> D, C -> D")
data = [forward_sample(true_net, rng) for _ in range(3000)]
print(f"  前向采样 {len(data)} 行")
print(f"  BIC(真实结构) = {bic_score(data, true_net["parents"]):.2f}")

print("\n== 从空图爬山 ==")
learned, score, history = hill_climb(data, nodes)
print(f"  {'步骤':<14}{'BIC':>12}")
for label, s in history:
    print(f"  {label:<14}{s:>12.2f}")
print(f"\n  学到的结构:")
for v in nodes:
    print(f"    {v} <- {learned[v] or '（无父节点）'}")
true_edges = {("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")}
learned_edges = {(p, v) for v in nodes for p in learned[v]}
print(f"  真实边集: {sorted(true_edges)}")
print(f"  学到边集: {sorted(learned_edges)}")
print(f"  完全一致: {true_edges == learned_edges}")

print("\n== BIC 的稀疏化压力 ==")
redundant = {v: list(ps) for v, ps in true_net["parents"].items()}
redundant["D"].append("A")
print(f"  真实结构+冗余边 D<-A 的 BIC = {bic_score(data, redundant):.2f}")
print(f"  真实结构本身的 BIC         = {bic_score(data, true_net["parents"]):.2f}")
print("  多出的参数拿不到足够的似然补偿 -> BIC 更低，爬山不会选它")

print("\n== 样本量与可辨识性 ==")
for n_samples in (100, 300, 1000, 3000):
    d2 = [forward_sample(true_net, rng) for _ in range(n_samples)]
    p2, _, _ = hill_climb(d2, nodes)
    edges2 = {(p, v) for v in nodes for p in p2[v]}
    print(f"  样本 {n_samples:>5}: 学到 {sorted(edges2)}")
print("  样本太少时 BIC 倾向空图（全独立）；足够后才恢复真实结构")

print("\n== 等价类提醒 ==")
print("  BIC 对 A->B 与 B->A 常给出相同分数（似然与参数数都一样）")
print("  纯观测数据只能确定到马尔可夫等价类；区分方向需要干预/时间序")
print("  这正是因果发现（causal discovery）作为独立领域的由来")

print("\n== 小结 ==")
for line in (
    "  结构学习 = 组合优化：评分（BIC）+ 局部搜索（加/删/反转）",
    "  惩罚项是灵魂：无惩罚会学到全连接的「作弊图」",
    "  学到的图是等价类代表，方向解释要谨慎",
    "  889 课：推断方法全家桶对照 —— 枚举到采样的完整光谱",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 AIC 评分（惩罚系数 1 而非 logN/2），对比两种准则学到的结构差异。
# 2. 实现贪心最小父集：对每个节点先做单变量筛选再拼图，对比爬山结果。
# 3. 加约束边集（白名单/黑名单），模拟「领域知识」对结构学习的影响。
# 4. 思考：为什么结构学习的搜索空间是超指数的？变量数到 50 时该怎么办
#    （提示：模块化、先验约束、分支定界）？
