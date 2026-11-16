# ===== 第716课：组合优化与启发式-模拟退火 =====
# 知识点：
#   - 模拟退火 SA：以概率 exp(-Δ/T) 接受「更差」的解，从而跳出局部最优
#   - 温度 T 从高到低按冷却表衰减；高温时几乎随机游走，低温时近似爬山
#   - Metropolis 准则：Δ<0 必接受，Δ>0 以 exp(-Δ/T) 接受（最小化问题）
#   - 冷却系数 α、初温 T0、终温、每温度迭代次数 L 是四个关键参数
#   - 与第678课马尔可夫链呼应：SA 是时变的 MCMC 搜索
#   - 用 TSP 做案例：2-opt 邻域（反转一段路径），目标为总路程最小
# 依赖：无（标准库）
import math
import random

# 8 个城市的坐标（人为构造，便于在小规模验证）
CITIES = [(0,0),(4,1),(6,5),(3,7),(-1,6),(-4,3),(-3,-2),(2,-3)]
N = len(CITIES)


def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


def tour_length(tour):
    return sum(dist(CITIES[tour[i]], CITIES[tour[(i+1) % N]])
               for i in range(N))


def two_opt(tour, i, j):
    """反转 tour[i:j+1] 得到邻域解。"""
    return tour[:i] + tour[i:j+1][::-1] + tour[j+1:]


def random_tour(rng):
    t = list(range(N))
    rng.shuffle(t)
    return t


def hill_climb_2opt(start, rng):
    cur, cur_v = start[:], tour_length(start)
    while True:
        best, best_v = None, cur_v
        for i in range(N - 1):
            for j in range(i + 1, N):
                cand = two_opt(cur, i, j)
                v = tour_length(cand)
                if v < best_v:
                    best, best_v = cand, v
        if best is None:
            break
        cur, cur_v = best, best_v
    return cur, cur_v


def simulated_annealing(start, T0=20.0, alpha=0.995, Tmin=0.01, L=60, seed=0):
    rng = random.Random(seed)
    cur, cur_v = start[:], tour_length(start)
    best, best_v = cur[:], cur_v
    T, accepted, steps = T0, 0, 0
    trace = []
    while T > Tmin:
        for _ in range(L):
            i, j = sorted(rng.sample(range(N), 2))
            cand = two_opt(cur, i, j)
            v = tour_length(cand)
            delta = v - cur_v
            if delta < 0 or rng.random() < math.exp(-delta / T):
                cur, cur_v = cand, v
                accepted += 1
                if v < best_v:
                    best, best_v = cand[:], v
            steps += 1
        trace.append((round(T, 3), round(cur_v, 2), round(best_v, 2)))
        T *= alpha
    return best, best_v, accepted / steps, trace


print("== TSP 建模 ==")
print(f"  城市 {N} 个，解=排列，目标=回路总长，邻域=2-opt 反转")
print(f"  全排列数 {math.factorial(N)}（已超出穷举舒适区）")

rng = random.Random(3)
start = random_tour(rng)
print(f"  随机起点路程={tour_length(start):.2f}")

print("\n== 2-opt 爬山：容易卡局部最优 ==")
hc, hv = hill_climb_2opt(start, rng)
print(f"  爬山结果={hv:.2f}  路径={hc}")

print("\n== 模拟退火（不同初温）==")
for T0 in (1.0, 5.0, 20.0, 50.0):
    sol, val, rate, trace = simulated_annealing(start, T0=T0, alpha=0.99,
                                                 Tmin=0.05, L=40, seed=7)
    print(f"  T0={T0:<5}: 最优={val:.2f} 接受率={rate:.1%} "
          f"温度档数={len(trace)}")

print("\n== 冷却曲线（T0=20）==")
_, _, _, trace = simulated_annealing(start, T0=20, alpha=0.99, Tmin=0.05,
                                     L=40, seed=7)
for t, cur, best in trace[::max(1, len(trace)//8)][:9]:
    print(f"  T={t:<8} 当前={cur:<8} 历史最优={best}")

print("\n== 多次独立运行：结果分布 ==")
results = [simulated_annealing(random_tour(random.Random(s)), T0=20,
                               alpha=0.99, Tmin=0.05, L=40, seed=s)[1]
           for s in range(15)]
print(f"  15 次: 最好={min(results):.2f} 最差={max(results):.2f} "
      f"均值={sum(results)/len(results):.2f}")
print(f"  爬山基线={hv:.2f}")
print("  随机化算法要报告分布，而不是只报一次的最好结果")

print("\n== 参数敏感性 ==")
for alpha in (0.95, 0.99, 0.999):
    sol, val, rate, tr = simulated_annealing(start, T0=20, alpha=alpha,
                                             Tmin=0.05, L=40, seed=7)
    print(f"  α={alpha:<6}: 最优={val:.2f} 步数≈{len(tr)*40} 接受率={rate:.1%}")
print("  α 越接近 1 冷却越慢、搜索越充分，但耗时越长")

print("\n== Metropolis 接受概率 ==")
for T in (20, 5, 1, 0.1):
    probs = [round(math.exp(-d / T), 4) for d in (0.5, 1, 2, 5)]
    print(f"  T={T:<5}: Δ=0.5/1/2/5 的接受概率={probs}")

print("\n== 与爬山法的关系 ==")
for line in (
    "  T→0 时 exp(-Δ/T)→0，SA 退化为爬山",
    "  T→∞ 时几乎全接受，变成随机游走",
    "  关键是「先探索、后收敛」的温度安排",
    "  SA 不保证全局最优，但工程上常显著优于纯爬山",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  初温可按「初始邻域 Δ 的平均值」自适应设定",
    "  记录历史最优 best，别把末态当答案（末态可能正处上坡）",
    "  用可复现 seed；报告多次运行的统计量",
    "  更大规模用并行 tempering / 遗传算法 / LKH 等专业求解器",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给 SA 增加「重升温 reheating」，在收敛后重新升温再搜一轮。
# 2. 用相邻交换（swap）替代 2-opt 作为邻域，对比收敛质量。
# 3. 实现自适应初温：采样 100 个邻域 Δ，令初始接受率约 0.8。
# 4. 思考：为什么 SA 要记录历史最优，而不是返回最后当前解？
