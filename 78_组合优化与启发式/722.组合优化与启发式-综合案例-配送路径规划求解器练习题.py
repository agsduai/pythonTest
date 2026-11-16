# ===== 第722课：组合优化与启发式-综合案例-配送路径规划求解器 =====
# 知识点：
#   - 综合串起本章：建模 -> 贪心构造 -> 邻域搜索 -> 模拟退火 -> 禁忌 -> 结果报告
#   - CVRP（带容量约束的车辆路径）：从仓库出发服务若干客户，最小化总里程
#   - 解表示：若干条「路线」，每条从 0（仓库）出发并回到 0
#   - 约束：每车容量上限、每个客户恰好访问一次；用罚函数软化约束
#   - 邻域算子：客户重定位 relocate、两客户交换 swap、路线内 2-opt
#   - 分层：构造初始解 -> 局部改进 -> 扰动跳出 -> 报告路线/里程/约束校验
#   - 全部标准库 + 固定 seed，纯内存、离线可运行
# 依赖：无（标准库）
import math
import random
from dataclasses import dataclass, field

R = random.Random()
R.seed(20261114)
N_CUSTOMERS = 14
COORDS = [(0, 0)] + [(R.randint(-50, 50), R.randint(-50, 50))
                     for _ in range(N_CUSTOMERS)]
DEMAND = [0] + [R.randint(1, 6) for _ in range(N_CUSTOMERS)]
CAPACITY = 18
DEPOT = 0


def dist(a, b):
    return math.hypot(COORDS[a][0]-COORDS[b][0], COORDS[a][1]-COORDS[b][1])


def route_distance(route):
    return sum(dist(route[i], route[i+1]) for i in range(len(route)-1))


def route_load(route):
    return sum(DEMAND[c] for c in route if c != DEPOT)


def solution_cost(routes, penalty=50.0):
    """总里程 + 超载罚分。"""
    total = sum(route_distance(r) for r in routes)
    over = sum(max(0, route_load(r) - CAPACITY) for r in routes)
    return total + penalty * over, total, over


@dataclass
class Solver:
    rng: random.Random = field(default_factory=lambda: random.Random(0))

    def greedy_construct(self):
        """按「最近可服务客户」逐车构造初始解。"""
        remaining = set(range(1, len(COORDS)))
        routes = []
        while remaining:
            route, load = [DEPOT], 0
            cur = DEPOT
            while True:
                feasible = [c for c in remaining if load + DEMAND[c] <= CAPACITY]
                if not feasible:
                    break
                nxt = min(feasible, key=lambda c: dist(cur, c))
                route.append(nxt)
                load += DEMAND[nxt]
                remaining.remove(nxt)
                cur = nxt
            route.append(DEPOT)
            routes.append(route)
        return routes

    def neighbors(self, routes):
        """生成 relocate / swap / 2-opt 三类邻域解（采样版）。"""
        out = []
        nr = len(routes)
        # relocate：把某客户移到另一条路线（或同路线另一位置）
        for _ in range(20):
            i = self.rng.randrange(nr)
            if len(routes[i]) <= 3:
                continue
            pos = self.rng.randrange(1, len(routes[i]) - 1)
            j = self.rng.randrange(nr)
            cand = [r[:] for r in routes]
            c = cand[i].pop(pos)
            ins = self.rng.randrange(1, len(cand[j]))
            cand[j].insert(ins, c)
            out.append(cand)
        # swap：交换两条路线里的两个客户
        for _ in range(15):
            i, j = self.rng.randrange(nr), self.rng.randrange(nr)
            if len(routes[i]) <= 3 or len(routes[j]) <= 3:
                continue
            cand = [r[:] for r in routes]
            a = self.rng.randrange(1, len(cand[i]) - 1)
            b = self.rng.randrange(1, len(cand[j]) - 1)
            cand[i][a], cand[j][b] = cand[j][b], cand[i][a]
            out.append(cand)
        # 2-opt：反转某条路线内部的一段
        for _ in range(15):
            i = self.rng.randrange(nr)
            if len(routes[i]) <= 4:
                continue
            cand = [r[:] for r in routes]
            a, b = sorted(self.rng.sample(range(1, len(cand[i]) - 1), 2))
            cand[i][a:b+1] = cand[i][a:b+1][::-1]
            out.append(cand)
        return out

    def local_search(self, routes, max_iter=400):
        cur = [r[:] for r in routes]
        cur_c = solution_cost(cur)[0]
        for _ in range(max_iter):
            cands = self.neighbors(cur)
            if not cands:
                break
            best = min(cands, key=lambda s: solution_cost(s)[0])
            best_c = solution_cost(best)[0]
            if best_c >= cur_c - 1e-9:
                break
            cur, cur_c = best, best_c
        return cur, cur_c

    def anneal(self, routes, T0=30.0, alpha=0.995, Tmin=0.1, iters=1200):
        cur = [r[:] for r in routes]
        cur_c = solution_cost(cur)[0]
        best, best_c = [r[:] for r in cur], cur_c
        T = T0
        step = 0
        while T > Tmin and step < iters:
            cands = self.neighbors(cur)
            if not cands:
                break
            cand = self.rng.choice(cands)
            c = solution_cost(cand)[0]
            d = c - cur_c
            if d < 0 or self.rng.random() < math.exp(-d / T):
                cur, cur_c = cand, c
                if c < best_c:
                    best, best_c = [r[:] for r in cand], c
            T *= alpha
            step += 1
        # 收尾再做一次局部搜索
        best, best_c = self.local_search(best)
        return best, best_c


