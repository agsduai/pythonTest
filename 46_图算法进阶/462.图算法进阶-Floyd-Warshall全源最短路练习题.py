# ===== 第462课：图算法进阶-Floyd-Warshall全源最短路 =====
# 知识点：
#   - 求“任意两点之间”的最短距离（全源最短路）
#   - 动态规划：dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
#   - 三重循环 O(n³)；n <= 几百时非常实用
#   - next 矩阵记录“从 i 到 j 的下一步”，用于还原路径
#   - 能处理负权边，但检测负环要看 dist[i][i] < 0
#   - 与第255课 DP、第460课 Dijkstra 的对比
INF = float("inf")


def floyd_warshall(n: int, edges: list[tuple]):
    """返回 (dist, nxt)。dist[i][j] 为最短距离，nxt 用于还原路径。"""
    dist = [[INF] * n for _ in range(n)]
    nxt = [[None] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0
        nxt[i][i] = i
    for u, v, w in edges:
        if w < dist[u][v]:                 # 处理重复边，取最小
            dist[u][v] = w
            nxt[u][v] = v

    for k in range(n):
        for i in range(n):
            if dist[i][k] == INF:
                continue
            for j in range(n):
                if dist[k][j] == INF:
                    continue
                candidate = dist[i][k] + dist[k][j]
                if candidate < dist[i][j]:
                    dist[i][j] = candidate
                    nxt[i][j] = nxt[i][k]

    return dist, nxt


def build_path(nxt, i, j):
    if nxt[i][j] is None:
        return []
    path = [i]
    while i != j:
        i = nxt[i][j]
        path.append(i)
    return path


# ---- 4 个节点的有向图 ----
NODES = ["A", "B", "C", "D"]
EDGES = [
    (0, 1, 4), (0, 2, 3),
    (1, 2, -2),              # 负权边：A→B→C = 2，比直达 3 更短
    (1, 3, 2), (2, 3, 4),
]
dist, nxt = floyd_warshall(4, EDGES)

print("== 全源最短距离矩阵 ==")
print("      " + "".join(f"{n:>8s}" for n in NODES))
for i, row in enumerate(dist):
    cells = []
    for v in row:
        cells.append("     ∞" if v == INF else f"{v:>6}")
    print(f"  {NODES[i]}  " + "".join(cells))

print("\n== 任意两点路径 ==")
pairs = [(0, 3), (0, 2), (1, 3), (2, 1)]
for i, j in pairs:
    path = build_path(nxt, i, j)
    if path:
        print(f"  {NODES[i]} → {NODES[j]}: {' → '.join(NODES[x] for x in path)}"
              f"（{dist[i][j]}）")
    else:
        print(f"  {NODES[i]} → {NODES[j]}: 不可达")

# ---- 负环检测 ----
print("\n== 负环检测 ==")
cycle_edges = [(0, 1, 1), (1, 2, -5), (2, 1, 1)]
d2, _ = floyd_warshall(3, cycle_edges)
has_cycle = any(d2[i][i] < 0 for i in range(3))
print("  dist 对角线：", [d2[i][i] for i in range(3)])
print("  是否存在负环：", has_cycle)

# ---- 与 Dijkstra 的对比：把无向图跑一遍 ----
print("\n== 对比 Dijkstra（同一张无向图）==")
import heapq


def dijkstra_all(graph, start):
    dist = {start: 0}
    heap = [(0, start)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, INF):
            continue
        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist.get(v, INF):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


UNDIRECTED = [(0, 1, 4), (0, 2, 3), (1, 2, 2), (1, 3, 2), (2, 3, 4)]
graph = {}
for u, v, w in UNDIRECTED:
    graph.setdefault(u, []).append((v, w))
    graph.setdefault(v, []).append((u, w))
fd, _ = floyd_warshall(4, [(u, v, w) for u, v, w in UNDIRECTED]
                       + [(v, u, w) for u, v, w in UNDIRECTED])
for start in range(4):
    dj = dijkstra_all(graph, start)
    fw = fd[start]
    same = all(dj.get(i, INF) == fw[i] for i in range(4))
    print(f"  起点 {NODES[start]}：Dijkstra {[dj.get(i, '∞') for i in range(4)]} "
          f"| Floyd {fw} | 一致={same}")

# ---- 复杂度与适用场景 ----
print("\n== 选择建议 ==")
for item in [
    "只要一个起点 → Dijkstra O((V+E)logV)",
    "要所有点对、图较小（几百点）→ Floyd O(V³)，代码最短",
    "有负权边 → Floyd 或 Bellman-Ford（Dijkstra 不行）",
    "图很大（几万点）且要全源 → 对每个点跑 Dijkstra 通常更快",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 打印“每对节点之间经过的中间节点”，验证路径还原。
# 2. 把不可达用 -1 输出（矩阵展示更友好）。
# 3. 用 Floyd 求“图的直径”（最长的最短路径）。
# 4. 思考：为什么 Floyd 的 k 循环必须放最外层？
