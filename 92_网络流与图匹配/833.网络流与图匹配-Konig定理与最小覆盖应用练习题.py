# ===== 第833课：网络流与图匹配-König定理与最小覆盖应用 =====
# 知识点：
#   - König 定理：二分图最大匹配数 = 最小顶点覆盖数（左右两侧取法见第828课）
#   - 最小顶点覆盖：选最少的节点覆盖所有边（每条边至少一个端点在覆盖集中）
#   - 一般图的最小顶点覆盖是 NP 难的，但二分图有多项式算法
#   - 最大独立集 = 总节点数 - 最小顶点覆盖（在二分图中）
#   - 应用：排课冲突（最少教室）、安全监控（最少摄像头覆盖所有走廊）、
#          数据库索引（最少索引覆盖所有查询）
#   - 与 Dilworth 定理：最小链覆盖 = 最大反链（偏序集的对偶性）
# 依赖：无（标准库）
from collections import defaultdict, deque


class BipartiteGraph:
    def __init__(self):
        self.adj = defaultdict(set)
        self.left = set()
        self.right = set()

    def add_edge(self, u, v):
        self.adj[u].add(v)
        self.left.add(u); self.right.add(v)


def hungarian(graph):
    match_r = {}
    match_l = {}

    def augment(u, visited):
        for v in graph.adj[u]:
            if v not in visited:
                visited.add(v)
                if v not in match_r or augment(match_r[v], visited):
                    match_r[v] = u; match_l[u] = v
                    return True
        return False

    size = 0
    for u in sorted(graph.left):
        visited = set()
        if augment(u, visited):
            size += 1
    return match_l, match_r, size


def min_vertex_cover(graph, match_l, match_r):
    """从最大匹配导出最小顶点覆盖（König 定理）。"""
    # 1) 找未匹配的左节点
    unmatched_left = graph.left - set(match_l.keys())
    # 2) 从未匹配左节点出发，沿「非匹配边（左→右）+ 匹配边（右→左）」标记
    visited_left, visited_right = set(), set()
    stack = list(unmatched_left)
    while stack:
        u = stack.pop()
        if u in visited_left: continue
        visited_left.add(u)
        for v in graph.adj[u]:
            if match_l.get(u) != v:              # 非匹配边
                if v not in visited_right:
                    visited_right.add(v)
                    if v in match_r:              # 已匹配的右节点
                        stack.append(match_r[v])
    # 3) 最小覆盖 = 未被标记的左节点 + 被标记的右节点
    cover = (graph.left - visited_left) | visited_right
    return cover


def is_valid_cover(graph, cover):
    """校验：每条边至少有一个端点在覆盖集中。"""
    for u in graph.left:
        for v in graph.adj[u]:
            if u not in cover and v not in cover:
                return False, (u, v)
    return True, None


print("== 场景：最少教室数（König 定理应用） ==")
# 课程时间表：每门课是一个「时间段」，每间教室一个「时间冲突」
# 建模：左=课程开始时间，右=课程结束时间，边=占用关系
# 最少教室 = 最大同时进行的课程数 = 二分图最大匹配（用区间图转二分图的性质）

# 简化：直接用课程冲突图（区间图）
class_intervals = [
    ("Math", (9, 10)), ("Physics", (10, 11)), ("Chemistry", (11, 12)),
    ("Biology", (10, 12)), ("History", (9, 11)), ("English", (11, 13)),
]

print("  课程时间表:")
for name, (start, end) in class_intervals:
    print(f"    {name:<12} {start}:00-{end}:00")

# 构建冲突图（同时进行的课程对）
conflict_graph = BipartiteGraph()
# 区间图是完美图 → 色数 = 团数 = 最大重叠数
# 按开始时间排序 + 贪心分配教室
sorted_classes = sorted(class_intervals, key=lambda x: x[1][0])
rooms = []      # [end_time]
assignments = {}
for name, (start, end) in sorted_classes:
    assigned = False
    for i, room_end in enumerate(rooms):
        if start >= room_end:                  # 教室空闲
            rooms[i] = end
            assignments[name] = i
            assigned = True; break
    if not assigned:
        rooms.append(end)
        assignments[name] = len(rooms) - 1
print(f"\n  贪心教室分配: {assignments}")
print(f"  最少教室数 = {len(rooms)}")
print("  区间图的最少教室数 = 最大重叠数（贪心即最优）")

print("\n== 最小顶点覆盖覆盖所有边 ==")
# 构建：左=课程，右=时间段，边=课程占用该时间段
bg = BipartiteGraph()
for name, (start, end) in class_intervals:
    for h in range(start, end):
        bg.add_edge(name, f"time_{h}")

m_l, m_r, size = hungarian(bg)
cover = min_vertex_cover(bg, m_l, m_r)
valid, bad_edge = is_valid_cover(bg, cover)
print(f"  最大匹配 = {size}")
print(f"  最小顶点覆盖 = {sorted(cover)}")
print(f"  覆盖合法: {valid}")
print(f"  König 定理成立: {len(cover) == size}")

print("\n== 最大独立集 = 总节点数 - 最小顶点覆盖 ==")
independent = bg.left | bg.right - cover
print(f"  总节点={len(bg.left) + len(bg.right)} 覆盖={len(cover)} "
      f"独立集={len(independent)}")
print("  独立集中的节点互不相邻（不共享时间段的课程可以共用教室）")

print("\n== Dilworth 定理（偏序集版本） ==")
# 偏序集：a ≤ b 当且仅当区间 a 完全在 b 之前（不重叠）
# 最小链覆盖（把元素分成最少的全序链）= 最大反链大小
# 反链 = 互不可比较的元素集合
overlaps = []
for i, (n1, (s1, e1)) in enumerate(class_intervals):
    for j, (n2, (s2, e2)) in enumerate(class_intervals):
        if i < j and s1 < e2 and s2 < e1:
            overlaps.append((n1, n2))
print(f"  重叠课程对: {overlaps}")
max_overlap = max(
    sum(1 for n, (s, e) in class_intervals if s < e2 and e > s2)
    for _, (s2, e2) in class_intervals
)
print(f"  最大同时重叠数 = {max_overlap} = 最少教室数")

print("\n== König 定理的应用 ==")
for line in [
    "  排课：最少教室数 = 最大重叠课程数",
    "  安全：最少摄像头覆盖所有走廊 = 最大匹配（走廊建模为二分图边）",
    "  任务调度：最少机器完成所有任务（无冲突任务可共享机器）",
    "  软件测试：最少测试用例覆盖所有代码路径（路径建模为二分图）",
]:
    print("  -", line)

print("\n== 工程要点 ==")
for line in [
    "  区间图是完美图：色数 = 团数，贪心着色即最优",
    "  一般图的最小覆盖是 NP 难的，但二分图有 König 定理保证多项式解",
    "  近似图（如非完美图）可用 LP 松弛 + 舍入得到 2 倍近似覆盖",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 构造一个二分图，验证「最小覆盖 = 最大匹配」对多种匹配方案都成立。
# 2. 实现教室分配的完整流程：输入课程列表，输出教室编号分配。
# 3. 用 König 定理求「最少保安覆盖所有走廊」（走廊建模为二分图的边）。
# 4. 思考：为什么区间图是完美图？这一性质如何简化教室分配？
