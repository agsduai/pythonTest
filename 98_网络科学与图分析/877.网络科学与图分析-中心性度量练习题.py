# ===== 第877课：网络科学与图分析-中心性度量 =====
# 知识点：
#   - 「谁最重要」取决于重要性的定义 -> 四种中心性四种答案
#   - 度中心性：连接数最多（局部流行度）
#   - 接近中心性：到所有人平均距离最短（信息传播起点）
#   - 介数中心性：出现在多少最短路径上（桥梁/瓶颈）
#   - 特征向量中心性：连接高价值节点（PageRank 的无阻尼近亲）
#   - Brandes 算法：O(V·E) 一次全源 BFS 计算全部介数
# 依赖：无（标准库）
from collections import deque


def bfs_dist(adj, s):
    dist = {s: 0}
    queue = deque([s])
    while queue:
        v = queue.popleft()
        for w in adj[v]:
            if w not in dist:
                dist[w] = dist[v] + 1
                queue.append(w)
    return dist


def degree_centrality(adj):
    return {v: len(nb) for v, nb in adj.items()}


def closeness_centrality(adj):
    out = {}
    for s in adj:
        dist = bfs_dist(adj, s)
        reach = sum(d for d in dist.values())
        out[s] = (len(dist) - 1) / reach if reach else 0.0
    return out


def betweenness_centrality(adj):
    """Brandes 算法（无向图结果除以 2）。"""
    bc = {v: 0.0 for v in adj}
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
                delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                bc[w] += delta[w]
    for v in bc:
        bc[v] /= 2
    return bc


def eigenvector_centrality(adj, iters=100):
    x = {v: 1.0 for v in adj}
    for _ in range(iters):
        new = {v: 0.0 for v in adj}
        for v, nb in adj.items():
            for w in nb:
                new[w] += x[v]
        norm = max(new.values())
        if norm == 0:
            return {v: 0.0 for v in adj}
        x = {v: val / norm for v, val in new.items()}
    return x


print("== 构造带桥梁的网络：两个团由 3-4 一条边连接 ==")
edges = [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3),
         (3, 4),
         (4, 5), (4, 6), (5, 6), (5, 7), (6, 7)]
adj = {i: set() for i in range(8)}
for a, b in edges:
    adj[a].add(b)
    adj[b].add(a)
print("  团A {0,1,2,3} — 边(3,4) — 团B {4,5,6,7}")

deg = degree_centrality(adj)
clo = closeness_centrality(adj)
bet = betweenness_centrality(adj)
eig = eigenvector_centrality(adj)

print("\n== 四种中心性对照表 ==")
print(f"  {'节点':>4}{'度':>4}{'接近':>8}{'介数':>9}{'特征向量':>10}")
for v in sorted(adj):
    print(f"  {v:>4}{deg[v]:>4}{clo[v]:>8.3f}{bet[v]:>9.3f}{eig[v]:>10.3f}")

print("\n== 谁是『最重要』的？ ==")
top_by = {}
for name, score in (("度", deg), ("接近", clo), ("介数", bet), ("特征向量", eig)):
    top = max(adj, key=lambda v: score[v])
    top_by[name] = top
    print(f"  {name}中心性最高: 节点 {top} (值 {score[top]:.3f})")
print("  度出现并列 —— 用『度+介数』才分辨出 3 是桥梁；不同问题要选不同度量")
print("  若删除节点 3：两团断开，网络分家 —— 介数最高的节点正是结构脆弱点")

print("\n== 移除桥梁节点的影响 ==")


def largest_component_frac(adj):
    seen, best = set(), 0
    for s in adj:
        if s in seen:
            continue
        comp, queue = {s}, deque([s])
        while queue:
            v = queue.popleft()
            for w in adj[v]:
                if w not in comp:
                    comp.add(w)
                    queue.append(w)
        seen |= comp
        best = max(best, len(comp))
    return best / len(adj)


adj_removed = {v: set(nb) for v, nb in adj.items()}
for a, b in list(adj_removed.items()):
    adj_removed[a].discard(3)
adj_removed = {v: {w for w in nb if w != 3} for v, nb in adj_removed.items()}
for v in adj_removed:
    adj_removed[v].discard(3)
print(f"  原网络最大分量占比 = {largest_component_frac(adj):.0%}")
print(f"  移除节点 3 后       = {largest_component_frac(adj_removed):.0%}")
print("  介数中心性就是『移除后网络碎裂程度』的一阶近似 —— 流行病学键人物的度量")

print("\n== 示例：星形网络的诊断 ==")
star = {0: set(range(1, 6))}
for i in range(1, 6):
    star[i] = {0}
sd, sc, sb, se = (degree_centrality(star), closeness_centrality(star),
                  betweenness_centrality(star), eigenvector_centrality(star))
print(f"  中心节点 0: 度 {sd[0]}, 接近 {sc[0]:.2f}, 介数 {sb[0]:.1f}")
print(f"  叶节点 1:   度 {sd[1]}, 接近 {sc[1]:.2f}, 介数 {sb[1]:.1f}, 特征向量 {se[1]:.2f}")
print("  星形叶节点度为 1 但特征向量高（连着中心）—— 度的失真被特征向量修正")

print("\n== 小结 ==")
for line in (
    "  中心性没有唯一答案：广告选度、疫情防控选介数、信息源选接近",
    "  Brandes 用一次全源 BFS 把介数降到 O(VE)，工程上完全可行",
    "  特征向量/PageRank 类度量是『网络递归定义的影响力』",
    "  下一课：不只找单点，而是找「群落」—— 社区发现",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现加权版的接近中心性（速度），比较权重反转（延迟 vs 强度）两种语义。
# 2. 实现 percolation 中心性：按「移除后最大分量缩减量」逐个移除 top-5 介数
#    节点，观察网络解体曲线。
# 3. 在 875 课的 ER 图上计算四种中心性并排序，验证它们在随机图上高度一致。
# 4. 思考：为什么介数中心性对「最短路径」敏感而现实传播（如谣言）不走最短
#    路径？有哪些替代定义（current-flow / 随机游走介数）？
