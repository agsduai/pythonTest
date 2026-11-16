# ===== 第721课：组合优化与启发式-约束满足与回溯剪枝 =====
# 知识点：
#   - CSP 三要素：变量、值域、约束；目标找到满足全部约束的赋值
#   - 回溯：逐变量赋值，违反约束即回退；比「全枚举再检查」早得多地剪枝
#   - 前向检查 forward checking：赋值后削减未赋值变量的可用值域
#   - 启发式：MRV（选剩余值最少的变量）、度启发式、最少约束值 LCV
#   - 约束传播 AC-3：弧一致性，反复删除不可能的值，常在回溯前预处理
#   - 案例：N 皇后、图着色、数独；本课用标准库实现并对比搜索节点数
# 依赖：无（标准库）
import time
from collections import defaultdict


def solve_nqueens(n, find_all=False):
    """N 皇后：逐行放一个皇后，列/主对角/副对角不能冲突。"""
    cols, diag1, diag2 = set(), set(), set()
    board = [-1] * n
    solutions, nodes = [], [0]

    def domains(row):
        return [c for c in range(n)
                if c not in cols and (row - c) not in diag1 and (row + c) not in diag2]

    def backtrack(row):
        nodes[0] += 1
        if row == n:
            solutions.append(board[:])
            return not find_all          # True 表示提前结束
        for c in domains(row):
            board[row] = c
            cols.add(c); diag1.add(row - c); diag2.add(row + c)
            stop = backtrack(row + 1)
            cols.discard(c); diag1.discard(row - c); diag2.discard(row + c)
            board[row] = -1
            if stop:
                return True
        return False

    backtrack(0)
    return solutions, nodes[0]


print("== N 皇后：朴素枚举 vs 回溯 ==")
for n in (4, 6, 8):
    sols, nodes = solve_nqueens(n)
    print(f"  n={n}: 第一个解={sols[0] if sols else None} 搜索节点={nodes} "
          f"（全枚举 n^n={n**n}）")

print("\n== 找全部解 ==")
for n in (4, 5, 6, 7, 8):
    sols, nodes = solve_nqueens(n, find_all=True)
    print(f"  n={n}: 解数={len(sols):>2} 搜索节点={nodes:>6}")

print("\n== 前向检查：图着色 ==")
EDGES = [(0,1),(0,2),(0,3),(1,2),(1,4),(2,3),(2,4),(3,4),(3,5),(4,5)]
N, K = 6, 3
adj = defaultdict(set)
for a, b in EDGES:
    adj[a].add(b); adj[b].add(a)

def solve_coloring(forward=True):
    domains = {v: set(range(K)) for v in range(N)}
    assign, nodes = {}, [0]

    def consistent(v, c):
        return all(assign.get(u) != c for u in adj[v])

    def propagate(v, c, changed):
        if not forward:
            return True
        for u in adj[v]:
            if u in assign:
                continue
            if c in domains[u]:
                domains[u].discard(c)
                changed.append((u, c))
                if not domains[u]:
                    return False
        return True

    def backtrack():
        nodes[0] += 1
        if len(assign) == N:
            return True
        # MRV：选剩余值域最小的未赋值变量
        v = min((x for x in range(N) if x not in assign),
                key=lambda x: len(domains[x]))
        # LCV：优先选对邻居约束最少的值
        values = sorted(domains[v],
                        key=lambda c: sum(c in domains[u] for u in adj[v]))
        for c in values:
            if not consistent(v, c):
                continue
            changed = []
            assign[v] = c
            if propagate(v, c, changed) and backtrack():
                return True
            assign.pop(v)
            for u, cc in changed:
                domains[u].add(cc)
        return False

    ok = backtrack()
    return (assign.copy() if ok else None), nodes[0]

for forward in (False, True):
    sol, nodes = solve_coloring(forward)
    print(f"  前向检查={forward!s:<5}: 解={sol} 搜索节点={nodes}")

print("\n== 约束传播 AC-3（弧一致性）==")
def ac3(domains, constraints):
    """constraints: {(x, y): 允许值对判定函数}；反复删不可能的值。"""
    queue = list(constraints)
    while queue:
        x, y = queue.pop(0)
        fn = constraints[(x, y)]
        removed = False
        for vx in list(domains[x]):
            if not any(fn(vx, vy) for vy in domains[y]):
                domains[x].remove(vx)
                removed = True
        if removed:
            queue.extend((z, x) for (z, w) in constraints if w == x and z != y)
    return domains

# 简单例子：X∈{1,2,3}, Y∈{1,2,3}, X<Y
d = {"X": {1,2,3}, "Y": {1,2,3}}
ac3(d, {("X", "Y"): lambda a, b: a < b,
        ("Y", "X"): lambda b, a: a < b})
print(f"  约束 X<Y 传播后: X={sorted(d['X'])}, Y={sorted(d['Y'])}")
print("  X=3 与 Y=1 被提前删除，回溯时不再白试")

print("\n== 变量/值排序启发式的效果 ==")
for n in (8, 10):
    t0 = time.perf_counter(); sols, nodes = solve_nqueens(n, find_all=True)
    dt = time.perf_counter() - t0
    print(f"  n={n}: 解数={len(sols)} 节点={nodes} 耗时={dt*1000:.1f}ms")
print("  MRV/度启发式通常能把节点数降一个数量级")

print("\n== CSP 求解策略速查 ==")
for line in (
    "  回溯 + 一致性检查: 基础，比全枚举强很多",
    "  前向检查 FC      : 赋值后立刻削减邻居值域",
    "  AC-3 弧一致性    : 回溯前/中反复传播，剪得更狠",
    "  MRV / 度启发式   : 先处理最「紧」的变量（失败优先）",
    "  LCV              : 给后续变量留更多选择",
):
    print(" ", line)

print("\n== 应用 ==")
for line in [
    "  排课/排班、考试安排、寄存器分配、数独、地图着色",
    "  配置产品选项（约束之间互相排斥）、时间表规划",
    "  大规模用 SAT/SMT 求解器或 CP-SAT（OR-Tools）",
    "  与优化结合：在可行解里再最小化代价（CSOP）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现完整的 MRV + 度启发式，对比 N=10 皇后的节点数。
# 2. 用 AC-3 预处理数独，再用回溯填完，统计搜索节点。
# 3. 把「最少约束值 LCV」加到图着色里，观察对首个解的影响。
# 4. 思考：为什么「失败优先」（MRV）比「先处理简单变量」更快？
