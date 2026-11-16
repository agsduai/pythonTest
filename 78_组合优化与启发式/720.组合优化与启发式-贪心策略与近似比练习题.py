# ===== 第720课：组合优化与启发式-贪心策略与近似比 =====
# 知识点：
#   - 贪心：每步取「当前看起来最好」的选择，不回退；快但不一定最优
#   - 近似比 approximation ratio：算法解 / 最优解（最小化）的上界保证
#   - 经典反例：0/1 背包按价值/按重量/按密度贪心都可能严重偏离最优
#   - 有保证的贪心：区间调度按结束时间、Huffman 编码、Dijkstra、Kruskal
#   - 集合覆盖：贪心近似比 H(n)≈ln n，且这是已知最好保证（除非 P=NP）
#   - 用「小规模穷举 + 随机实例」实测经验比，别只信理论最坏情况
# 依赖：无（标准库）
import math
import random

print("== 0/1 背包：三种贪心都可能翻车 ==")
ITEMS = [(10, 60), (20, 100), (30, 120)]      # (重量, 价值)
CAP = 50

def brute_knapsack(items, cap):
    best = 0
    for mask in range(1 << len(items)):
        w = sum(items[i][0] for i in range(len(items)) if (mask >> i) & 1)
        if w <= cap:
            v = sum(items[i][1] for i in range(len(items)) if (mask >> i) & 1)
            best = max(best, v)
    return best

def greedy_knapsack(items, cap, key):
    order = sorted(range(len(items)), key=lambda i: -key(items[i]))
    w = v = 0
    for i in order:
        if w + items[i][0] <= cap:
            w += items[i][0]; v += items[i][1]
    return v

opt = brute_knapsack(ITEMS, CAP)
print(f"  物品(重量,价值)={ITEMS} 容量={CAP} 最优={opt}")
for name, key in (("按价值", lambda it: it[1]),
                  ("按最轻", lambda it: -it[0]),
                  ("按价值密度", lambda it: it[1]/it[0])):
    v = greedy_knapsack(ITEMS, CAP, key)
    print(f"  {name:<12}: 得到={v:>3} 近似比={v/opt:.2f} "
          f"{'（此例恰好最优）' if v == opt else '（次优）'}")

# 构造一个让「按价值」贪心明显失败的实例
TRAP = [(10, 60), (20, 100), (30, 120), (1, 2), (1, 2), (1, 2)]
opt2 = brute_knapsack(TRAP, 50)
print(f"\n  专门构造的实例容量=50 最优={opt2}")
for name, key in (("按价值", lambda it: it[1]),
                  ("按价值密度", lambda it: it[1]/it[0])):
    v = greedy_knapsack(TRAP, CAP, key)
    print(f"    {name:<10}: 得到={v} 近似比={v/opt2:.2f}")
print("  0/1 背包贪心没有常数近似比保证（分数背包才有）")

print("\n== 有保证的贪心：区间调度 ==")
INTERVALS = [(1,3),(2,5),(3,9),(0,2),(5,7),(8,10),(6,9),(1,4),(4,6)]
def interval_schedule(intervals):
    chosen, end = [], -1
    for s, e in sorted(intervals, key=lambda x: x[1]):
        if s >= end:
            chosen.append((s, e)); end = e
    return chosen
chosen = interval_schedule(INTERVALS)
print(f"  按结束时间贪心选出 {len(chosen)} 个: {chosen}")
print("  该策略可证明是最优的（最早结束给后面留最多空间）")

print("\n== 集合覆盖：贪心近似比 ≈ ln n ==")
UNIVERSE = set(range(20))
SETS = [set(random.Random(s).sample(range(20), random.Random(s).randint(3, 8)))
        for s in range(12)]
# 保证能覆盖全部（补一个全集）
SETS.append(set(UNIVERSE))

def greedy_set_cover(universe, sets):
    remaining, chosen = set(universe), []
    while remaining:
        best = max(range(len(sets)), key=lambda i: len(sets[i] & remaining))
        gain = sets[best] & remaining
        if not gain:
            break
        chosen.append(best)
        remaining -= gain
    return chosen

sol = greedy_set_cover(UNIVERSE, SETS)
# 精确最优（集合数少，穷举）
best_exact = len(SETS)
for mask in range(1 << len(SETS)):
    if sum(1 for i in range(len(SETS)) if (mask >> i) & 1) >= best_exact:
        continue
    covered = set()
    for i in range(len(SETS)):
        if (mask >> i) & 1:
            covered |= SETS[i]
    if covered == UNIVERSE:
        best_exact = bin(mask).count("1")
print(f"  全集 20 个元素，{len(SETS)} 个候选集合")
print(f"  贪心选 {len(sol)} 个，精确最优 {best_exact} 个，"
      f"经验比={len(sol)/best_exact:.2f}")
print(f"  理论最坏比 H(20)={sum(1/i for i in range(1, 21)):.2f} ≈ ln(20)+γ")

print("\n== 随机实例上的经验近似比 ==")
def random_instance(n, cap, seed):
    r = random.Random(seed)
    return [(r.randint(1, 15), r.randint(1, 30)) for _ in range(n)]

ratios = []
for seed in range(200):
    items = random_instance(10, 40, seed)
    o = brute_knapsack(items, 40)
    g = greedy_knapsack(items, 40, lambda it: it[1]/it[0])
    if o:
        ratios.append(g / o)
print(f"  200 个 10 物品实例: 平均比={sum(ratios)/len(ratios):.3f} "
      f"最差比={min(ratios):.3f} 达到最优的比例="
      f"{sum(r == 1.0 for r in ratios)/len(ratios):.1%}")
print("  理论最坏情况很差，但平均表现常不错 -> 工程上仍值得用")

print("\n== 近似算法 vs 启发式 ==")
for line in (
    "  近似算法: 有多项式时间 + 可证明的最坏情况保证",
    "  启发式  : 实践效果好，但无理论保证（SA/GA/禁忌）",
    "  两者可叠加: 用近似解做初始解，再用局部搜索改进",
    "  报告结果时区分「经验比」与「理论近似比」",
):
    print(" ", line)

print("\n== 贪心何时有效 ==")
for line in [
    "  拟阵结构（matroid）上，贪心对加权问题是最优的：Kruskal MST 是典型",
    "  具有「贪心选择性质 + 最优子结构」的问题才可证明最优",
    "  反例检验: 小规模穷举找 counter-example，别凭直觉",
    "  交换论证（exchange argument）是证明贪心最优的常用手法",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 用交换论证证明「区间调度按结束时间」的最优性。
# 2. 构造一个让「按价值密度」贪心近似比任意差（趋近 0）的背包实例。
# 3. 实现 Huffman 编码（贪心 + 优先堆），验证带权路径长度最小。
# 4. 思考：为什么「平均表现好」不足以替代「最坏情况保证」？
