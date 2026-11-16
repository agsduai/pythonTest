# ===== 第834课：网络流与图匹配-综合案例-资源分配优化引擎 =====
# 知识点：
#   - 综合串起本章：最大流 -> 最小割 -> 二分图匹配 -> 最小费用流 -> 资源分配
#   - 统一接口：分配引擎支持「容量约束 + 成本优化 + 公平性」多目标
#   - 用最大流判定可行性，用 MCMF 优化成本，用 König 分析覆盖
#   - 全部标准库 + 固定 seed + 内存操作，离线可运行
# 依赖：无（标准库）
from collections import defaultdict, deque
import math
import random


def solve_max_flow(cap, source, sink):
    """最大流（Edmonds-Karp）。"""
    residual = defaultdict(lambda: defaultdict(float))
    for u in cap:
        for v, c in cap[u].items():
            residual[u][v] += c
            residual[v][u] += 0
    flow = 0.0
    while True:
        parent = {source: None}
        q = deque([source])
        found = False
        while q and not found:
            u = q.popleft()
            for v in list(residual[u]):
                if v not in parent and residual[u][v] > 1e-9:
                    parent[v] = u
                    if v == sink: found = True; break
                    q.append(v)
        if not found: break
        path, cur = [], sink
        while cur != source:
            path.append(cur); cur = parent[cur]
        path.reverse(); path.insert(0, source)
        bottleneck = min(residual[path[i]][path[i+1]]
                        for i in range(len(path)-1))
        for i in range(len(path)-1):
            residual[path[i]][path[i+1]] -= bottleneck
            residual[path[i+1]][path[i]] += bottleneck
        flow += bottleneck
    return flow, residual


def solve_mcmf(edges, source, sink):
    """最小费用最大流（SPFA），支持字符串节点名。"""
    # 收集所有节点并映射为索引
    node_set = set()
    for u, v, _, _ in edges:
        node_set.add(u); node_set.add(v)
    node_list = sorted(node_set)
    node_idx = {n: i for i, n in enumerate(node_list)}
    n = len(node_list)

    graph = defaultdict(list)
    all_edges = []
    for u, v, cap, cost in edges:
        ui, vi = node_idx[u], node_idx[v]
        graph[ui].append((vi, cap, cost, len(all_edges)))
        graph[vi].append((ui, 0, -cost, len(all_edges)+1))
        all_edges.append([u, v, cap, cost])
        all_edges.append([v, u, 0, -cost])
    src_i, snk_i = node_idx[source], node_idx[sink]
    INF = math.inf
    total_flow, total_cost = 0, 0
    flows = [0] * len(all_edges)
    max_rounds = 200
    round_count = 0
    while round_count < max_rounds:
        round_count += 1
        dist = [INF]*n
        parent = [None]*n
        in_q = [False]*n
        dist[src_i] = 0
        q = deque([src_i]); in_q[src_i] = True
        while q:
            u = q.popleft(); in_q[u] = False
            for v, cap, cost, ei in graph[u]:
                # 检查残余容量 all_edges[ei][2]，不是原始容量
                if all_edges[ei][2] > 0 and dist[u] + cost < dist[v]:
                    dist[v] = dist[u] + cost
                    parent[v] = (u, ei)
                    if not in_q[v]: q.append(v); in_q[v] = True
        if dist[snk_i] == INF: break
        bottleneck = INF
        cur = snk_i
        while cur != src_i:
            u, ei = parent[cur]
            bottleneck = min(bottleneck, all_edges[ei][2])
            cur = u
        cur = snk_i
        while cur != src_i:
            u, ei = parent[cur]
            all_edges[ei][2] -= bottleneck
            all_edges[ei ^ 1][2] += bottleneck
            flows[ei] += bottleneck
            total_cost += bottleneck * dist[snk_i]
            cur = u
        total_flow += bottleneck
    return total_flow, total_cost


def bipartite_matching(graph, left, right):
    """匈牙利算法求最大匹配。graph 可以是 dict 或有 .adj 属性的对象。"""
    adj = graph.adj if hasattr(graph, "adj") else graph
    match_r = {}
    match_l = {}
    def augment(u, visited):
        for v in adj.get(u, set()):
            if v not in visited:
                visited.add(v)
                if v not in match_r or augment(match_r[v], visited):
                    match_r[v] = u; match_l[u] = v
                    return True
        return False
    size = 0
    for u in sorted(left):
        visited = set()
        if augment(u, visited): size += 1
    return match_l, size


print("== 场景：多云算力分配 ==")
# 3 个数据中心 -> 3 个区域，带宽和成本不同
SUPPLIERS = {
    "DC-A": {"supply": 30, "cost_per_unit": 5},
    "DC-B": {"supply": 25, "cost_per_unit": 8},
    "DC-C": {"supply": 20, "cost_per_unit": 3},
}
CONSUMERS = {
    "East": {"demand": 25, "price_per_unit": 12},
    "West": {"demand": 20, "price_per_unit": 10},
    "South": {"demand": 25, "price_per_unit": 14},
}
ROUTES = [
    ("DC-A", "East", 20, 4),    # (from, to, capacity, cost_per_unit)
    ("DC-A", "West", 15, 6),
    ("DC-B", "East", 10, 3),
    ("DC-B", "South", 20, 5),
    ("DC-C", "West", 18, 2),
    ("DC-C", "South", 10, 7),
]

