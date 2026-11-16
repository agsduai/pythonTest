# ===== 第830课：网络流与图匹配-最小费用最大流 =====
# 知识点：
#   - 最小费用最大流 Min-Cost Max-Flow：在最大流前提下，最小化费用
#   - 每条边有 (容量, 费用)；SPFA/Bellman-Ford 找最短增广路径（费用最小）
#   - 消除负环：初始流为 0 时无负环（费用≥0 的边），SPFA 可用
#   - 应用：运输成本优化、任务分配（带成本）、网络路由
#   - 与第78章组合优化的对比：LP 可解连续问题，MCMF 解离散整数流
# 依赖：无（标准库）
from collections import defaultdict, deque
import math

INF = math.inf


class MCMF:
    """最小费用最大流（SPFA 版本）。"""

    def __init__(self):
        self.graph = defaultdict(list)   # u -> [(v, cap, cost, edge_index)]
        self.edges = []                  # [(u, v, cap, cost)]

    def add_edge(self, u, v, cap, cost):
        """加正向边和反向边（反向容量 0，费用为负）。"""
        self.graph[u].append((v, cap, cost, len(self.edges)))
        self.graph[v].append((u, 0, -cost, len(self.edges)+1))
        self.edges.append((u, v, cap, cost))
        self.edges.append((v, u, 0, -cost))

    def spfa(self, source, sink):
        """SPFA 找费用最小的增广路径，返回 (dist, parent_edge)。"""
        dist = defaultdict(lambda: INF)
        in_queue = defaultdict(bool)
        parent_edge = {}
        dist[source] = 0
        q = deque([source])
        in_queue[source] = True
        while q:
            u = q.popleft()
            in_queue[u] = False
            for v, cap, cost, ei in self.graph[u]:
                # 关键：检查残余容量（self.edges[ei][2]），不是原始容量
                residual_cap = self.edges[ei][2]
                if residual_cap > 0 and dist[u] + cost < dist[v]:
                    dist[v] = dist[u] + cost
                    parent_edge[v] = (u, ei)
                    if not in_queue[v]:
                        q.append(v)
                        in_queue[v] = True
        return dist, parent_edge

    def solve(self, source, sink):
        """返回 (最大流, 最小费用, 每条边的流量)。"""
        total_flow, total_cost = 0, 0
        flow_per_edge = [0] * len(self.edges)

        while True:
            dist, parent_edge = self.spfa(source, sink)
            if dist[sink] == INF:
                break
            # 沿路径找瓶颈容量
            bottleneck = INF
            cur = sink
            while cur != source:
                u, ei = parent_edge[cur]
                bottleneck = min(bottleneck, self.edges[ei][2])  # cap
                cur = u
            # 更新流量和费用
            cur = sink
            while cur != source:
                u, ei = parent_edge[cur]
                self.edges[ei] = (u, self.edges[ei][1],
                                  self.edges[ei][2] - bottleneck, self.edges[ei][3])
                rev = ei ^ 1
                self.edges[rev] = (self.edges[rev][0], self.edges[rev][1],
                                   self.edges[rev][2] + bottleneck, self.edges[rev][3])
                flow_per_edge[ei] += bottleneck
                cur = u
            total_flow += bottleneck
            total_cost += bottleneck * dist[sink]
        return total_flow, total_cost, flow_per_edge


print("== 基础示例：运输问题 ==")
# 2 个仓库 -> 3 个商店，求最小运输费用
# 仓库 A(供 3), B(供 3) -> 商店 X(需 2), Y(需 2), Z(需 2)
mcmf = MCMF()
mcmf.add_edge("S", "A", 3, 0)     # 源->仓库A 容量3
mcmf.add_edge("S", "B", 3, 0)     # 源->仓库B 容量3
mcmf.add_edge("A", "X", 3, 4)     # A->X 单价4
mcmf.add_edge("A", "Y", 3, 2)     # A->Y 单价2
mcmf.add_edge("B", "X", 3, 5)     # B->X 单价5
mcmf.add_edge("B", "Y", 3, 1)     # B->Y 单价1
mcmf.add_edge("B", "Z", 3, 3)     # B->Z 单价3
mcmf.add_edge("X", "T", 2, 0)     # X->汇 容量2
mcmf.add_edge("Y", "T", 2, 0)
mcmf.add_edge("Z", "T", 2, 0)

flow, cost, fe = mcmf.solve("S", "T")
print(f"  最大流 = {flow}  最小费用 = {cost}")
print("  各边流量:")
for i, (u, v, cap, cst) in enumerate(mcmf.edges):
    if cap > 0 and cst > 0 and fe[i] > 0:
        print(f"    {u}->{v}: flow={fe[i]}/{cap} cost/unit={cst}")

print("\n== 与纯最大流的对比 ==")
# 同一网络但所有费用 = 0（纯最大流）
mcmf_zero = MCMF()
mcmf_zero.add_edge("S", "A", 3, 0)
mcmf_zero.add_edge("S", "B", 3, 0)
mcmf_zero.add_edge("A", "X", 3, 0)
mcmf_zero.add_edge("A", "Y", 3, 0)
mcmf_zero.add_edge("B", "X", 3, 0)
mcmf_zero.add_edge("B", "Y", 3, 0)
mcmf_zero.add_edge("B", "Z", 3, 0)
mcmf_zero.add_edge("X", "T", 2, 0)
mcmf_zero.add_edge("Y", "T", 2, 0)
mcmf_zero.add_edge("Z", "T", 2, 0)
f0, c0, _ = mcmf_zero.solve("S", "T")
print(f"  最大流={f0}（费用=0 时最小费用=0）")
print(f"  最小费用问题的最大流 = {flow} = 最大流 ✓" if flow == f0 else "异常")

print("\n== 复杂度与应用 ==")
for line in (
    "  SPFA 增广: O(F·VE) 其中 F 为最大流量（逐单位增广慢）",
    "  更快: Dijkstra + 势函数（Johnson 重赋权），O(F·E log V)",
    "  应用: 运输优化、任务分配、网络路由、供应链管理",
):
    print(" ", line)

print("\n== 与线性规划 ==")
for line in [
    "  最小费用流是 LP 的特例（约束矩阵是全幺模的，LP 解自动为整数）",
    "  LP 可用单纯形法（第78章思路的扩展），MCMF 用图算法更快",
    "  多商品流（多种货物同时运输）不再是 MCMF，需要 LP 或列生成",
]:
    print("  -", line)

print("\n== 工程要点 ==")
for line in [
    "  SPFA 可能退化到 O(VE)，用 Dijkstra + 势函数保证 O(E log V) 每轮",
    "  大规模问题用网络单纯形法（network simplex）",
    "  负费用边需要初始消圈或用势函数处理",
    "  生产用 OR-Tools / LEMON 库，本课是原理版",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现带「下界」的费用流：每条边有 flow ≥ lower_bound 约束。
# 2. 用 MCMF 解「任务分配」问题：n 个人 m 个任务，各有成本，求最小成本分配。
# 3. 实现 Dijkstra + 势函数版本，对比 SPFA 的效率。
# 4. 思考：为什么 MCMF 可以用「逐单位增广」贪心，而 LP 需要更复杂的方法？
