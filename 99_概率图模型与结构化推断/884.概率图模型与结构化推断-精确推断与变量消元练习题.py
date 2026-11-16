# ===== 第884课：概率图模型与结构化推断-精确推断与变量消元 =====
# 知识点：
#   - 推断任务：P(查询 | 证据) —— 贝叶斯网络的全部价值都在推断上
#   - 朴素枚举：对全部联合取值求和 —— O(2^n)，浪费且重复计算
#   - 因子（factor）= 小联合分布表；推断 = 因子的乘积/边缘化
#   - 变量消元（VE）：按序消掉非查询变量，中间因子远小于全联合表
#   - 消元顺序影响成本：最优顺序是 NP 难的，但启发式（贪心最小因子）足够
# 依赖：无（标准库）
from itertools import product as iproduct
from collections import deque


class BayesNet:
    def __init__(self):
        self.parents = {}
        self.cpt = {}
        self.values = ("T", "F")

    def add(self, node, parents, cpt):
        self.parents[node] = list(parents)
        self.cpt[node] = cpt

    def topo(self):
        children = {v: [] for v in self.parents}
        indeg = {v: len(self.parents[v]) for v in self.parents}
        for v, ps in self.parents.items():
            for p in ps:
                children[p].append(v)
        queue = deque([v for v, d in indeg.items() if d == 0])
        order = []
        while queue:
            v = queue.popleft()
            order.append(v)
            for w in children[v]:
                indeg[w] -= 1
                if indeg[w] == 0:
                    queue.append(w)
        return order

    def node_prob(self, node, value, assignment):
        key = tuple(assignment[p] for p in self.parents[node])
        return self.cpt[node][key][value]

    def joint_prob(self, assignment):
        prob = 1.0
        for v in self.topo():
            prob *= self.node_prob(v, assignment[v], assignment)
        return prob


def build_sprinkler():
    net = BayesNet()
    net.add("Cloudy", [], {(): {"T": 0.5, "F": 0.5}})
    net.add("Sprinkler", ["Cloudy"], {("T",): {"T": 0.1, "F": 0.9},
                                      ("F",): {"T": 0.5, "F": 0.5}})
    net.add("Rain", ["Cloudy"], {("T",): {"T": 0.8, "F": 0.2},
                                 ("F",): {"T": 0.2, "F": 0.8}})
    net.add("Wet", ["Sprinkler", "Rain"],
            {("T", "T"): {"T": 0.99, "F": 0.01}, ("T", "F"): {"T": 0.9, "F": 0.1},
             ("F", "T"): {"T": 0.8, "F": 0.2}, ("F", "F"): {"T": 0.0, "F": 1.0}})
    net.add("Slippery", ["Wet"], {("T",): {"T": 0.7, "F": 0.3},
                                  ("F",): {"T": 0.0, "F": 1.0}})
    return net


class Factor:
    def __init__(self, vars_, table):
        self.vars = tuple(vars_)
        self.table = table                  # {取值元组: 概率}


def factor_product(f1, f2):
    """因子乘积：变量取并集，概率相乘。"""
    shared = [v for v in f1.vars if v in f2.vars]
    extra2 = [v for v in f2.vars if v not in f1.vars]
    table = {}
    for k1, v1 in f1.table.items():
        a1 = dict(zip(f1.vars, k1))
        base = {v: val for v, val in a1.items()}
        for combo in iproduct(("T", "F"), repeat=len(extra2)):
            for v, val in zip(extra2, combo):
                base[v] = val
            k2 = tuple(base[v] for v in f2.vars)
            out_key = tuple(base[v] for v in f1.vars + tuple(extra2))
            table[out_key] = v1 * f2.table.get(k2, 0.0)
    return Factor(f1.vars + tuple(extra2), table)


def marginalize(f, var):
    """消掉变量：对其取值求和。"""
    idx = f.vars.index(var)
    rest = f.vars[:idx] + f.vars[idx + 1:]
    table = {}
    for k, v in f.table.items():
        key = k[:idx] + k[idx + 1:]
        table[key] = table.get(key, 0.0) + v
    return Factor(rest, table)


def restrict(f, evidence):
    """按证据裁剪：冲突行直接丢弃。"""
    keep = [i for i, v in enumerate(f.vars) if v not in evidence]
    table = {}
    for k, val in f.table.items():
        if any(v in evidence and k[i] != evidence[v]
               for i, v in enumerate(f.vars)):
            continue
        table[tuple(k[i] for i in keep)] = val
    return Factor([f.vars[i] for i in keep], table)


