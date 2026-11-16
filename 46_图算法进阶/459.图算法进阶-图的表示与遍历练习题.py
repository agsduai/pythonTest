# ===== 第459课：图算法进阶-图的表示与遍历 =====
# 知识点：
#   - 图的两种表示：邻接表（省空间，遍历邻居快）、邻接矩阵（查边 O(1)，占 n²）
#   - 有向/无向：无向边要在两个方向各存一次
#   - 带权图：邻居存 (节点, 权重)
#   - BFS：按层扩散，适合“最少跳数”；DFS：一条路走到底，适合连通性/拓扑
#   - 与第332/333课呼应：那两课用无权图，这里加入权重与建图工具
from collections import defaultdict, deque


def build_graph(edges, directed=False):
    """边列表 → 邻接表。edges: [(u, v, weight), ...]"""
    graph = defaultdict(list)
    for u, v, w in edges:
        graph[u].append((v, w))
        if not directed:
            graph[v].append((u, w))
        else:
            graph.setdefault(v, [])
    # 邻居按名字排序，输出稳定
    return {node: sorted(neighbors, key=lambda x: x[0]) for node, neighbors in graph.items()}


def bfs(graph, start):
    """无权意义下的层序遍历（忽略权重）。"""
    visited = {start}
    order = []
    queue = deque([start])
    while queue:
        node = queue.popleft()
        order.append(node)
        for nxt, _ in graph[node]:
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    return order


def dfs(graph, start, visited=None):
    visited = visited or set()
    visited.add(start)
    order = [start]
    for nxt, _ in graph[start]:
        if nxt not in visited:
            order.extend(dfs(graph, nxt, visited))
    return order


def degree_stats(graph, directed=False):
    stats = {}
    for node, neighbors in graph.items():
        stats[node] = {"out": len(neighbors), "in": 0}
    for node, neighbors in graph.items():
        for nxt, _ in neighbors:
            stats.setdefault(nxt, {"out": 0, "in": 0})["in"] += 1
    if not directed:                       # 无向图：出入度合并为度数
        for node in stats:
            stats[node] = {"degree": stats[node]["in"]}
    return stats


# ---- 无向带权图：城市路网 ----
EDGES = [
    ("北京", "天津", 120), ("北京", "石家庄", 280),
    ("天津", "济南", 320), ("石家庄", "郑州", 410),
    ("济南", "郑州", 440), ("郑州", "武汉", 520),
]
graph = build_graph(EDGES)
print("== 邻接表 ==")
for node, neighbors in graph.items():
    print(f"  {node}: {neighbors}")

print("\n== 度数 ==")
for node, deg in degree_stats(graph).items():
    print(f"  {node}: {deg['degree']}")

print("\n== BFS（从北京出发）==")
print("  ", " → ".join(bfs(graph, "北京")))
print("== DFS ==")
print("  ", " → ".join(dfs(graph, "北京")))

# ---- 有向图：依赖关系 ----
DIRECTED = [("A", "B", 1), ("A", "C", 1), ("B", "D", 1), ("C", "D", 1)]
dg = build_graph(DIRECTED, directed=True)
print("\n== 有向图邻接表 ==")
for node, neighbors in dg.items():
    print(f"  {node} → {neighbors}")
print("  出/入度：", degree_stats(dg, directed=True))

# ---- 邻接矩阵：小图、频繁查边时用 ----
nodes = ["A", "B", "C", "D"]
index = {n: i for i, n in enumerate(nodes)}
INF = float("inf")
matrix = [[INF] * len(nodes) for _ in nodes]
for i in range(len(nodes)):
    matrix[i][i] = 0
for u, v, w in DIRECTED:
    matrix[index[u]][index[v]] = w
print("\n== 邻接矩阵 ==")
print("      " + "".join(f"{n:>6s}" for n in nodes))
for i, row in enumerate(matrix):
    print(f"  {nodes[i]}  " + "".join(f"{v:>6}" if v != INF else "  ∞ " for v in row))

# ===== 练习题 =====
# 1. 给 build_graph 增加“重复边取最小值”的处理。
# 2. 实现 connected_components(graph)：返回连通分量个数（BFS 计数）。
# 3. 把邻接矩阵版改成自动从边列表构建。
# 4. 思考：10 万个节点、20 万条边，邻接表和邻接矩阵各占多少内存？
