# ===== 第832课：网络流与图匹配-多源多汇与流量分配 =====
# 知识点：
#   - 多源多汇：多个源点（供给）+ 多个汇点（需求），用超源超汇统一建模
#   - 超源 S -> 各源点（容量=供给量）；各汇点 -> 超汇 T（容量=需求量）
#   - 可行流判定：最大流 = Σ需求 时可行，否则需求无法全部满足
#   - 多种货物：每种货物独立建网络，或用带标签的流
#   - 与第78章组合优化：分配问题用 MCMF（第830课），可行流用最大流判定
# 依赖：无（标准库）
from collections import defaultdict, deque
import math


class FlowNetwork:
    def __init__(self):
        self.cap = defaultdict(lambda: defaultdict(float))
        self.nodes = set()

    def add_edge(self, u, v, cap):
        self.cap[u][v] += cap
        self.nodes.add(u); self.nodes.add(v)

    def max_flow(self, s, t):
        residual = defaultdict(lambda: defaultdict(float))
        for u in self.cap:
            for v, c in self.cap[u].items():
                residual[u][v] += c
                residual[v][u] += 0
        flow = 0.0
        while True:
            parent = {s: None}
            q = deque([s])
            found = False
            while q and not found:
                u = q.popleft()
                for v in list(residual[u]):
                    if v not in parent and residual[u][v] > 1e-9:
                        parent[v] = u
                        if v == t: found = True; break
                        q.append(v)
            if not found: break
            path, cur = [], t
            while cur != s:
                path.append(cur); cur = parent[cur]
            path.reverse(); path.insert(0, s)
            bottleneck = min(residual[path[i]][path[i+1]]
                           for i in range(len(path)-1))
            for i in range(len(path)-1):
                residual[path[i]][path[i+1]] -= bottleneck
                residual[path[i+1]][path[i]] += bottleneck
            flow += bottleneck
        return flow, residual


print("== 多源多汇：资源分配可行性 ==")
# 3 个数据中心（源）向 3 个区域（汇）分配算力
SOURCES = {"DC-A": 30, "DC-B": 25, "DC-C": 20}       # 供给量
SINKS = {"Region-East": 25, "Region-West": 20, "Region-South": 25}  # 需求量
# 连接：数据中心 -> 区域，容量为带宽限制
LINKS = [
    ("DC-A", "Region-East", 20), ("DC-A", "Region-West", 15),
    ("DC-B", "Region-East", 10), ("DC-B", "Region-South", 20),
    ("DC-C", "Region-West", 18), ("DC-C", "Region-South", 10),
]
SUPPLY_TOTAL = sum(SOURCES.values())
DEMAND_TOTAL = sum(SINKS.values())

print(f"  供给总量 = {SUPPLY_TOTAL}  需求总量 = {DEMAND_TOTAL}")
print(f"  {'源':<8}{'供给':>6}   {'汇':<16}{'需求':>6}")
for s, v in SOURCES.items(): print(f"  {s:<8}{v:>6}")
for t, v in SINKS.items(): print(f"  {'':>8}      {t:<16}{v:>6}")

print("\n== 构建超源超汇 ==")
net = FlowNetwork()
SUPER_S, SUPER_T = "SUPER_S", "SUPER_T"
for s, v in SOURCES.items():
    net.add_edge(SUPER_S, s, v)
for t, v in SINKS.items():
    net.add_edge(t, SUPER_T, v)
for u, v, cap in LINKS:
    net.add_edge(u, v, cap)

flow, residual = net.max_flow(SUPER_S, SUPER_T)
print(f"  最大流 = {flow:.0f}  需求总量 = {DEMAND_TOTAL}")
print(f"  可行 = {flow >= DEMAND_TOTAL}")

print("\n== 各源实际流出 / 各汇实际流入 ==")
src_flow = {s: 0.0 for s in SOURCES}
sink_flow = {t: 0.0 for t in SINKS}
for u in net.cap:
    for v in net.cap[u]:
        cap = net.cap[u][v]
        r = residual.get(u, {}).get(v, 0)
        if cap > 0:
            actual = cap - r
            if u in SOURCES: src_flow[u] += actual
            if v in SINKS: sink_flow[v] += actual
