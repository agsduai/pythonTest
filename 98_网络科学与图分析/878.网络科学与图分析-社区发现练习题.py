# ===== 第878课：网络科学与图分析-社区发现 =====
# 知识点：
#   - 社区 = 内部连接稠密、之间连接稀疏的节点群
#   - 标签传播（LPA）：节点采纳邻居多数标签，随机顺序迭代到稳定 —— O(E) 极快
#   - Girvan-Newman：反复移除介数最高的边，社区从桥边处裂开 —— 慢但直观
#   - 模块度 Q：社区内边占比减去随机图期望 —— 衡量划分质量，Q>0.3 算有结构
#   - Q = Σ_c [ l_c/m - (d_c/2m)² ]，l_c 社区内边数，d_c 社区度总和
# 依赖：无（标准库）
from collections import deque
import random


def build_adj(edges, nodes):
    adj = {v: set() for v in nodes}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    return adj


def components_of(adj):
    seen, comps = set(), []
    for s in adj:
        if s in seen:
            continue
        comp, queue = {s}, deque([s])
        while queue:
            v = queue.pop()
            for w in adj[v]:
                if w not in comp:
                    comp.add(w)
                    queue.append(w)
        seen |= comp
        comps.append(comp)
    return comps


def modularity(adj, labels):
    m = sum(len(nb) for nb in adj.values()) / 2
    if m == 0:
        return 0.0
    deg = {v: len(adj[v]) for v in adj}
    lc = {}
    dc = {}
    for v, nb in adj.items():
        dc[labels[v]] = dc.get(labels[v], 0) + deg[v]
        for w in nb:
            if labels[w] == labels[v] and v < w:
                lc[labels[v]] = lc.get(labels[v], 0) + 1
    q = 0.0
    for c in set(labels.values()):
        q += lc.get(c, 0) / m - (dc.get(c, 0) / (2 * m)) ** 2
    return q


def label_propagation(adj, rng, max_iter=50):
    labels = {v: i for i, v in enumerate(adj)}
    for it in range(max_iter):
        order = list(adj)
        rng.shuffle(order)
        changed = False
        for v in order:
            if not adj[v]:
                continue
            counts = {}
            for w in adj[v]:
                counts[labels[w]] = counts.get(labels[w], 0) + 1
            best = max(counts.values())
            candidates = [c for c, n in counts.items() if n == best]
            new = rng.choice(candidates) if len(candidates) > 1 else candidates[0]
            if new != labels[v]:
                labels[v] = new
                changed = True
        if not changed:
            return labels, it + 1
    return labels, max_iter


def edge_betweenness(adj):
    eb = {}
    for s in adj:
        S = []
        P = {v: [] for v in adj}
        sigma = {v: 0 for v in adj}
        sigma[s] = 1
        dist = {s: 0}
        queue = deque([s])
        while queue:
            v = queue.popleft()
            S.append(v)
            for w in adj[v]:
                if w not in dist:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    P[w].append(v)
        delta = {v: 0.0 for v in adj}
        while S:
            w = S.pop()
            for v in P[w]:
                c = (sigma[v] / sigma[w]) * (1 + delta[w])
                delta[v] += c
                key = (min(v, w), max(v, w))
                eb[key] = eb.get(key, 0.0) + c
    for k in eb:
        eb[k] /= 2
    return eb


def girvan_newman(adj, target_comps=2):
    g = {v: set(nb) for v, nb in adj.items()}
    m0 = sum(len(nb) for nb in g.values()) / 2
    history = []
    while True:
        comps = components_of(g)
        labels = {}
        for i, comp in enumerate(comps):
            for v in comp:
                labels[v] = i
        q = modularity(adj, labels)
        history.append((len(comps), q))
        if len(comps) >= target_comps:
            return comps, history
        eb = edge_betweenness(g)
        top = max(eb, key=eb.get)
        g[top[0]].discard(top[1])
        g[top[1]].discard(top[0])


print("== 构造两个 planted 社区 ==")
rng = random.Random(8)
nodes = list(range(12))
edges = []
for a in range(12):
    for b in range(a + 1, 12):
        same = (a < 6) == (b < 6)
        p = 0.7 if same else 0.08
        if rng.random() < p:
            edges.append((a, b))
adj = build_adj(edges, nodes)
print(f"  社区A {list(range(6))}, 社区B {list(range(6, 12))}")
print(f"  边数 = {len(edges)}，其中跨社区 {sum(1 for a, b in edges if (a < 6) != (b < 6))} 条")
print(f"  真实划分的模块度 Q = {modularity(adj, {v: 0 if v < 6 else 1 for v in nodes}):.3f}")

print("\n== 标签传播（LPA）==")
labels, iters = label_propagation(adj, rng)
comps = {}
for v, c in labels.items():
    comps.setdefault(c, []).append(v)
print(f"  {iters} 轮收敛，发现 {len(comps)} 个社区:")
for c, members in comps.items():
    print(f"    社区{c}: {sorted(members)}")
print(f"  划分模块度 Q = {modularity(adj, labels):.3f}")
print("  LPA 单次结果依赖随机顺序 —— 工程上跑多次取模块度最高的一次")

print("\n== Girvan-Newman：从桥边裂开 ==")
comps_gn, history = girvan_newman(adj, target_comps=2)
print(f"  {'移除边数':>8}{'分量数':>8}{'模块度Q':>9}")
for step, (ncomp, q) in enumerate(history):
    print(f"  {step:>8}{ncomp:>8}{q:>9.3f}")
for i, comp in enumerate(sorted(comps_gn, key=lambda c: min(c))):
    print(f"  社区{i}: {sorted(comp)}")
print("  GN 每一步移掉介数最高的边 —— 桥边最先断，社区沿真实结构裂开")

print("\n== 模块度曲线的含义 ==")
best = max(history, key=lambda x: x[1])
print(f"  模块度峰值 = {best[1]:.3f}（分量数 = {best[0]}）")
print("  继续移除边后 Q 下降 -> 把本来连着的社区又拆开了")
print("  工程策略：GN/LPA 产出多个划分，选 Q 最大者（GN 变体：峰值即停）")

print("\n== 环形图的反例（社区不唯一的提醒）==")
ring = {i: {(i - 1) % 10, (i + 1) % 10} for i in range(10)}
rl, rit = label_propagation(ring, rng)
print(f"  10 节点环：LPA {rit} 轮收敛 -> {len(set(rl.values()))} 个社区")
print("  环上没有稠密子群，任何切法都是人为的 —— 指标好看≠社区真实存在")

print("\n== 小结 ==")
for line in (
    "  LPA 快而随机，GN 慢而可解释 —— 大图用 LPA/Louvain，小图可 GN",
    "  模块度是划分质量的通用标尺，但它自身有分辨率极限（练习）",
    "  桥边（高介数边）是社区之间的公路，社区发现的第一刀切在这里",
    "  下一课：小世界网络 —— 真实社交网的高聚类+短路径之谜",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Louvain 的第一阶段：节点贪心移入能最大提升 Q 的邻居社区，与 LPA 对比。
# 2. 构造「环上每个节点都连两个远端点」的解析极限图，演示模块度分辨率极限。
# 3. 让 LPA 跑 20 次不同随机种子，统计社区数量分布与模块度分布。
# 4. 思考：为什么 GN 用「边介数」而不是「节点介数」来决定切哪里？
