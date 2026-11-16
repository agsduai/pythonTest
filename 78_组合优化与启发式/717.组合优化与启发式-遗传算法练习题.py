# ===== 第717课：组合优化与启发式-遗传算法 =====
# 知识点：
#   - 遗传算法 GA：维护一个「种群」，通过选择/交叉/变异逐代进化
#   - 编码：0/1 串（背包）、排列（TSP）、实数向量；编码决定交叉算子
#   - 适应度 fitness：直接由目标函数映射，选择概率与其成正比
#   - 选择：轮盘赌 / 锦标赛；精英保留 elitism 防止最优解丢失
#   - 交叉：单点 / 均匀 / OX（排列专用）；变异：位翻转 / 交换 / 逆序
#   - 参数：种群大小、交叉率、变异率、代数；过早收敛是常见问题
# 依赖：无（标准库）
import random

# 0/1 背包：在容量限制下最大化价值
ITEMS = [("笔记本", 3, 4), ("相机", 4, 5), ("水壶", 2, 3), ("帐篷", 6, 8),
         ("食物", 3, 4), ("衣服", 2, 2), ("地图", 1, 2), ("手电", 2, 3),
         ("药品", 2, 4), ("书籍", 3, 3), ("工具", 4, 6), ("睡袋", 5, 7)]
CAPACITY = 15
N = len(ITEMS)


def fitness(ch):
    weight = sum(ITEMS[i][1] for i, b in enumerate(ch) if b)
    value = sum(ITEMS[i][2] for i, b in enumerate(ch) if b)
    if weight > CAPACITY:
        return value - 3 * (weight - CAPACITY)      # 软惩罚（允许超重但扣分）
    return value


def weight_of(ch):
    return sum(ITEMS[i][1] for i, b in enumerate(ch) if b)


def value_of(ch):
    return sum(ITEMS[i][2] for i, b in enumerate(ch) if b)


def tournament(pop, fits, rng, k=3):
    cand = rng.sample(range(len(pop)), k)
    return pop[max(cand, key=lambda i: fits[i])][:]


def crossover(a, b, rng, rate=0.8):
    if rng.random() > rate or N < 2:
        return a[:], b[:]
    p = rng.randrange(1, N)
    return a[:p] + b[p:], b[:p] + a[p:]


def mutate(ch, rng, rate=0.05):
    return [b ^ 1 if rng.random() < rate else b for b in ch]


def ga(pop_size=40, generations=80, elite=2, seed=7, mutation_rate=0.05):
    rng = random.Random(seed)
    pop = [[rng.randrange(2) for _ in range(N)] for _ in range(pop_size)]
    best_ch, best_fit = None, -1
    history = []
    for gen in range(generations):
        fits = [fitness(ch) for ch in pop]
        idx = max(range(pop_size), key=lambda i: fits[i])
        if fits[idx] > best_fit:
            best_ch, best_fit = pop[idx][:], fits[idx]
        history.append((gen, max(fits), sum(fits) / pop_size))
        new = [pop[i][:] for i in sorted(range(pop_size),
                                        key=lambda i: -fits[i])[:elite]]
        while len(new) < pop_size:
            p1 = tournament(pop, fits, rng)
            p2 = tournament(pop, fits, rng)
            c1, c2 = crossover(p1, p2, rng)
            new.append(mutate(c1, rng, mutation_rate))
            if len(new) < pop_size:
                new.append(mutate(c2, rng, mutation_rate))
        pop = new
    return best_ch, best_fit, history


print("== 0/1 背包建模 ==")
print(f"  物品 {N} 件，容量={CAPACITY}，解=0/1 串，目标=总价值最大")
print(f"  搜索空间 2^{N} = {2**N}")
print("  超重采用软惩罚，让搜索能穿越不可行区域")

print("\n== 穷举全局最优（基线）==")
best_all, best_ch_all, best_w = -1, None, 0
for mask in range(1 << N):
    ch = [(mask >> i) & 1 for i in range(N)]
    w = weight_of(ch)
    if w <= CAPACITY:
        v = value_of(ch)
        if v > best_all:
            best_all, best_ch_all, best_w = v, ch, w
print(f"  全局最优价值={best_all} 重量={best_w} 解={best_ch_all}")

print("\n== 遗传算法运行 ==")
ch, fit, hist = ga(seed=7)
print(f"  最优适应度={fit} 重量={weight_of(ch)} 价值={value_of(ch)}")
print(f"  达到全局最优: {fit == best_all and weight_of(ch) <= CAPACITY}")
print("  选中的物品:", [ITEMS[i][0] for i, b in enumerate(ch) if b])

print("\n== 收敛曲线（每 10 代）==")
for gen, mx, avg in hist[::10]:
    print(f"  gen={gen:>3}: 最优={mx:<4} 平均={avg:.2f}")

print("\n== 参数敏感性 ==")
for size, gens, mr in ((20, 50, 0.05), (40, 80, 0.05), (40, 80, 0.2),
                       (80, 120, 0.02)):
    c, f, _ = ga(pop_size=size, generations=gens, seed=11, mutation_rate=mr)
    print(f"  pop={size:>3} gen={gens:>3} 变异率={mr:<5}: 最优={f} "
          f"{'命中' if f == best_all else '未命中'}")

print("\n== 精英保留的作用 ==")
for elite in (0, 2, 8):
    c, f, _ = ga(elite=elite, seed=5)
    print(f"  elite={elite}: 最优={f}")
print("  elite=0 时最优解可能被交叉/变异破坏；过大则种群多样性不足")

print("\n== 选择压力：锦标赛 k ==")
for k in (2, 3, 5, 10):
    rng = random.Random(1)
    pop = [[rng.randrange(2) for _ in range(N)] for _ in range(30)]
    fits = [fitness(c) for c in pop]
    chosen = [tournament(pop, fits, rng, k=k) for _ in range(100)]
    avg = sum(fitness(c) for c in chosen) / len(chosen)
    print(f"  k={k:>2}: 被选中个体平均适应度={avg:.2f}（越大选择压力越强）")

print("\n== 过早收敛（premature convergence）==")
for line in (
    "  现象: 种群很快几乎一样，平均≈最优，之后长期停滞",
    "  原因: 选择压力过大 / 变异率过低 / 种群太小",
    "  对策: 提高变异率、增大种群、适应度共享、随机移民",
    "  诊断: 监控种群汉明距离多样性",
):
    print(" ", line)

print("\n== GA vs SA / 爬山 ==")
for line in (
    "  爬山/SA: 单点轨迹，内存小，邻域结构决定效果",
    "  GA     : 种群并行探索，交叉能组合不同解的「优片段」",
    "  GA 参数更多、评估次数更多，但天然易并行",
    "  实际问题常混合使用：GA 找区域 + 局部搜索精修（memetic）",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 实现均匀交叉与两点交叉，对比单点交叉的收敛速度。
# 2. 给 TSP 排列编码实现 OX 交叉，并验证子代是合法排列（不重复不遗漏）。
# 3. 增加「种群多样性」监控，在过低时自动提高变异率。
# 4. 思考：为什么交叉算子必须与编码方式匹配，乱用会产生非法解？
