# ===== 第682课：随机模拟与蒙特卡洛-综合案例-库存策略风险模拟器 =====
# 知识点：
#   - 综合串起本章：可复现 RNG、分布采样、蒙特卡洛、方差缩减、置信区间、DES
#   - 库存问题：需求随机、补货有提前期、(s, S) 策略：低于 s 就补到 S
#   - 每天事件：到货 -> 满足需求 -> 记录缺货/持有 -> 决定是否下单
#   - 风险指标：服务水平（不缺货天数占比）、平均库存、缺货量、总成本分布 P90
#   - 用对偶变量降低对比两种策略时的方差；用 bootstrap 给成本均值做 CI
#   - 全部可注入 seed 与参数，纯函数 simulate() 返回结构化结果，离线可运行
# 依赖：无（标准库）
import math
import random
import statistics
from dataclasses import dataclass, field

COST_HOLD = 0.5        # 每件每天持有成本
COST_SHORT = 8.0       # 每件缺货罚金
COST_ORDER = 20.0      # 每次下单固定成本


@dataclass
class Config:
    days: int = 365
    s: int = 20          # 再订货点
    S: int = 60          # 补到水平
    lead: int = 3        # 提前期（天）
    lam: float = 12.0    # 泊松需求均值
    seed: int = 0


@dataclass
class Result:
    service: float = 0.0
    avg_inventory: float = 0.0
    total_short: int = 0
    orders: int = 0
    cost: float = 0.0
    daily_inventory: list = field(default_factory=list)


def simulate(cfg, demand_seq=None):
    """(s,S) 库存策略的离散事件模拟；demand_seq 可注入便于单测。"""
    rng = random.Random(cfg.seed)
    demand = demand_seq or [None] * cfg.days
    inv = cfg.S
    pending = []         # (到货日, 数量)
    short_total, orders = 0, 0
    hold_total = 0
    no_short_days = 0
    history = []

    for day in range(cfg.days):
        # 1) 到货
        arrivals = [q for d, q in pending if d == day]
        for q in arrivals:
            inv += q
        pending = [(d, q) for d, q in pending if d > day]

        # 2) 需求（泊松近似：用 Knuth 乘积法，避免大 λ 的循环开销）
        if demand[day] is None:
            L = math.exp(-cfg.lam)
            k, p = 0, 1.0
            while True:
                p *= rng.random()
                if p <= L:
                    break
                k += 1
            d = k
        else:
            d = demand[day]
        sold = min(inv, d)
        inv -= sold
        short = d - sold
        short_total += short
        if short == 0:
            no_short_days += 1

        # 3) 成本与记录
        hold_total += inv * COST_HOLD
        history.append(inv)

        # 4) 补货决策（在途 + 现货 < s 时下单）
        in_transit = sum(q for _, q in pending)
        if inv + in_transit < cfg.s:
            qty = cfg.S - inv - in_transit
            pending.append((day + cfg.lead, qty))
            orders += 1

    cost = hold_total + short_total * COST_SHORT + orders * COST_ORDER
    return Result(no_short_days / cfg.days, hold_total / COST_HOLD / cfg.days,
                  short_total, orders, cost, history)


def bootstrap_ci(results, B=4000, seed=99):
    r = random.Random(seed)
    n = len(results)
    means = []
    for _ in range(B):
        means.append(statistics.fmean(results[r.randrange(n)].cost for _ in range(n)))
    means.sort()
    return means[int(B * 0.025)], means[int(B * 0.975)]


print("== 基准策略 (s=20, S=60, lead=3) ==")
base = simulate(Config(seed=7))
print(f"  服务水平={base.service:.1%}  平均库存={base.avg_inventory:.1f} 件")
print(f"  总缺货={base.total_short} 件  下单={base.orders} 次  总成本={base.cost:.0f}")

print("\n== 策略对比（同一随机流，减少对比噪声）==")
print(f"  {'s':<5}{'S':<5}{'服务水平':<12}{'平均库存':<12}{'缺货':<9}{'成本':<10}")
for s, S in ((10, 60), (20, 60), (30, 60), (20, 40), (20, 80), (40, 100)):
    r = simulate(Config(s=s, S=S, seed=7))
    print(f"  {s:<5}{S:<5}{r.service:<12.1%}{r.avg_inventory:<12.1f}"
          f"{r.total_short:<9}{r.cost:<10.0f}")
print("  提高 s/S 提升服务水平，但持有成本上升 -> 需要找成本最优点")

print("\n== 30 次独立重复的成本分布与风险指标 ==")
runs = [simulate(Config(seed=100 + i)) for i in range(30)]
costs = sorted(r.cost for r in runs)
print(f"  均值={statistics.fmean(costs):.0f}  标准差={statistics.pstdev(costs):.0f}")
print(f"  P50={costs[15]:.0f}  P90={costs[int(30*0.9)]:.0f}  "
      f"最差={costs[-1]:.0f}")
lo, hi = bootstrap_ci(runs, B=2000)
print(f"  均值 95% bootstrap CI = [{lo:.0f}, {hi:.0f}]")
print("  P90（VaR 思路）比均值更能反映坏年份的风险")

print("\n== 持有成本 vs 缺货罚金的权衡（同一轨迹，换权重重算）==")
r = simulate(Config(s=20, S=60, seed=7))
hold_part = r.avg_inventory * COST_HOLD * 365
order_part = r.orders * COST_ORDER
for cs in (3.0, 8.0, 20.0):
    total = hold_part + r.total_short * cs + order_part
    print(f"  缺货罚金={cs:<5}: 总成本={total:.0f}（缺货 {r.total_short} 件 × {cs}）")
print("  罚金越高，缺货越不可接受，最优策略应越保守（更大的 s/S）")

print("\n== 提前期的影响 ==")
for lead in (1, 3, 7, 14):
    r = simulate(Config(lead=lead, seed=7))
    print(f"  lead={lead:>2} 天: 服务水平={r.service:.1%} 缺货={r.total_short:>4} 件")
print("  提前期越长，需求不确定性越大，需要更多安全库存（第44/53章）")

print("\n== 可复现性验证 ==")
a = simulate(Config(seed=123))
b = simulate(Config(seed=123))
print("  同 seed 结果一致:", (a.service, a.cost, a.total_short) ==
      (b.service, b.cost, b.total_short))
c = simulate(Config(seed=124))
print("  不同 seed 结果不同:", a.cost != c.cost)

print("\n== 关卡：注入确定性需求做单测 ==")
fixed = [10] * 30
det = simulate(Config(days=30, s=20, S=60, seed=0), demand_seq=fixed)
print(f"  固定每天需求 10: 服务水平={det.service:.1%} 总缺货={det.total_short}")
print("  需求恒定可手算验证，是检验模拟器正确性的好办法")

print("\n== 分层回顾 ==")
for line in [
    "  RNG 层   : Random(seed) 独立实例，保证可复现（第675课）",
    "  采样层   : 泊松需求用 Knuth 乘积法（第676课）",
    "  模拟层   : 逐日离散事件，事件顺序固定（第679课）",
    "  统计层   : 多跑 + bootstrap CI + P90 风险指标（第680课）",
    "  决策层   : 参数扫描找成本/服务水平平衡，结论带不确定性",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 用对偶变量让「策略 A vs B」共享需求随机数，缩小对比的置信区间。
# 2. 增加「需求随季节波动」的 λ(t)，重新评估最优 (s,S)。
# 3. 实现网格搜索，找到使期望总成本最小的 (s,S) 组合。
# 4. 思考：为什么评估库存策略要看 P90 成本，而不只看平均成本？