print("  源流出:", {k: f"{v:.0f}/{SOURCES[k]}" for k, v in src_flow.items()})
print("  汇流入:", {k: f"{v:.0f}/{SINKS[k]}" for k, v in sink_flow.items()})

print("\n== 需求无法满足的场景 ==")
SINKS_BIG = {"Region-East": 40, "Region-West": 30, "Region-South": 30}  # 需求 100 > 供给 75
net2 = FlowNetwork()
for s, v in SOURCES.items(): net2.add_edge(SUPER_S, s, v)
for t, v in SINKS_BIG.items(): net2.add_edge(t, SUPER_T, v)
for u, v, cap in LINKS: net2.add_edge(u, v, cap)
f2, r2 = net2.max_flow(SUPER_S, SUPER_T)
print(f"  供给={SUPPLY_TOTAL} 需求={sum(SINKS_BIG.values())} -> 最大流={f2:.0f}")
print(f"  缺口={sum(SINKS_BIG.values())-f2:.0f}（无法满足全部需求）")
print("  各汇实际流入:", end=" ")
for u in net2.cap:
    for v in net2.cap[u]:
        cap = net2.cap[u][v]
        r = r2.get(u, {}).get(v, 0)
        if cap > 0 and v in SINKS_BIG:
            actual = cap - r
            print(f"{v}={actual:.0f}", end=" ")
print()

print("\n== 最小割分析：哪些需求无法满足 ==")
S_side = {SUPER_S}
q = deque([SUPER_S])
while q:
    u = q.popleft()
    for v in net2.cap[u]:
        if v not in S_side and r2.get(u, {}).get(v, 0) > 1e-9:
            S_side.add(v); q.append(v)
cut_edges = [(u, v) for u in S_side for v in net2.cap[u]
             if v not in S_side and net2.cap[u][v] > 0]
print(f"  S 侧: {sorted(S_side)}")
print(f"  T 侧（未被供给）: {sorted(set(SINKS_BIG) - S_side)}")
print(f"  割边: {cut_edges}（瓶颈所在）")

print("\n== 多种货物（每种独立建网络） ==")
for cargo_type, bandwidth_factor in (("视频", 1.0), ("语音", 0.5), ("数据", 0.3)):
    # 简化：按带宽因子缩小链路容量
    net_c = FlowNetwork()
    for s, v in SOURCES.items(): net_c.add_edge(SUPER_S, s, v * bandwidth_factor)
    for t, v in SINKS.items(): net_c.add_edge(t, SUPER_T, v * bandwidth_factor)
    for u, v, cap in LINKS: net_c.add_edge(u, v, cap * bandwidth_factor)
    f_c, _ = net_c.max_flow(SUPER_S, SUPER_T)
    print(f"  {cargo_type}（带宽因子={bandwidth_factor}）: 最大流={f_c:.1f}")

print("\n== 建模技巧 ==")
for line in (
    "  多源多汇 -> 超源超汇（容量=供给/需求）",
    "  供给和需求不等 -> 仍可求最大流，找出瓶颈",
    "  多种货物 -> 每种独立建网络，或用「标签流」（更复杂）",
    "  与第830课 MCMF 结合 -> 在可行流中选费用最小的分配方案",
):
    print(" ", line)

print("\n== 应用 ==")
for line in [
    "  CDN：多个源站向多个边缘节点分发内容",
    "  云计算：VM 迁移（源=物理机，汇=目标机，容量=带宽/资源）",
    "  电力网：发电站 -> 变电站 -> 用户（最大输电能力）",
    "  供水系统：水库 -> 水厂 -> 用户",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「带最小流量约束」的多源多汇：每个源至少流出 min_supply。
# 2. 用第830课 MCMF 为上述网络找费用最小的分配方案。
# 3. 实现「多商品流」的简单版本（2 种货物共享链路容量）。
# 4. 思考：为什么多源多汇问题用超源超汇建模就等价于单源单汇？
