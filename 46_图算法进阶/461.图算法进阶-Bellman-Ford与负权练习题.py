# ===== 第461课：图算法进阶-Bellman-Ford与负权 =====
# 知识点：
#   - Bellman-Ford：允许负权边的单源最短路
#   - 核心：对所有边做 V-1 轮松弛；第 V 轮还能松弛 → 存在负权环
#   - 复杂度 O(VE)，比 Dijkstra 慢，但能处理负权/检测负环
#   - 负权环：绕一圈总成本下降，最短路径不存在（-∞）
#   - 应用：套利检测、成本差分约束、带补贴的路径规划
#   - 与第460课 Dijkstra 的分工要记牢
from collections import defaultdict


def bellman_ford(n_nodes: int, edges: list[tuple], start: int):
    """返回 (dist, has_negative_cycle)。节点编号 0..n_nodes-1。"""
    INF = float("inf")
    dist = [INF] * n_nodes
    dist[start] = 0.0

    for i in range(n_nodes - 1):
        updated = False
        for u, v, w in edges:
            if dist[u] != INF and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                updated = True
        if not updated:                    # 提前收敛
            print(f"  第 {i + 1} 轮已无更新，提前结束")
            break

    # 第 V 轮：若还能松弛，说明有负权环
    for u, v, w in edges:
        if dist[u] != INF and dist[u] + w < dist[v]:
            return dist, True
    return dist, False


# ---- 例 1：含负权边但无负环 ----
print("== 例 1：负权边（无负环）==")
# 0→1 成本 4；0→2 成本 5；1→2 成本 -3（走 0→1→2 更便宜）
EDGES = [(0, 1, 4), (0, 2, 5), (1, 2, -3), (2, 3, 2)]
dist, negative = bellman_ford(4, EDGES, 0)
print("  最短距离：", dist)
print("  是否存在负环：", negative)
print("  说明：0→2 经 1 中转 = 4-3 = 1，比直接 5 更短")

print("\n== Dijkstra 在同样输入下会怎样？==")
print("  Dijkstra 假设“先弹出的就是最终最短”，负权会打破这个前提")
print("  本例中 0 弹出时把 2 标成 5；之后再发现 1 的路径为 1，已无法回头修正")

# ---- 例 2：负权环检测 ----
print("\n== 例 2：负权环 ==")
NEG_CYCLE = [(0, 1, 1), (1, 2, -5), (2, 1, 1), (2, 3, 1)]
dist2, negative2 = bellman_ford(4, NEG_CYCLE, 0)
print("  是否存在负环：", negative2)
print("  含义：1→2→1 每绕一圈成本 -4，最短路径为 -∞")

# ---- 例 3：套利检测（汇率的负对数）----
print("\n== 例 3：汇率套利检测 ==")
# 货币 0=CNY, 1=USD, 2=JPY
# 汇率：1 CNY = 0.14 USD；1 USD = 110 JPY；1 JPY = 0.07 CNY
# 走一圈：0.14 * 110 * 0.07 = 1.078 > 1 → 存在套利
rates = {(0, 1): 0.14, (1, 2): 110.0, (2, 0): 0.07}
import math
edges = []
for (u, v), rate in rates.items():
    edges.append((u, v, -math.log(rate)))     # 乘积变求和，>1 变成负环
dist3, negative3 = bellman_ford(3, edges, 0)
print("  是否存在套利机会：", negative3)
print("  （负环 = 绕一圈汇率乘积 >1，可低买高卖）")

# ---- 与 Dijkstra 的选择 ----
print("\n== 算法选择 ==")
print("  边权全非负 → Dijkstra（快）")
print("  有负权边   → Bellman-Ford（慢但正确）")
print("  需要检测负环/套利 → Bellman-Ford 或 SPFA")
print("  全源最短路 → Floyd-Warshall（第462课）")

# ---- 路径还原（无负环时）----
print("\n== 路径还原 ==")
def bellman_ford_path(n, edges, start, end):
    dist = [float("inf")] * n
    prev = [None] * n
    dist[start] = 0
    for _ in range(n - 1):
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
    if dist[end] == float("inf"):
        return None, None
    path, cur = [], end
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    return list(reversed(path)), dist[end]

path, cost = bellman_ford_path(4, EDGES, 0, 3)
print("  0 → 3：", path, "成本", cost)

# ===== 练习题 =====
# 1. 实现 SPFA（队列优化的 Bellman-Ford），对比运行轮数。
# 2. 给套利例子增加一条边，构造“无套利”的情况。
# 3. 用 Bellman-Ford 解差分约束（x_v <= x_u + w）。
# 4. 思考：为什么负权环会让“最短路径”这个概念失效？