def variable_elimination(net, query, evidence, order, cost_counter=None):
    factors = []
    for node in net.topo():
        vars_ = [node] + net.parents[node]
        table = {}
        for combo in iproduct(("T", "F"), repeat=len(vars_)):
            a = dict(zip(vars_, combo))
            table[combo] = net.node_prob(node, a[node], a)
        factors.append(Factor(vars_, table))
    factors = [restrict(f, evidence) for f in factors]
    ops = 0
    for var in order:
        if var == query or var in evidence:
            continue
        related = [f for f in factors if var in f.vars]
        if not related:
            continue
        prod = related[0]
        for f in related[1:]:
            prod = factor_product(prod, f)
        ops += len(prod.table)
        factors = [f for f in factors if var not in f.vars]
        factors.append(marginalize(prod, var))
    result = factors[0]
    for f in factors[1:]:
        result = factor_product(result, f)
    if cost_counter is not None:
        cost_counter.append(ops)
    total = sum(result.table.values())
    dist = {}
    for k, v in result.table.items():
        dist[k[0]] = v / total
    return dist


def brute_force(net, query, evidence):
    nodes = net.topo()
    dist = {"T": 0.0, "F": 0.0}
    for combo in iproduct(("T", "F"), repeat=len(nodes)):
        a = dict(zip(nodes, combo))
        if any(a[e] != v for e, v in evidence.items()):
            continue
        p = net.joint_prob(a)
        dist[a[query]] += p
    total = dist["T"] + dist["F"]
    return {k: v / total for k, v in dist.items()}


net = build_sprinkler()

print("== 网络与推断任务 ==")
print("  Cloudy -> {Sprinkler, Rain}; Sprinkler/Rain -> Wet -> Slippery")
print("  任务：P(Rain | Wet=T) 等后验")

print("\n== VE vs 朴素枚举 ==")
cases = [("Rain", {"Wet": "T"}), ("Sprinkler", {"Wet": "T"}),
         ("Cloudy", {"Wet": "T", "Slippery": "T"})]
for query, ev in cases:
    ve = variable_elimination(net, query, ev, list(net.topo()))
    bf = brute_force(net, query, ev)
    match = all(abs(ve[k] - bf[k]) < 1e-12 for k in ("T", "F"))
    print(f"  P({query} | {ev}):")
    print(f"    VE   = {ve}")
    print(f"    枚举 = {bf}   一致: {match}")

print("\n== 解释掉现象（碰撞子开路）==")
p_spr_wet = variable_elimination(net, "Sprinkler", {"Wet": "T"}, list(net.topo()))
p_spr_both = variable_elimination(net, "Sprinkler", {"Wet": "T", "Rain": "T"},
                                  list(net.topo()))
print(f"  P(Sprinkler=T | Wet=T)        = {p_spr_wet['T']:.4f}")
print(f"  P(Sprinkler=T | Wet=T, Rain=T) = {p_spr_both['T']:.4f}")
print("  已确认下雨后，洒水器的嫌疑下降 —— 这就是贝叶斯的『责任分摊』")

print("\n== 消元顺序的成本差异 ==")
print(f"  {'消元顺序':<28}{'中间因子总规模':>14}")
for label, order in (("拓扑正序", list(net.topo())),
                     ("反序", list(reversed(net.topo())))):
    cost = []
    variable_elimination(net, "Rain", {"Wet": "T"}, order, cost_counter=cost)
    print(f"  {label:<28}{cost[0]:>14}")
print("  小网络差异不明显；网络一大，顺序决定推断是否可行（最优顺序 NP 难）")

print("\n== 小结 ==")
for line in (
    "  因子乘积 + 边缘化是精确推断的两个原子操作",
    "  VE 的本质：利用网络结构复用部分和，避免重复枚举",
    "  消元顺序决定中间因子宽度（树宽）—— 图结构的性质",
    "  885 课：精确推断撑不住时怎么办 —— 先看隐变量模型与 EM",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「贪心最小因子」消元顺序：每步选使中间因子最小的变量，对比正序/反序成本。
# 2. 把 VE 推广到三值节点并验证与枚举一致。
# 3. 实现证据敏感的先验（virtual evidence）：给 Wet 加软证据系数 0.6/0.4，观察后验。
# 4. 思考：为什么 VE 在链状网络上是最优的，而在稠密网络上退化为枚举？
