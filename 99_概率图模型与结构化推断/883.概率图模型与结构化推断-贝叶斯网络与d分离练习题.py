# ===== 第883课：概率图模型与结构化推断-贝叶斯网络与d-分离 =====
# 知识点：
#   - 贝叶斯网络 = DAG + 每个节点的条件概率表（CPT）
#   - 联合分布按图分解：P(X1..Xn) = Π P(Xi | Pa(Xi)) —— 图「编码」条件独立
#   - 三种基本结构：链 A→B→C、分叉 A←B→C、汇（碰撞子）A→B←C
#   - d-分离：给定 Z 后 X 与 Y 无活跃路径 => X ⊥ Y | Z
#   - 关键反直觉：条件在碰撞子上会「打开」路径（解释掉/伯克森悖论）
#   - 判定算法：祖先集 + 道德化 + 删 Z 判连通（Lauritzen 法），再用枚举验证
# 依赖：无（标准库）
from collections import deque
from itertools import product as iproduct
import random


class BayesNet:
    """全二值贝叶斯网络。CPT 键为父节点取值元组。"""

    def __init__(self):
        self.parents = {}
        self.cpt = {}
        self.values = ("T", "F")

    def add(self, node, parents, cpt):
        self.parents[node] = list(parents)
        self.cpt[node] = cpt

    def topo(self):
        indeg = {v: len(self.parents[v]) for v in self.parents}
        children = {v: [] for v in self.parents}
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

    def forward_sample(self, rng):
        assignment = {}
        for v in self.topo():
            p = self.node_prob(v, self.values[0], assignment)
            assignment[v] = self.values[0] if rng.random() < p else self.values[1]
        return assignment


def d_separated(net, x, y, zs):
    """d-分离判定：祖先集 + 道德化 + 删 Z 判连通。"""
    A = {x, y, *zs}
    queue = deque(A)
    while queue:                                   # 补齐祖先
        v = queue.popleft()
        for p in net.parents[v]:
            if p not in A:
                A.add(p)
                queue.append(p)
    edges = set()
    for v in A:
        for p in net.parents[v]:
            if p in A:
                edges.add((p, v))
                edges.add((v, p))
        ps = [p for p in net.parents[v] if p in A]  # 道德化：同父互连（碰撞子开路）
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                edges.add((ps[i], ps[j]))
                edges.add((ps[j], ps[i]))
    zset = set(zs)
    seen = {x}
    queue = deque([x])
    while queue:
        v = queue.popleft()
        for w, u in edges:
            if w == v and u not in seen and u not in zset:
                seen.add(u)
                queue.append(u)
    return y not in seen


def cond_independent_enum(net, x, y, zs):
    """枚举联合分布验证 x ⊥ y | z（真值参照）。"""
    nodes = net.topo()
    count = {}
    for combo in iproduct(net.values, repeat=len(nodes)):
        a = dict(zip(nodes, combo))
        p = net.joint_prob(a)
        if p <= 0:
            continue
        key = (a[x], a[y]) + tuple(a[z] for z in zs)
        count[key] = count.get(key, 0.0) + p
    independent = True
    for zvals in iproduct(net.values, repeat=len(zs)):
        pz = sum(count.get((xx, yy) + zvals, 0.0)
                 for xx in net.values for yy in net.values)
        if pz <= 1e-12:
            continue
        px = {v: sum(count.get((v, yy) + zvals, 0.0)
                     for yy in net.values) / pz for v in net.values}
        py = {v: sum(count.get((xx, v) + zvals, 0.0)
                     for xx in net.values) / pz for v in net.values}
        for xv in net.values:
            for yv in net.values:
                pxy = count.get((xv, yv) + zvals, 0.0) / pz
                if abs(pxy - px[xv] * py[yv]) > 1e-9:
                    independent = False
    return independent


print("== 构建经典喷水器网络 ==")
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
print("  Cloudy -> {Sprinkler, Rain};  Sprinkler/Rain -> Wet;  Wet -> Slippery")
print(f"  拓扑序 = {net.topo()}")

print("\n== d-分离判定 vs 枚举真值 ==")
tests = [
    ("Sprinkler", "Rain", (), "分叉：共同原因未条件 -> 依赖（d-连通）"),
    ("Sprinkler", "Rain", ("Cloudy",), "条件在共同原因上 -> 阻断 -> 独立"),
    ("Sprinkler", "Rain", ("Wet",), "碰撞子 Wet 被条件 -> 打开（解释掉）"),
    ("Wet", "Slippery", (), "链 Wet->Slippery -> 依赖"),
    ("Cloudy", "Slippery", ("Wet",), "所有路径被 Wet 阻断 -> 独立"),
]
print(f"  {'查询':<26}{'d-分离':>8}{'枚举验证':>10}  结构解释")
for x, y, zs, why in tests:
    ds = d_separated(net, x, y, list(zs))
    ind = cond_independent_enum(net, x, y, list(zs))
    agree = "一致" if ds == ind else "矛盾!"
    print(f"  {x} ⊥ {y} | {str(list(zs) or '{}'):<12}{str(ds):>8}{str(ind):>10}  [{agree}] {why}")
print("  「条件在碰撞子上会打开路径」= 解释掉现象：知道下雨就降低洒水器的嫌疑")

print("\n== 联合分布与采样 ==")
rng = random.Random(21)
p_wet_exact = 0.0
for combo in iproduct(net.values, repeat=5):
    a = dict(zip(net.topo(), combo))
    p_wet_exact += net.joint_prob(a) if a["Wet"] == "T" else 0.0
samples = sum(1 for _ in range(20000) if net.forward_sample(rng)["Wet"] == "T") / 20000
print(f"  P(Wet=T) 枚举精确 = {p_wet_exact:.4f}   前向采样估计 = {samples:.4f}")
sample = net.forward_sample(rng)
print(f"  单次采样示例: {sample}")
print(f"  该采样联合概率 = {net.joint_prob(sample):.6f}")

print("\n== 小结 ==")
for line in (
    "  网络结构 + CPT 完全确定联合分布：分解让 2^5 表变成 5 张小表",
    "  d-分离是「图上可读的独立关系」：分叉阻断、碰撞子激活",
    "  判定算法三步：取祖先、道德化（同父相连）、删 Z 判连通",
    "  884 课：把这些独立关系变成推断的加速器 —— 变量消元",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现三值节点支持：values 扩为 (T,M,F)，CPT 泛化，重跑 d-分离测试。
# 2. 实现「伯克森悖论」定量演示：在网络上计算 P(Sprinkler|Rain,Wet) 与
#    P(Sprinkler|Rain) 对比。
# 3. 实现反向采样：给定 Wet=T 的观测，用拒绝采样生成后验样本，与枚举后验对比。
# 4. 思考：为什么道德化要「同父互连」？它对应 d-分离判定中哪种结构的打开？
