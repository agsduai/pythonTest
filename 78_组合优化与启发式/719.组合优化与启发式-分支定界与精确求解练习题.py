# ===== 第719课：组合优化与启发式-分支定界与精确求解 =====
# 知识点：
#   - 分支定界 B&B：把解空间递归分成子问题（分支），用界限剪掉不可能更优的子树
#   - 上界/下界：最大化问题里，乐观估计的上界 ≤ 当前最优解即可剪枝
#   - 界限函数要「又快又紧」：太松剪不掉，太慢得不偿失
#   - 与贪心/启发式配合：先找一个好可行解作为初始下界，能大幅提前剪枝
#   - 0/1 背包：按价值密度排序 + 分数背包松弛给出乐观上界
#   - 精确算法保证最优，但最坏仍指数；适合中小规模或作为启发式的校验基准
# 依赖：无（标准库）
import time
from dataclasses import dataclass, field

ITEMS = [("笔记本", 3, 4), ("相机", 4, 5), ("水壶", 2, 3), ("帐篷", 6, 8),
         ("食物", 3, 4), ("衣服", 2, 2), ("地图", 1, 2), ("手电", 2, 3),
         ("药品", 2, 4), ("书籍", 3, 3), ("工具", 4, 6), ("睡袋", 5, 7),
         ("炉具", 3, 5), ("雨衣", 2, 3), ("绳索", 4, 5)]
CAPACITY = 18
N = len(ITEMS)


@dataclass
class Stats:
    nodes: int = 0
    pruned_bound: int = 0
    pruned_capacity: int = 0
    leaves: int = 0


def greedy(items, cap):
    """按价值密度排序的贪心可行解，作为初始下界。"""
    order = sorted(range(len(items)), key=lambda i: -items[i][2] / items[i][1])
    chosen, w, v = [0] * len(items), 0, 0
    for i in order:
        if w + items[i][1] <= cap:
            chosen[i] = 1
            w += items[i][1]
            v += items[i][2]
    return chosen, v, w


def fractional_bound(items, order, start, cap_left, value_so_far):
    """分数背包松弛：允许取物品的一部分，给出乐观上界。"""
    bound = value_so_far
    rem = cap_left
    for i in order[start:]:
        _, w, v = items[i]
        if w <= rem:
            bound += v
            rem -= w
        else:
            bound += v * rem / w     # 取一部分
            break
    return bound


def branch_and_bound(items, cap):
    order = sorted(range(len(items)), key=lambda i: -items[i][2] / items[i][1])
    init_sol, init_v, _ = greedy(items, cap)
    # 初始下界来自贪心可行解，对应解也要记下：若贪心恰好最优，B&B 不再更新 best_sol
    best_val, best_sol, stats = init_v, init_sol[:], Stats()
    chosen = [0] * len(items)

    def dfs(k, cap_left, value_so_far):
        nonlocal best_val, best_sol
        stats.nodes += 1
        if k == len(items):
            stats.leaves += 1
            if value_so_far > best_val:
                best_val, best_sol = value_so_far, chosen[:]
            return
        if fractional_bound(items, order, k, cap_left, value_so_far) <= best_val:
            stats.pruned_bound += 1
            return
        i = order[k]
        _, w, v = items[i]
        # 分支 1：不选
        chosen[i] = 0
        dfs(k + 1, cap_left, value_so_far)
        # 分支 2：选（若装得下）
        if w <= cap_left:
            chosen[i] = 1
            dfs(k + 1, cap_left - w, value_so_far + v)
            chosen[i] = 0
        else:
            stats.pruned_capacity += 1

    dfs(0, cap, 0)
    return best_sol, best_val, stats


print("== 0/1 背包精确求解 ==")
print(f"  物品 {N} 件，容量={CAPACITY}，全空间 2^{N} = {2**N}")
g_sol, g_val, g_w = greedy(ITEMS, CAPACITY)
print(f"  贪心初始解: 价值={g_val} 重量={g_w}")

print("\n== 暴力穷举（基线）==")
t0 = time.perf_counter()
brute_val, brute_sol = -1, None
for mask in range(1 << N):
    w = sum(ITEMS[i][1] for i in range(N) if (mask >> i) & 1)
    if w <= CAPACITY:
        v = sum(ITEMS[i][2] for i in range(N) if (mask >> i) & 1)
        if v > brute_val:
            brute_val, brute_sol = v, mask
t_brute = time.perf_counter() - t0
print(f"  最优价值={brute_val}  耗时={t_brute*1000:.1f}ms")

