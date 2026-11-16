# ===== 第464课：图算法进阶-最小生成树 =====
# 知识点：
#   - 最小生成树（MST）：连接所有节点、总权重最小的树（N 个点 N-1 条边）
#   - Kruskal：边按权重排序，用并查集（第420课）判断“加这条边会不会成环”
#   - Prim：从一个点出发，每次用最小堆选“连接已选集合与外部”的最短边
#   - 两者结果总权重相同（MST 不唯一时边可能不同）
#   - 应用：铺网线/修路/管道、聚类、近似旅行商
import heapq


# ---------------- 并查集 ----------------
class UnionFind:
    def __init__(self, nodes):
        self.parent = {n: n for n in nodes}
        self.rank = {n: 0 for n in nodes}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]   # 路径压缩
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def kruskal(nodes, edges):
    """edges: [(w, u, v), ...]。返回 (选中边, 总权重)。"""
    uf = UnionFind(nodes)
    chosen, total = [], 0
    for w, u, v in sorted(edges):
        if uf.union(u, v):
            chosen.append((u, v, w))
            total += w
            if len(chosen) == len(nodes) - 1:
                break
    return chosen, total


def prim(nodes, edges, start=None):
    """从 start 出发，用最小堆扩展。"""
    start = start or nodes[0]
    graph = {n: [] for n in nodes}
    for w, u, v in edges:
        graph[u].append((w, v))
        graph[v].append((w, u))

    visited = {start}
    heap = [(w, start, v) for w, v in graph[start]]
    heapq.heapify(heap)
    chosen, total = [], 0

    while heap and len(visited) < len(nodes):
        w, u, v = heapq.heappop(heap)
        if v in visited:
            continue
        visited.add(v)
        chosen.append((u, v, w))
        total += w
        for nw, nxt in graph[v]:
            if nxt not in visited:
                heapq.heappush(heap, (nw, v, nxt))

    return chosen, total


# ---- 城市光纤铺设：5 个城市 ----
NODES = ["北京", "天津", "石家庄", "济南", "郑州"]
EDGES = [
    (120, "北京", "天津"),
    (280, "北京", "石家庄"),
    (320, "天津", "济南"),
    (410, "石家庄", "郑州"),
    (440, "济南", "郑州"),
    (260, "石家庄", "济南"),
    (560, "北京", "济南"),
]
# 注意：边是 (权重, u, v)，便于直接排序

k_edges, k_total = kruskal(NODES, EDGES)
p_edges, p_total = prim(NODES, EDGES, start="北京")

print("== Kruskal ==")
for u, v, w in k_edges:
    print(f"  {u} — {v}: {w} km")
print("  总长度：", k_total, "km")

print("\n== Prim（从北京出发）==")
for u, v, w in p_edges:
    print(f"  {u} — {v}: {w} km")
print("  总长度：", p_total, "km")

print("\n== 一致性校验 ==")
print("  两种算法总权重相同：", k_total == p_total)
print("  边数 = 节点数 - 1：", len(k_edges) == len(NODES) - 1, len(p_edges) == len(NODES) - 1)

# ---- 如果城市不连通：MST 不存在 ----
print("\n== 不连通的情况 ==")
DISCONNECTED = [
    (100, "A", "B"), (200, "B", "C"),
    (150, "D", "E"),                       # D/E 与 A/B/C 不连通
]
chosen, total = kruskal(["A", "B", "C", "D", "E"], DISCONNECTED)
print(f"  选中 {len(chosen)} 条边（应为 4 条），总权重 {total}")
print("  结论：图不连通时得到的是“最小生成森林”，不是一棵树")

# ---- 应用：聚类（切掉最长的边）----
print("\n== 用 MST 做聚类 ==")
# 把 5 个城市切成 2 组：去掉 MST 里最长的一条边
u, v, w = max(k_edges, key=lambda e: e[2])
remaining = [e for e in k_edges if (e[0], e[1]) != (u, v)]
print(f"  去掉最长边 {u}-{v}（{w} km）后分成两组：")
print("  剩余边：", remaining)
print("  这就是单链接层次聚类的最小版本")

# ---- 复杂度 ----
print("\n== 复杂度 ==")
print("  Kruskal：O(E log E)（排序）+ 并查集近似 O(1)")
print("  Prim（堆）：O(E log V)")
print("  稀疏图两者都行；稠密图 Prim 的邻接矩阵版更简单")

# ===== 练习题 =====
# 1. 给 Kruskal 增加“输出被跳过的边及原因（会成环）”。
# 2. 用 MST 结果计算“任意两城连通所需的最短光缆总长”（已给出）。
# 3. 改成有向图会怎样？为什么 MST 只定义在无向图上？
# 4. 思考：MST 与第460课的最短路径树有什么本质区别？
