# ===== 第828课：网络流与图匹配-二分图最大匹配 =====
# 知识点：
#   - 二分图：节点分为左右两组，所有边跨越两组
#   - 最大匹配：选最多条边使得每个节点最多被一条边覆盖
#   - 增广路径：从未匹配的左节点出发，交替走未匹配/已匹配边，终点是未匹配右节点
#   - 匈牙利算法 Hungarian：反复找增广路径，O(VE)；也叫 Kuhn-Munkres 简化版
#   - König 定理：最大匹配数 = 最小顶点覆盖数
#   - 应用：任务分配、课程排课、带权版本是匈牙利/KM 算法
# 依赖：无（标准库）
from collections import defaultdict, deque


class BipartiteGraph:
    def __init__(self):
        self.adj = defaultdict(set)      # 左节点 -> 右节点集合
        self.left = set()
        self.right = set()

    def add_edge(self, u, v):
        self.adj[u].add(v)
        self.left.add(u); self.right.add(v)


def hungarian(graph):
    """匈牙利算法（Kuhn）：贪心 + 增广路径。"""
    match_right = {}                     # 右节点 -> 左节点
    match_left = {}                      # 左节点 -> 右节点

    def try_augment(u, visited):
        """DFS 找增广路径。"""
        for v in graph.adj[u]:
            if v not in visited:
                visited.add(v)
                # v 未匹配 或 v 的当前匹配者能找到新的匹配
                if v not in match_right or try_augment(match_right[v], visited):
                    match_right[v] = u
                    match_left[u] = v
                    return True
        return False

    matching_size = 0
    for u in sorted(graph.left):
        visited = set()
        if try_augment(u, visited):
            matching_size += 1
    return match_left, match_right, matching_size


def brute_force_max_matching(graph):
    """暴力枚举验证（小规模）。"""
    left = sorted(graph.left)
    right = sorted(graph.right)
    best = 0
    for perm in _permutations(right, len(left)):
        count = sum(1 for i, u in enumerate(left)
                    if i < len(perm) and perm[i] in graph.adj[u])
        best = max(best, count)
    return best


def _permutations(items, r):
    from itertools import permutations
    return permutations(items, min(r, len(items)))


print("== 构建二分图 ==")
bg = BipartiteGraph()
# 任务分配：员工 -> 可执行的任务
edges = [("A", "T1"), ("A", "T2"), ("B", "T1"), ("B", "T3"),
         ("C", "T2"), ("C", "T3"), ("C", "T4"), ("D", "T4"),
         ("D", "T5"), ("E", "T3")]
for u, v in edges:
    bg.add_edge(u, v)
print(f"  左侧(员工): {sorted(bg.left)}")
print(f"  右侧(任务): {sorted(bg.right)}")
print(f"  边: {edges}")

print("\n== 匈牙利算法求最大匹配 ==")
match_l, match_r, size = hungarian(bg)
print(f"  最大匹配数 = {size}")
print("  匹配:")
for u, v in sorted(match_l.items()):
    print(f"    {u} -> {v}")

print("\n== 暴力验证 ==")
if len(bg.left) <= 6:
    brute = brute_force_max_matching(bg)
    print(f"  暴力最大匹配 = {brute}  一致={brute == size}")

print("\n== 匈牙利算法的增广路径过程 ==")
bg2 = BipartiteGraph()
for u, v in [("A","1"),("A","2"),("B","1"),("C","2"),("C","3")]:
    bg2.add_edge(u, v)
m_l, m_r, sz = hungarian(bg2)
print(f"  A-1, A-2, B-1, C-2, C-3")
print(f"  匹配结果: {m_l}  大小={sz}")
print("  步骤:")
print("    A → 1 (直接匹配)")
print("    B → 1 被占 → 增广: B→1→A→2 → A 改配 2, B 配 1")
print("    C → 2 被占 → 增广: C→2→A→... 但 A 已配 2...")

print("\n== König 定理验证 ==")
# 最大匹配 = 最小顶点覆盖
def min_vertex_cover(graph, match_l, match_r):
    """从匈牙利算法的匹配结果导出最小顶点覆盖。"""
    # 未匹配的左节点出发，标记 alternating path 可达的节点
    unmatched_left = graph.left - set(match_l.keys())
    visited_left, visited_right = set(), set()
    stack = list(unmatched_left)
    while stack:
        u = stack.pop()
        if u in visited_left: continue
        visited_left.add(u)
        for v in graph.adj[u]:
            if match_l.get(u) != v:         # 非匹配边
                if v not in visited_right:
                    visited_right.add(v)
                    if v in match_r:
                        stack.append(match_r[v])
    # 最小覆盖 = 未访问左节点 + 已访问右节点
    cover = (graph.left - visited_left) | visited_right
    return cover

cover = min_vertex_cover(bg, match_l, match_r)
print(f"  最大匹配 = {size}")
print(f"  最小顶点覆盖 = {sorted(cover)}  大小={len(cover)}")
print(f"  König 定理: {len(cover) == size}")

print("\n== 无解情况：更多左侧节点 ==")
bg3 = BipartiteGraph()
for u, v in [("A","1"),("B","1"),("C","1"),("D","1")]:
    bg3.add_edge(u, v)
m3, _, sz3 = hungarian(bg3)
print(f"  4 个左节点只连 1 个右节点: 最大匹配={sz3}（受限于右侧）")

print("\n== 复杂度与应用 ==")
for line in (
    "  匈牙利算法 O(VE)：每个左节点最多做一次 DFS 增广",
    "  Hopcroft-Karp O(E√V)：同时找多条增广路径，更快",
    "  应用：任务分配、课程排课、广告位分配、基因序列匹配",
):
    print(" ", line)

print("\n== 带权匹配（KM 算法概念） ==")
for line in [
    "  每条边有权重，找权重和最大的完美匹配",
    "  匈牙利算法扩展版（Kuhn-Munkres），O(n³)",
    "  scipy.optimize.linear_sum_assignment 是工业实现",
    "  无权版本用本课的匈牙利算法即可",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Hopcroft-Karp 算法（BFS 分层 + DFS 多路增广），对比效率。
# 2. 把二分图匹配建模为最大流问题（超源超汇 + 容量 1 边），用第827课求解。
# 3. 实现带权二分图的 KM 算法（匈牙利算法扩展版）。
# 4. 思考：为什么增广路径法能保证「每加一条路径，匹配数恰增 1」？
