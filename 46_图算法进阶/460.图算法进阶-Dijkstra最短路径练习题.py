# ===== 第460课：图算法进阶-Dijkstra最短路径 =====
# 知识点：
#   - Dijkstra：单源最短路径，要求边权非负
#   - 贪心 + 优先队列：每次弹出当前最近的节点，松弛它的邻居
#   - 复杂度：O((V+E) log V)（用堆）
#   - prev 数组记录前驱，用于还原完整路径
#   - 与第331课堆、第334课贪心的结合
#   - 局限：负权边会失效（下一课 Bellman-Ford）
import heapq


def dijkstra(graph: dict, start: str):
    """返回 (dist, prev)：各点最短距离与前驱节点。"""
    dist = {start: 0.0}
    prev = {}
    heap = [(0.0, start)]
    visited = set()

    while heap:
        d, node = heapq.heappop(heap)
        if node in visited:                # 旧条目：已经用更短距离处理过
            continue
        visited.add(node)

        for neighbor, weight in graph.get(node, []):
            if weight < 0:
                raise ValueError("Dijkstra 不支持负权边")
            new_dist = d + weight
            if new_dist < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_dist
                prev[neighbor] = node
                heapq.heappush(heap, (new_dist, neighbor))

    return dist, prev


def build_path(prev: dict, start: str, end: str) -> list[str]:
    if end not in prev and end != start:
        return []
    path = [end]
    while path[-1] != start:
        path.append(prev[path[-1]])
    return list(reversed(path))


# ---- 城市路网（无向带权）----
EDGES = [
    ("北京", "天津", 120), ("北京", "石家庄", 280),
    ("天津", "济南", 320), ("石家庄", "郑州", 410),
    ("济南", "郑州", 440), ("郑州", "武汉", 520),
    ("济南", "青岛", 360), ("青岛", "上海", 780),
    ("武汉", "上海", 690),
]
graph = {}
for u, v, w in EDGES:
    graph.setdefault(u, []).append((v, w))
    graph.setdefault(v, []).append((u, w))

print("== 从北京出发的最短距离 ==")
dist, prev = dijkstra(graph, "北京")
for city in sorted(dist, key=lambda c: dist[c]):
    print(f"  {city:5s} {dist[city]:6.0f} km")

print("\n== 具体路径 ==")
for target in ("上海", "武汉", "青岛"):
    path = build_path(prev, "北京", target)
    print(f"  北京 → {target}：{' → '.join(path)}（{dist[target]:.0f} km）")

# ---- 与 BFS 的区别：BFS 只看跳数，Dijkstra 看权重 ----
from collections import deque

def bfs_hops(graph, start):
    hops = {start: 0}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for nxt, _ in graph[node]:
            if nxt not in hops:
                hops[nxt] = hops[node] + 1
                queue.append(nxt)
    return hops


hops = bfs_hops(graph, "北京")
print("\n== BFS 跳数 vs Dijkstra 距离 ==")
for city in ("上海", "武汉", "青岛"):
    print(f"  {city}: BFS {hops[city]} 跳 | 最短 {dist[city]:.0f} km")

# ---- 有向 + 权重变化的场景：时间最短 ----
print("\n== 按“时间”而非距离 ==")
TIME_EDGES = [
    ("北京", "天津", 30), ("北京", "石家庄", 70),
    ("天津", "济南", 90), ("石家庄", "郑州", 120),
    ("济南", "郑州", 100), ("郑州", "武汉", 150),
]
tg = {}
for u, v, t in TIME_EDGES:
    tg.setdefault(u, []).append((v, t))
    tg.setdefault(v, []).append((u, t))
t_dist, t_prev = dijkstra(tg, "北京")
print("  北京 → 武汉 最快：", " → ".join(build_path(t_prev, "北京", "武汉")),
      f"（{t_dist['武汉']} 分钟）")

# ---- 常见坑 ----
print("\n== 注意事项 ==")
for item in [
    "负权边 → 换 Bellman-Ford（第461课）",
    "堆里会有旧距离条目 → 用 visited 跳过",
    "图不连通 → 不可达节点不在 dist 里",
    "只要距离不要路径 → 可以不存 prev",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把图换成有向图，验证单向道路的最短路径。
# 2. 实现多源 Dijkstra（初始堆放入多个起点，距离为 0）。
# 3. 记录“经过的边数”，用于比较“最快”和“最少换乘”。
# 4. 思考：为什么 Dijkstra 一旦弹出节点就能确定它的最短距离？
