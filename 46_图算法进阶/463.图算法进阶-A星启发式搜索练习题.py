# ===== 第463课：图算法进阶-A*启发式搜索 =====
# 知识点：
#   - A*：Dijkstra + 启发函数 h(n)，优先扩展“g + h”最小的节点
#   - g：从起点到当前的实际代价；h：当前到终点的估计代价
#   - h 必须“可采纳”（不高估），才能保证找到最优解
#   - 启发式越准，扩展节点越少；h=0 就退化成 Dijkstra
#   - 典型场景：网格寻路（游戏/机器人）、地图导航
#   - 与第460课 Dijkstra 共用同一套松弛逻辑，只换了优先级
import heapq


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def neighbors(grid, node):
    r, c = node
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != "#":
            yield (nr, nc)


def astar(grid, start, goal, heuristic=manhattan):
    """返回 (path, cost, 扩展节点数)。"""
    counter = 0
    open_heap = [(heuristic(start, goal), 0, counter, start)]
    g_cost = {start: 0}
    parent = {}
    closed = set()
    expanded = 0

    while open_heap:
        f, g, _, node = heapq.heappop(open_heap)
        if node in closed:
            continue
        closed.add(node)
        expanded += 1

        if node == goal:
            path = [node]
            while path[-1] != start:
                path.append(parent[path[-1]])
            return list(reversed(path)), g, expanded

        for nxt in neighbors(grid, node):
            new_g = g + 1
            if new_g < g_cost.get(nxt, float("inf")):
                g_cost[nxt] = new_g
                parent[nxt] = node
                counter += 1
                heapq.heappush(open_heap, (new_g + heuristic(nxt, goal), new_g, counter, nxt))

    return None, None, expanded


# ---- 网格：S 起点，G 终点，# 障碍 ----
GRID = [
    "S........",
    ".##.##...",
    ".........",
    ".#.##.##.",
    "........G",
]
start, goal = (0, 0), (4, 8)

path, cost, expanded = astar(GRID, start, goal, manhattan)
print("== A*（曼哈顿启发）==")
print("  路径长度：", cost, "| 扩展节点：", expanded)
print("  路径：", path)

# 可视化路径
def render(grid, path):
    cells = [list(row) for row in grid]
    for r, c in path:
        if cells[r][c] == ".":
            cells[r][c] = "*"
    return "\n".join("".join(row) for row in cells)


print("\n" + render(GRID, path))

# ---- 对比：h=0 就是 Dijkstra ----
_, _, expanded_dijkstra = astar(GRID, start, goal, heuristic=lambda a, b: 0)
print("== 扩展节点对比 ==")
print(f"  A*：{expanded} 个 | Dijkstra（h=0）：{expanded_dijkstra} 个")
print("  启发式越准，搜索越聚焦")

# ---- 不同启发函数 ----
def euclidean(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


for name, h in (("曼哈顿", manhattan), ("欧氏", euclidean), ("零（Dijkstra）", lambda a, b: 0)):
    p, c, e = astar(GRID, start, goal, h)
    print(f"  {name:12s} 路径 {c} 步，扩展 {e} 个节点")

# ---- 启发式不可采纳的例子（会走弯路）----
def bad_heuristic(a, b):
    return manhattan(a, b) * 5          # 高估 → 不保证最优


p2, c2, e2 = astar(GRID, start, goal, bad_heuristic)
print("\n== 高估启发式 ==")
print(f"  路径 {c2} 步（最优 {cost} 步），扩展 {e2} 个")
print("  h 高估会破坏最优性保证：可能提前冲向终点而错过更短路径")

# ---- 应用注意 ----
print("\n== 使用要点 ==")
for item in [
    "网格四方向用曼哈顿，八方向用切比雪夫/欧氏",
    "启发式只需“不高估”，可以放大常数因子但别超过真实代价",
    "障碍多时 h 的剪枝效果最明显",
    "带权网格：g 累加边权，h 用最小边权 × 距离",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把四方向改成八方向（斜走代价 1.414），重跑 A*。
# 2. 给网格加“沼泽”代价（走一格代价 5），修改 g 的累加。
# 3. 实现 weighted A*（f = g + 1.5*h），观察速度与最优性的取舍。
# 4. 思考：地图导航里，h 为什么常用“直线距离/最高限速”？
