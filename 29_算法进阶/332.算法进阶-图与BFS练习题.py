# ===== 第332课：算法进阶-图与BFS =====
# 知识点：
#   - 图：dict 邻接表 {节点: [邻居]}，最直观的表示
#   - BFS 广度优先：一层层扩散 —— 无权图最短路径的标准解法
#   - 用队列实现（复习第251课），visited 防止绕圈
# 依赖：无

from collections import deque

graph = {
    "A": ["B", "C"],
    "B": ["D"],
    "C": ["D", "E"],
    "D": ["F"],
    "E": ["F"],
    "F": [],
}


def bfs_shortest(graph, start, end):
    """BFS 最短路径：队列里带“走到这里的路径”。"""
    queue = deque([(start, [start])])
    visited = {start}
    while queue:
        node, path = queue.popleft()
        if node == end:
            return path
        for nxt in graph[node]:
            if nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, path + [nxt]))
    return None


print("A 到 F 最短路径：", " → ".join(bfs_shortest(graph, "A", "F")))

# ---- 按层遍历：看“几步能到” ----
def bfs_levels(graph, start):
    level = {start: 0}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for nxt in graph[node]:
            if nxt not in level:
                level[nxt] = level[node] + 1
                queue.append(nxt)
    return level


levels = bfs_levels(graph, "A")
print("各节点步数：", levels)
print("两步可达：", [n for n, d in levels.items() if d == 2])

# ---- 社交关系的小演示：朋友的朋友 ----
friends = {"小明": ["小红", "小刚"], "小红": ["小丽"], "小刚": ["小强"], "小丽": [], "小强": []}
print("小明两步内认识：", [n for n, d in bfs_levels(friends, "小明").items() if d <= 2 and n != "小明"])

# ===== 练习题 =====
# 1. 给 bfs_shortest 加“把路径上所有等长最短路径都返回”的版本。
# 2. 用 BFS 判断图是否连通（能到的节点数 == 总节点数）。
# 3. 思考：BFS 为什么用队列而不用栈？换成栈会变成什么遍历？（下一课）