print("\n== 分支定界 ==")
t0 = time.perf_counter()
sol, val, st = branch_and_bound(ITEMS, CAPACITY)
t_bb = time.perf_counter() - t0
print(f"  最优价值={val} 与穷举一致={val == brute_val}")
print(f"  耗时={t_bb*1000:.1f}ms  加速≈{t_brute/t_bb if t_bb else 0:.0f}×")
print(f"  搜索节点={st.nodes} / 2^{N+1}-1≈{2**(N+1)-1} "
      f"({st.nodes/(2**(N+1)-1):.1%})")
print(f"  剪枝: 上界={st.pruned_bound} 超重={st.pruned_capacity} 到叶子={st.leaves}")
print("  选中物品:", [ITEMS[i][0] for i, b in enumerate(sol) if b])

print("\n== 界限函数质量对比 ==")
def trivial_bound(items, order, k, cap_left, value_so_far):
    """粗糙上界：把剩余全加上（不管容量）。"""
    return value_so_far + sum(items[i][2] for i in order[k:])

def bb_with(bound_fn, cap=CAPACITY):
    order = sorted(range(len(ITEMS)), key=lambda i: -ITEMS[i][2]/ITEMS[i][1])
    best = [0]
    stats = [0]
    chosen = [0] * len(ITEMS)
    def dfs(k, left, v):
        stats[0] += 1
        if k == len(ITEMS):
            best[0] = max(best[0], v)
            return
        if bound_fn(ITEMS, order, k, left, v) <= best[0]:
            return
        i = order[k]; w, val = ITEMS[i][1], ITEMS[i][2]
        dfs(k+1, left, v)
        if w <= left:
            chosen[i] = 1
            dfs(k+1, left-w, v+val)
            chosen[i] = 0
    dfs(0, cap, 0)
    return best[0], stats[0]

for name, fn in (("平凡上界(剩余全加)", trivial_bound),
                 ("分数背包上界", fractional_bound)):
    v, nodes = bb_with(fn)
    print(f"  {name:<22}: 最优={v} 搜索节点={nodes}")
print("  上界越紧，剪枝越多，节点数可差几个数量级")

print("\n== 初始下界的作用 ==")
def bb_with_init(bound_fn, init_best, cap=CAPACITY):
    order = sorted(range(len(ITEMS)), key=lambda i: -ITEMS[i][2]/ITEMS[i][1])
    best, nodes = [init_best], [0]
    def dfs(k, left, v):
        nodes[0] += 1
        if k == len(ITEMS):
            best[0] = max(best[0], v)
            return
        if bound_fn(ITEMS, order, k, left, v) <= best[0]:
            return
        i = order[k]; w, val = ITEMS[i][1], ITEMS[i][2]
        dfs(k+1, left, v)
        if w <= left:
            dfs(k+1, left-w, v+val)
    dfs(0, cap, 0)
    return best[0], nodes[0]

for init in (0, 10, 20, g_val):
    v, nodes = bb_with_init(fractional_bound, init)
    print(f"  初始下界={init:>2}: 搜索节点={nodes:>6} 最终最优={v}")
print("  下界越接近最优，越早触发上界剪枝 -> 节点数下降")

print("\n== B&B 三要素 ==")
for line in (
    "  分支: 把「选/不选第 k 件」拆成两个子问题，覆盖全部解且不重叠",
    "  定界: 给每个子树算乐观上界，≤当前最优就整棵剪掉",
    "  初始解: 贪心/启发式先给一个好下界，让剪枝尽早生效",
    "  正确性: 上界必须真的「乐观」，低估会误剪掉最优解",
):
    print(" ", line)

print("\n== 启发式 vs 精确算法 ==")
for line in [
    f"  本例 N={N} 精确可解；N=100 时 2^100 完全不可行",
    "  工程做法: 启发式找可行解 + 精确算法验证小实例/求最优性间隙",
    "  最优性间隙 gap = (上界 - 可行解) / 上界，衡量解还有多少提升空间",
    "  商业求解器（Gurobi/CP-SAT）把 B&B + 割平面 + 启发式做到极致",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给 B&B 增加「最优性间隙」输出，随时报告当前上界与下界。
# 2. 把分支顺序改成「先选价值密度高的」，观察节点数变化。
# 3. 用 B&B 求解图着色判定问题（k 色是否可行），与第718课对比。
# 4. 思考：为什么上界函数「低估最优」会破坏 B&B 的正确性？
