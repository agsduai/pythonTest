# ===== 第718课：组合优化与启发式-禁忌搜索与局部搜索增强 =====
# 知识点：
#   - 禁忌搜索 Tabu Search：用短期记忆禁止「刚做过的逆操作」，强制跳出局部最优
#   - 禁忌表 tabu list 存最近若干次移动（或移动属性）， tenure 决定记忆长度
#   - 特赦准则 aspiration：若某禁忌移动能刷新历史最优，仍允许执行
#   - 与 SA 对比：SA 用概率接受劣解，TS 用确定性记忆避免循环
#   - 候选列表策略：每步只评估部分邻域，配合增量 delta 提效
#   - 应用：调度、车辆路径、图着色、作业车间（JSP）
# 依赖：无（标准库）
import random
from collections import deque

# 图着色：给 8 个顶点染 k 种颜色，最小化「冲突边」数
EDGES = [(0,1),(0,2),(0,4),(1,2),(1,3),(1,5),(2,3),(2,5),
         (3,4),(3,5),(4,5),(4,6),(5,6),(5,7),(6,7),(0,6),(2,7)]
N, K = 8, 3


def conflicts(color):
    return sum(1 for a, b in EDGES if color[a] == color[b])


def delta_conflict(color, v, new_c):
    """只重算顶点 v 关联边，返回冲突数变化。"""
    old_c = color[v]
    old = sum(1 for a, b in EDGES if v in (a, b) and color[a] == color[b])
    color[v] = new_c
    new = sum(1 for a, b in EDGES if v in (a, b) and color[a] == color[b])
    color[v] = old_c
    return new - old


def hill_climb(start, seed=0):
    rng = random.Random(seed)
    cur, cur_v = start[:], conflicts(start)
    steps = 0
    while cur_v > 0 and steps < 2000:
        best = []
        for v in range(N):
            for c in range(K):
                if c == cur[v]:
                    continue
                d = delta_conflict(cur, v, c)
                best.append((d, v, c))
        d, v, c = min(best)
        if d >= 0:
            break                       # 无改进，卡住
        cur[v] = c
        cur_v += d
        steps += 1
    return cur, cur_v, steps


def tabu_search(start, tenure=5, iterations=300, seed=0):
    rng = random.Random(seed)
    cur, cur_v = start[:], conflicts(start)
    best, best_v = cur[:], cur_v
    tabu = {}                            # 移动属性 -> 解禁迭代号
    history = [cur_v]
    for it in range(iterations):
        candidates = []
        for v in range(N):
            for c in range(K):
                if c == cur[v]:
                    continue
                d = delta_conflict(cur, v, c)
                forbidden = tabu.get((v, cur[v]), -1) > it
                aspiration = cur_v + d < best_v
                candidates.append((d, rng.random(), v, c, forbidden and not aspiration))
        # 优先非禁忌；若全被禁忌则取最好的（含特赦）
        allowed = [x for x in candidates if not x[4]]
        pool = allowed or candidates
        d, _, v, c, _ = min(pool, key=lambda x: (x[0], x[1]))
        old_c = cur[v]
        cur[v] = c
        cur_v += d
        # 禁止「把这个点改回旧颜色」
        tabu[(v, c)] = it + tenure
        if cur_v < best_v:
            best, best_v = cur[:], cur_v
        history.append(cur_v)
        if best_v == 0:
            break
    return best, best_v, history


print("== 图着色建模 ==")
print(f"  顶点 {N}，边 {len(EDGES)}，颜色数 K={K}")
print(f"  解=长度 {N} 的颜色列表，目标=冲突边数最小（理想为 0）")
print(f"  搜索空间 K^N = {K**N}")

print("\n== 爬山法：多种子结果 ==")
hc_results = []
for s in range(10):
    start = [random.Random(100 + s).randrange(K) for _ in range(N)]
    _, v, steps = hill_climb(start, seed=s)
    hc_results.append(v)
    print(f"  seed={s}: 冲突={v} 步数={steps}")
print(f"  10 次平均冲突={sum(hc_results)/len(hc_results):.2f}")

print("\n== 禁忌搜索（不同 tenure）==")
for tenure in (2, 5, 10, 20):
    start = [random.Random(100).randrange(K) for _ in range(N)]
    sol, v, hist = tabu_search(start, tenure=tenure, iterations=200, seed=1)
    print(f"  tenure={tenure:>2}: 最优冲突={v} 收敛代数={len(hist)} "
          f"{'（找到合法着色）' if v == 0 else ''}")

print("\n== 搜索轨迹（tenure=5，前 25 代）==")
start = [random.Random(100).randrange(K) for _ in range(N)]
_, _, hist = tabu_search(start, tenure=5, iterations=60, seed=1)
print("  ", hist[:25])
print("  可见目标值会「先变差再变好」——正是禁忌强制跳出局部最优的效果")

print("\n== 禁忌表内容示意 ==")
tabu = {(2, 1): 12, (5, 0): 15, (7, 2): 18}
print("  禁忌项 (顶点, 新颜色) -> 解禁迭代:", tabu)
print("  当前迭代=14 时，前两项已解禁，(7,2) 仍被禁止")

print("\n== 特赦准则 aspiration 的必要性 ==")
for line in (
    "  若某个被禁的移动恰好能刷新历史最优，禁止它反而丢掉好解",
    "  规则: 候选解 < best_so_far 时无视禁忌",
    "  这是 TS 里唯一「打破记忆」的合法途径",
):
    print(" ", line)

print("\n== SA vs TS vs 爬山 ==")
print(f"  {'方法':<12}{'跳出局部最优':<18}{'参数':<22}{'内存'}")
for row in (("爬山", "不能", "无", "O(1)"),
            ("模拟退火", "概率接受劣解", "T0/α/L", "O(1)"),
            ("禁忌搜索", "记忆禁止回退", "tenure/iterations", "O(tenure)")):
    print(f"  {row[0]:<12}{row[1]:<18}{row[2]:<22}{row[3]}")

print("\n== 局部搜索增强技巧 ==")
for line in [
    "  增量 delta 评估：单步从 O(E) 降到 O(deg)（第715课）",
    "  候选列表：只采样部分邻域，减小每步开销",
    "  变邻域搜索 VNS：卡住时切换到另一种邻域结构",
    "  扰动重启：对当前最优做大力度随机扰动后再爬山（ILS）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 VNS：交替使用「改单点颜色」与「交换两点颜色」两种邻域。
# 2. 给禁忌表加「频率记忆」，长期频繁出现的移动额外惩罚（多样化）。
# 3. 把 TS 用到第716课的 TSP 上，与 SA 比较解质量。
# 4. 思考：为什么禁忌表存「移动属性」而不是「完整解」？
