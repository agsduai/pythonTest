# ===== 第466课：图算法进阶-综合案例-物流路径规划 =====
# 知识点：
#   - 综合运用：Dijkstra（460）+ 最近邻多站路径 + MST（464）
#   - 场景：从仓库出发，依次配送 3 个城市，再返回，求较优路线
#   - 多站路径（TSP 简化）：每站选“当前最近未访问城市”（贪心）
#   - MST：评估“把所有城市连起来”的最低建设成本
#   - 真实系统还要考虑：时间窗、载重、实时路况、多点取送
import heapq

# ---------------- 路网：距离 + 时间（分钟）----------------
ROADS = [
    ("仓库", "北京", 30, 40),
    ("仓库", "天津", 120, 90),
    ("北京", "天津", 120, 75),
    ("北京", "石家庄", 280, 180),
    ("天津", "济南", 320, 200),
    ("石家庄", "郑州", 410, 260),
    ("济南", "郑州", 440, 280),
    ("北京", "济南", 430, 250),
]
CITIES = ["仓库", "北京", "天津", "石家庄", "济南", "郑州"]


def build_graph(roads, metric="time"):
    graph = {c: [] for c in CITIES}
    for u, v, distance, minutes in roads:
        w = minutes if metric == "time" else distance
        graph[u].append((v, w))
        graph[v].append((u, w))
    return graph


def dijkstra(graph, start):
    dist = {start: 0}
    prev = {}
    heap = [(0, start)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue
        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    return dist, prev


def path_to(prev, start, end):
    if end == start:
        return [start]
    if end not in prev:
        return []
    path = [end]
    while path[-1] != start:
        path.append(prev[path[-1]])
    return list(reversed(path))


# ---- 1. 单程最快路线 ----
time_graph = build_graph(ROADS, "time")
dist_t, prev_t = dijkstra(time_graph, "仓库")
print("== 仓库到各城市最快时间（分钟）==")
for city in CITIES[1:]:
    route = " → ".join(path_to(prev_t, "仓库", city))
    print(f"  {city:4s} {dist_t[city]:4d} 分钟 | {route}")

# ---- 2. 多站配送：最近邻贪心 ----
def nearest_neighbor_route(graph, start, stops, metric_name=""):
    unvisited = set(stops)
    route, total, current = [start], 0, start
    detail = []
    while unvisited:
        dist, prev = dijkstra(graph, current)
        nxt = min(unvisited, key=lambda c: dist.get(c, float("inf")))
        segment = path_to(prev, current, nxt)
        segment_time = dist[nxt]
        detail.append((current, nxt, segment_time, segment))
        total += segment_time
        route.extend(segment[1:])
        unvisited.remove(nxt)
        current = nxt
    # 返回仓库
    dist, prev = dijkstra(graph, current)
    back = path_to(prev, current, start)
    detail.append((current, start, dist[start], back))
    total += dist[start]
    route.extend(back[1:])
    print(f"\n== 最近邻配送路线（按{metric_name}）==")
    for u, v, t, seg in detail:
        print(f"  {u} → {v}: {t} 分钟（{' → '.join(seg)}）")
    print("  完整路线：", " → ".join(route))
    print("  总耗时：", total, "分钟")
    return route, total


stops = ["北京", "石家庄", "郑州"]
nearest_neighbor_route(time_graph, "仓库", stops, "时间")

# ---- 3. 与其他顺序对比：穷举全排列（只有 3 站）----
print("\n== 穷举对比（3 个站点的所有顺序）==")
import itertools

def route_cost(graph, start, order):
    total, current = 0, start
    for nxt in order + [start]:
        dist, _ = dijkstra(graph, current)
        total += dist[nxt]
        current = nxt
    return total

best_order, best_cost = None, float("inf")
for perm in itertools.permutations(stops):
    cost = route_cost(time_graph, "仓库", list(perm))
    print(f"  {perm}: {cost} 分钟")
    if cost < best_cost:
        best_order, best_cost = perm, cost
print(f"  最优顺序：{best_order}（{best_cost} 分钟）")
print("  说明：站点少可穷举；站点多时用启发式（遗传/模拟退火）")

# ---- 4. MST：所有城市互联的最低建设成本 ----
distance_graph = build_graph(ROADS, "distance")
edges = []
seen = set()
for u, v, distance, _ in ROADS:
    key = tuple(sorted((u, v)))
    if key not in seen:
        seen.add(key)
        edges.append((distance, u, v))
edges.sort()

parent = {c: c for c in CITIES}

def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

def union(a, b):
    ra, rb = find(a), find(b)
    if ra == rb:
        return False
    parent[rb] = ra
    return True

print("\n== MST：光缆/道路最低建设成本 ==")
total_distance, chosen = 0, []
for w, u, v in edges:
    if union(u, v):
        chosen.append((u, v, w))
        total_distance += w
        if len(chosen) == len(CITIES) - 1:
            break
for u, v, w in chosen:
    print(f"  {u} — {v}: {w} km")
print("  总成本：", total_distance, "km")

# ---- 5. 业务输出 ----
print("\n== 规划建议 ==")
for item in [
    "日常配送：按最近邻顺序 北京 → 石家庄 → 郑州，回程走高速",
    "旺季：以 MST 为主干道，避免重复修路",
    "实时调整：路况变化时重跑 Dijkstra（边权换成实时耗时）",
    "扩展：加入时间窗后，问题变成 VRPTW，需要专门求解器",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给最近邻加“返回起点才结束”的约束（本课已实现），对比穷举验证是否最优。
# 2. 把时间换成“距离 + 拥堵系数”，重新规划路线。
# 3. 增加一个城市和两条路，观察 MST 与配送路线的变化。
# 4. 思考：为什么物流公司不总是走“最短路径”？（时间窗、载重、限行）