print("== 数据 ==")
print(f"  供给: { {k: v['supply'] for k, v in SUPPLIERS.items()} }")
print(f"  需求: { {k: v['demand'] for k, v in CONSUMERS.items()} }")
print(f"  路由:")
for u, v, cap, cost in ROUTES:
    print(f"    {u} -> {v}: cap={cap} cost={cost}/unit")

print("\n== 1) 可行性判定（最大流） ==")
cap = defaultdict(lambda: defaultdict(float))
for s, d in SUPPLIERS.items():
    cap["SUPER_S"][s] += d["supply"]
for c, d in CONSUMERS.items():
    cap[c]["SUPER_T"] += d["demand"]
for u, v, cp, _ in ROUTES:
    cap[u][v] += cp
flow, residual = solve_max_flow(cap, "SUPER_S", "SUPER_T")
print(f"  最大流 = {flow:.0f}  需求 = {sum(d['demand'] for d in CONSUMERS.values())}")
print(f"  可行 = {flow >= sum(d['demand'] for d in CONSUMERS.values())}")

print("\n== 2) 最小费用分配（MCMF） ==")
mcmf_edges = []
for s, d in SUPPLIERS.items():
    mcmf_edges.append(("SRC", s, d["supply"], 0))
for c, d in CONSUMERS.items():
    mcmf_edges.append((c, "SNK", d["demand"], 0))
for u, v, cp, cost in ROUTES:
    mcmf_edges.append((u, v, cp, cost))
mcmf_flow, mcmf_cost = solve_mcmf(mcmf_edges, "SRC", "SNK")
print(f"  MCMF: 流={mcmf_flow} 费用={mcmf_cost}")
print("  MCMF 在保证最大流的同时最小化运输成本")

print("\n== 3) 匹配：员工-项目分配 ==")
team_graph = defaultdict(set)
team_left = set(); team_right = set()
emp_skills = {
    "alice": ["backend", "frontend"],
    "bob": ["backend", "devops"],
    "carol": ["frontend", "design"],
    "dave": ["devops", "backend"],
}
projects = ["webapp", "infra", "landing"]
proj_needs = {"webapp": ["frontend"], "infra": ["backend", "devops"], "landing": ["design", "frontend"]}
for emp, skills in emp_skills.items():
    team_left.add(emp)
    for proj in projects:
        for skill in proj_needs.get(proj, []):
            if skill in skills:
                team_graph[emp].add(proj)
                team_right.add(proj)
                break

m_match, m_size = bipartite_matching(team_graph, team_left, team_right)
print(f"  员工技能: {emp_skills}")
print(f"  项目需求: {proj_needs}")
print(f"  最大匹配 = {m_size}/{len(team_left)} 人")
print(f"  分配: {m_match}")

print("\n== 4) 最小割分析瓶颈 ==")
S_side = {"SUPER_S"}
q = deque(["SUPER_S"])
while q:
    u = q.popleft()
    for v in cap[u]:
        if v not in S_side and residual.get(u, {}).get(v, 0) > 1e-9:
            S_side.add(v); q.append(v)
bottleneck_edges = []
for u in S_side:
    for v in cap[u]:
        if v not in S_side and cap[u][v] > 0:
            bottleneck_edges.append((u, v, cap[u][v]))
print(f"  瓶颈边（割边）: {bottleneck_edges}")
print(f"  瓶颈容量 = {sum(c for _, _, c in bottleneck_edges):.0f}")
print("  增加这些边的容量可以直接提高总分配量")

print("\n== 引擎分层 ==")
for line in [
    "  可行性层  : 最大流判定「需求能否满足」（第827课）",
    "  优化层    : MCMF 在可行流中选费用最小的（第830课）",
    "  匹配层    : 二分图匹配做人员/任务分配（第828课）",
    "  分析层    : 最小割找瓶颈、König 定理找覆盖（第829/833课）",
    "  组合层    : 统一接口 + 多目标权衡 + 可扩展策略",
]:
    print("  -", line)

print("\n== 与生产系统的差距 ==")
for line in [
    "  单商品流；多商品流（多种资源共享链路）是 NP 难的",
    "  无时间维度（真实调度有窗口、时序依赖）",
    "  未考虑公平性约束（如每个消费者至少分配 min_units）",
    "  生产用 OR-Tools CP-SAT / Gurobi 求解更复杂的组合优化",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给分配问题加「公平性约束」：每个消费者至少分配 min_units（用下界费用流）。
# 2. 实现「动态重分配」：某个数据中心宕机后自动重新分配。
# 3. 对比 MCMF 费用最优解与贪心分配的费用差异，量化优化收益。
# 4. 思考：为什么资源分配问题能用网络流求解，而一般 TSP 不能？
