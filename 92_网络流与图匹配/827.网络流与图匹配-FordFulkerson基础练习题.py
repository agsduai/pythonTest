# ===== 第827课：网络流与图匹配-FordFulkerson基础 =====
# 知识点：
#   - 流网络：有向图，每条边有容量 capacity(u,v) ≤ cap，流量 flow(u,v) ≤ cap
#   - 流守恒：除源汇外，流入 = 流出；源净流出 = 汇净流入 = 最大流值
#   - Ford-Fulkerson：反复找增广路径（s→t 的残余容量>0 路径），累加流量
#   - 残余容量 residual = capacity - flow + 反向边 flow
#   - 用 BFS 找增广路径 = Edmonds-Karp，O(VE²)；DFS 版不保证多项式
#   - 最大流最小割定理：最大流 = 最小割的容量
# 依赖：无（标准库）
from collections import defaultdict, deque


class FlowNetwork:
    def __init__(self):
        self.graph = defaultdict(dict)      # u -> {v: capacity}
        self.nodes = set()

    def add_edge(self, u, v, cap):
        self.graph[u][v] = cap
        self.graph[v].setdefault(u, 0)      # 反向边容量 0
        self.nodes.add(u); self.nodes.add(v)

    def bfs_find_path(self, source, sink, residual):
        """BFS 找增广路径，返回路径或 None。"""
        parent = {source: None}
        q = deque([source])
        while q:
            u = q.popleft()
            for v in self.graph[u]:
                if v not in parent and residual.get((u, v), 0) > 0:
                    parent[v] = u
                    if v == sink:
                        # 回溯路径
                        path = []
                        cur = v
                        while cur is not None:
                            path.append(cur)
                            cur = parent[cur]
                        path.reverse()
                        return path
                    q.append(v)
        return None

    def edmonds_karp(self, source, sink):
        """Edmonds-Karp：BFS 增广的 Ford-Fulkerson，O(VE²)。"""
        residual = {}
        for u in self.graph:
            for v, cap in self.graph[u].items():
                residual[(u, v)] = cap
                residual.setdefault((v, u), residual.get((v, u), 0))
        max_flow = 0
        augmentations = 0
        while True:
            path = self.bfs_find_path(source, sink, residual)
            if path is None:
                break
            # 找路径上的最小残余容量
            bottleneck = math.inf
            for i in range(len(path)-1):
                u, v = path[i], path[i+1]
                bottleneck = min(bottleneck, residual[(u, v)])
            # 更新残余图
            for i in range(len(path)-1):
                u, v = path[i], path[i+1]
                residual[(u, v)] -= bottleneck
                residual[(v, u)] = residual.get((v, u), 0) + bottleneck
            max_flow += bottleneck
            augmentations += 1
        return max_flow, augmentations, residual

    def min_cut(self, residual, source):
        """最小割：残余图中从 source 可达的节点集合。"""
        visited = {source}
        q = deque([source])
        while q:
            u = q.popleft()
            for v in self.graph[u]:
                if v not in visited and residual.get((u, v), 0) > 0:
                    visited.add(v); q.append(v)
        return visited


import math

print("== 构建流网络 ==")
net = FlowNetwork()
net.add_edge("S", "A", 10)
net.add_edge("S", "B", 5)
net.add_edge("A", "B", 4)
net.add_edge("A", "C", 8)
net.add_edge("B", "C", 6)
net.add_edge("C", "T", 10)
net.add_edge("B", "T", 5)

print("  边:")
for u in sorted(net.graph):
    for v, cap in sorted(net.graph[u].items()):
        if cap > 0:
            print(f"    {u} -> {v}: cap={cap}")

print("\n== Edmonds-Karp 求最大流 ==")
flow, augs, residual = net.edmonds_karp("S", "T")
print(f"  最大流 = {flow}")
print(f"  增广次数 = {augs}")

print("\n== 各边流量 ==")
for (u, v), r in sorted(residual.items()):
    cap = net.graph[u].get(v, 0)
    if cap > 0:
        fl = cap - r
        print(f"    {u}->{v}: flow={fl}/{cap}")

print("\n== 最小割 ==")
S_side = net.min_cut(residual, "S")
T_side = net.nodes - S_side
print(f"  S 侧: {sorted(S_side)}")
print(f"  T 侧: {sorted(T_side)}")
cut_edges = [(u, v) for u in S_side for v in net.graph[u]
             if v in T_side and net.graph[u][v] > 0]
cut_cap = sum(net.graph[u][v] for u, v in cut_edges)
print(f"  割边: {cut_edges}")
print(f"  割容量 = {cut_cap}  == 最大流 = {flow}  {cut_cap == flow}")

print("\n== 另一个网络 ==")
net2 = FlowNetwork()
net2.add_edge("S", "A", 3)
net2.add_edge("S", "B", 3)
net2.add_edge("A", "B", 2)
net2.add_edge("A", "T", 2)
net2.add_edge("B", "T", 2)
f2, a2, r2 = net2.edmonds_karp("S", "T")
print(f"  最大流 = {f2}  增广 {a2} 次")

print("\n== 复杂度 ==")
for line in (
    "  Ford-Fulkerson (DFS): O(E · max_flow) — 整数容量时终止但可能很慢",
    "  Edmonds-Karp (BFS):  O(VE²) — 增广路径长度单调递增",
    "  Dinic (分层+阻塞流): O(V²E) — 实践中最快的最大流算法之一",
    "  Push-Relabel:        O(V³) — 理论更优，实现更复杂",
):
    print(" ", line)

print("\n== 应用 ==")
for line in [
    "  网络：带宽分配、CDN 负载均衡",
    "  运输：最大运输量、最小运输成本",
    "  图像分割：把像素分为前景/背景（Graph Cut）",
    "  匹配：二分图最大匹配（第831课）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现DFS版Ford-Fulkerson，构造一个使其增广路径很多的反例。
# 2. 用最大流求二分图最大匹配（构造超源超汇）。
# 3. 实现Dinic算法（BFS分层 + DFS阻塞流），对比与Edmonds-Karp的效率。
# 4. 思考：为什么「最小割容量 = 最大流」？（提示：割是流的上界，最大流达到上界）