def validate(routes):
    """校验：每个客户恰好一次、每条路线首尾是仓库、容量不超。"""
    served = [c for r in routes for c in r if c != DEPOT]
    all_customers = set(range(1, len(COORDS)))
    return {
        "all_served_once": len(served) == len(all_customers) and set(served) == all_customers,
        "depot_ends": all(r[0] == DEPOT and r[-1] == DEPOT for r in routes),
        "capacity_ok": all(route_load(r) <= CAPACITY for r in routes),
        "max_load": max(route_load(r) for r in routes),
    }


def render(name, routes):
    cost, mileage, over = solution_cost(routes)
    v = validate(routes)
    print(f"  {name}")
    print(f"    总代价={cost:.1f} 里程={mileage:.1f} 超载罚分={over*50:.0f} "
          f"车辆数={len(routes)}")
    print(f"    校验: 全覆盖={v['all_served_once']} 仓库闭合={v['depot_ends']} "
          f"容量合规={v['capacity_ok']} 最大载重={v['max_load']}/{CAPACITY}")
    for i, r in enumerate(routes, 1):
        print(f"    车{i}: {' -> '.join(map(str, r))}  里程={route_distance(r):.1f} "
              f"载重={route_load(r)}")


sv = Solver(random.Random(7))
print("== 问题规模 ==")
print(f"  客户 {N_CUSTOMERS} 个，仓库 1 个，单车容量={CAPACITY}，总需求={sum(DEMAND)}")
print(f"  理论最少车辆数={math.ceil(sum(DEMAND)/CAPACITY)}")

print("\n== 1) 贪心构造初始解 ==")
init = sv.greedy_construct()
render("贪心构造", init)

print("\n== 2) 局部搜索改进 ==")
ls, _ = sv.local_search([r[:] for r in init])
render("贪心 + 邻域搜索", ls)

print("\n== 3) 模拟退火 + 收尾局部搜索 ==")
sa, _ = sv.anneal(init)
render("SA 优化后", sa)

print("\n== 4) 多种子稳定性 ==")
costs = []
for seed in range(8):
    s = Solver(random.Random(seed))
    g = s.greedy_construct()
    best, c = s.anneal(g, iters=600)
    costs.append(solution_cost(best)[1])
print(f"  8 次独立运行里程: {[round(c, 1) for c in costs]}")
print(f"  最好={min(costs):.1f} 最差={max(costs):.1f} "
      f"均值={sum(costs)/len(costs):.1f}")
print("  随机算法要报告分布，不能只挑一次最好的说")

print("\n== 5) 容量约束敏感性 ==")
for cap in (12, 18, 25):
    CAPACITY = cap
    s = Solver(random.Random(7))
    g = s.greedy_construct()
    print(f"  容量={cap:>2}: 贪心需 {len(g)} 辆车，"
          f"理论下限 {math.ceil(sum(DEMAND)/cap)} 辆")
CAPACITY = 18

print("\n== 分层回顾 ==")
for line in [
    "  建模        : 解=路线列表，目标=里程+罚分，约束=容量/覆盖（第715课）",
    "  贪心构造    : 最近邻 + 容量检查，快速给可行初解（第720课）",
    "  邻域算子    : relocate / swap / 2-opt 三类移动（第715/716课）",
    "  局部搜索    : 只接受改进，快速收敛到局部最优（第715课）",
    "  模拟退火    : 概率接受劣解跳出局部最优（第716课）",
    "  校验与报告  : 结构化 validate + 多次运行统计，结论可信",
]:
    print("  -", line)

print("\n== 与真实 VRP 的差距 ==")
for line in [
    "  真实问题还有时间窗、多仓库、异构车队、取送货、路况",
    "  生产用 OR-Tools / LKH-3 / 商用求解器，规模可达上万点",
    "  本课展示「构造 + 改进 + 扰动」这一通用启发式框架",
    "  任何优化结果都要先过 validate，再谈目标值",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加时间窗约束：每个客户有 [最早, 最晚] 服务时间，迟到罚分。
# 2. 实现「扰动 + 重优化」的 ILS，对比与单次 SA 的解质量。
# 3. 用第719课的分支定界为 8 客户小实例求精确最优，计算最优性间隙。
# 4. 思考：为什么 VRP 里「先构造可行解、再改进」比「直接随机搜索」有效？
