# ===== 第333课：算法进阶-DFS与拓扑排序 =====
# 知识点：
#   - DFS 深度优先：一条路走到黑再回头（递归/栈实现，复习第250课）
#   - 有向无环图 DAG + 拓扑排序：排出“先做什么后做什么”
#   - Kahn 算法：入度为 0 的先出队，经典 BFS 应用（复习第332课）
#   - 有环的图排不出序 —— 检测环的副产品
# 依赖：无

from collections import deque

# ---- DFS：递归版与显式栈版 ----
graph = {
    "A": ["B", "C"], "B": ["D"], "C": ["D", "E"], "D": ["F"], "E": ["F"], "F": [],
}


def dfs_recursive(graph, node, visited=None):
    visited = visited if visited is not None else set()
    visited.add(node)
    order = [node]
    for nxt in graph[node]:
        if nxt not in visited:
            order += dfs_recursive(graph, nxt, visited)
    return order


def dfs_stack(graph, start):
    visited, order = set(), []
    stack = [start]
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        stack.extend(reversed(graph[node]))     # 反向入栈，保证字母序
    return order


print("DFS 递归：", dfs_recursive(graph, "A"))
print("DFS 栈　：", dfs_stack(graph, "A"))


# ---- 拓扑排序（Kahn 算法）：课程先修关系 ----
courses = {
    "Python基础": ["数据分析"], "SQL": ["数据分析"],
    "数据分析": ["机器学习"], "统计学": ["机器学习"], "机器学习": [],
}


def topo_sort(graph):
    indegree = {u: 0 for u in graph}
    for neighbors in graph.values():
        for v in neighbors:
            indegree[v] += 1
    queue = deque([u for u in graph if indegree[u] == 0])
    order = []
    while queue:
        u = queue.popleft()
        order.append(u)
        for v in graph[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    return order if len(order) == len(graph) else None    # None = 有环


print("推荐学习顺序：", " → ".join(topo_sort(courses)))

# 有环检测：A依赖B，B依赖A
cyclic = {"A": ["B"], "B": ["A"]}
print("有环图拓扑排序：", topo_sort(cyclic))

# ===== 练习题 =====
# 1. 用 DFS 实现拓扑排序（提示：逆后序）。
# 2. 判断两个节点是否连通（DFS 找到即停）。
# 3. 思考：课程依赖、任务调度、构建顺序，为什么都是拓扑排序？
