# ===== 第715课：组合优化与启发式-问题建模与邻域搜索 =====
# 知识点：
#   - 组合优化三要素：解的表示、目标函数、约束；很多问题是 NP 难
#   - 精确算法（枚举/分支定界）只适用于小规模；大规模用启发式找「足够好」的解
#   - 邻域 neighbor：对当前解做一次最小改动得到的所有候选解
#   - 爬山法 hill climbing：只接受更优邻域解，容易卡在局部最优
#   - 随机重启：从多个随机初始解出发取最好， cheap 但有效
#   - 用可注入 rng 保证可复现；评估函数要 O(1)~O(n) 更新而非每次重算
# 依赖：无（标准库）
import random

# 以「最大割 Max-Cut」为例：把图的顶点分成两组，最大化跨组边数
EDGES = [(0,1),(0,2),(0,4),(1,2),(1,3),(1,5),(2,3),(2,5),
         (3,4),(3,5),(4,5),(0,3),(2,4)]
N = 6


def cut_value(assign):
    """assign[i] ∈ {0,1}，返回跨组边数。"""
    return sum(1 for a, b in EDGES if assign[a] != assign[b])


def neighbors(assign):
    """翻转一个顶点得到全部 N 个邻域解。"""
    for i in range(len(assign)):
        cand = assign[:]
        cand[i] ^= 1
        yield cand, i


def hill_climb(start, rng):
    cur = start[:]
    cur_v = cut_value(cur)
    history = [cur_v]
    while True:
        best, best_v, best_i = None, cur_v, None
        for cand, i in neighbors(cur):
            v = cut_value(cand)
            if v > best_v:
                best, best_v, best_i = cand, v, i
        if best is None:
            break
        cur, cur_v = best, best_v
        history.append(cur_v)
    return cur, cur_v, history


print("== 问题建模：Max-Cut ==")
print(f"  顶点 {N} 个，边 {len(EDGES)} 条")
print("  解表示: 长度 6 的 0/1 列表；目标: 最大化跨组边数")
print(f"  全空间大小 2^{N} = {2**N}（小规模可穷举验证）")

print("\n== 穷举求全局最优（基线）==")
best_all, best_val = None, -1
for mask in range(1 << N):
    a = [(mask >> i) & 1 for i in range(N)]
    v = cut_value(a)
    if v > best_val:
        best_val, best_all = v, a
print(f"  全局最优 = {best_val}，解 = {best_all}")

print("\n== 单次爬山（不同起点可能卡住）==")
rng = random.Random(7)
for trial in range(6):
    start = [rng.randrange(2) for _ in range(N)]
    sol, val, hist = hill_climb(start, rng)
    stuck = val < best_val
    print(f"  起点={start} -> {val} {'（局部最优）' if stuck else '（达到全局最优）'} "
          f"轨迹={hist}")

print("\n== 随机重启爬山 ==")
def restart_hill(restarts=20, seed=42):
    r = random.Random(seed)
    best_sol, best_v = None, -1
    for _ in range(restarts):
        start = [r.randrange(2) for _ in range(N)]
        sol, v, _ = hill_climb(start, r)
        if v > best_v:
            best_sol, best_v = sol, v
    return best_sol, best_v

for k in (1, 3, 5, 10, 30):
    sol, v = restart_hill(k, seed=42)
    print(f"  restarts={k:>2}: 最优={v} 命中全局={v == best_val}")

print("\n== 增量评估：翻转一个点只需看它的关联边 ==")
adj = [[] for _ in range(N)]
for a, b in EDGES:
    adj[a].append(b); adj[b].append(a)

def flip_delta(assign, i):
    """翻转顶点 i 后 cut_value 的变化量，O(degree(i))。"""
    old = sum(1 for j in adj[i] if assign[i] != assign[j])
    new = sum(1 for j in adj[i] if (assign[i] ^ 1) != assign[j])
    return new - old

a = [0, 1, 0, 1, 0, 1]
for i in (0, 2, 5):
    before = cut_value(a)
    b = a[:]; b[i] ^= 1
    print(f"  翻转 {i}: 预测 Δ={flip_delta(a, i):+d} 实测={cut_value(b)-before:+d} "
          f"一致={flip_delta(a, i) == cut_value(b)-before}")

print("\n== 复杂度对比 ==")
for line in (
    f"  穷举: 2^{N}={2**N} 个解，每个 O(E) -> {2**N * len(EDGES)} 次边检查",
    f"  爬山: 每轮 O(N·E)={N*len(EDGES)}，通常几轮收敛",
    "  N=1000 时穷举完全不可行，启发式仍可跑",
    "  增量评估把单步从 O(E) 降到 O(deg)，长跑收益显著",
):
    print(" ", line)

print("\n== 建模要点 ==")
for line in [
    "  解表示要便于生成邻域（0/1 串、排列、路径、划分）",
    "  约束可硬拒（罚函数）或软惩罚，后者让搜索更平滑",
    "  目标函数尽量可增量计算，否则迭代次数上不去",
    "  先在小实例上与穷举对照，验证实现正确性",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 把爬山法改成「接受相等解」(plateau 移动)，观察是否更容易跳出平台。
# 2. 用增量 delta 重写 hill_climb，测量 100 个顶点时的耗时差异。
# 3. 给 Max-Cut 加「两组大小差不超过 1」的约束，用罚函数实现。
# 4. 思考：为什么「邻域定义」几乎决定了一个启发式算法的成败？
