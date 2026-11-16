# ===== 第778课：博弈论与机制设计-综合案例-拍卖平台模拟器 =====
# 知识点：
#   - 综合串起本章：策略式博弈 -> 拍卖规则 -> 激励相容 -> 收入/福利分析 -> 机制比较
#   - 平台视角：跑多场拍卖，统计卖家收入、社会福利、成交率、诚实率
#   - 对比一价 / 二价 / 带保留价二价 / 全支付拍卖的收益与激励
#   - 竞价者策略：诚实 / 固定压价 / 学式最优反应（对历史分布做最优响应）
#   - 用蒙特卡洛估计期望收入，验证收入等价定理的适用条件
#   - 全部标准库 + 固定 seed，纯内存、离线可运行
# 依赖：无（标准库）
import random
import statistics

VAL_RANGE = (10, 100)


def first_price(bids):
    ranked = sorted(bids, key=lambda x:-x[1])
    return ranked[0][0], ranked[0][1], ranked[0][1]      # 赢家, 支付, 第二价(参考)

def second_price(bids):
    ranked = sorted(bids, key=lambda x:-x[1])
    return ranked[0][0], ranked[1][1], ranked[1][1]

def second_price_reserve(bids, reserve):
    ranked = sorted(bids, key=lambda x:-x[1])
    if ranked[0][1] < reserve:
        return None, 0, ranked[0][1]                     # 流拍
    pay = max(reserve, ranked[1][1])
    return ranked[0][0], pay, ranked[1][1]

def all_pay(bids):
    """全支付拍卖：所有人都要付自己的出价，最高者得物品。"""
    ranked = sorted(bids, key=lambda x:-x[1])
    # 返回赢家、赢家支付、总支付（用于收入统计）
    return ranked[0][0], ranked[0][1], sum(b for _,b in bids)


MECHANISMS = {
    "一价密封": lambda bids: first_price(bids),
    "二价密封": lambda bids: second_price(bids),
    "二价+保留价": lambda bids: second_price_reserve(bids, 60),
    "全支付": lambda bids: all_pay(bids),
}


def run_auction(mechanism, values, strategies, reserve=60, reserve_override=None):
    if reserve_override is not None:
        reserve = reserve_override
    """values: {名字: 真实估值}, strategies: {名字: 报价函数}。"""
    bids = [(n, max(0, strategies[n](v))) for n, v in values.items()]
    if mechanism == "全支付":
        winner, pay, revenue = all_pay(bids)
        welfare = values[winner]
        utilities = {n: (values[n] if n==winner else 0) - b for n,b in bids}
        return {"winner":winner, "revenue":revenue, "welfare":welfare,
                "sold": True, "utilities":utilities, "pay":pay}
    if mechanism == "二价+保留价":
        winner, pay, second = second_price_reserve(bids, reserve)
        sold = winner is not None
    elif mechanism == "二价密封":
        winner, pay, second = second_price(bids); sold = True
    else:
        winner, pay, second = first_price(bids); sold = True
    welfare = values[winner] if sold else 0
    utilities = {n: ((values[n]-pay) if n==winner else 0) for n in values}
    return {"winner":winner, "revenue":pay, "welfare":welfare,
            "sold":sold, "utilities":utilities, "pay":pay}


def simulate(mechanism, n_bidders=4, rounds=3000, seed=7, strategy="truthful",
             reserve_override=None):
    rng = random.Random(seed)
    revenues, welfares, sold_count = [], [], 0
    for _ in range(rounds):
        values = {f"B{i}": rng.uniform(*VAL_RANGE) for i in range(n_bidders)}
        if strategy == "truthful":
            strat = {n: (lambda v: v) for n in values}
        elif strategy == "shade":
            strat = {n: (lambda v: v*0.8) for n in values}
        else:
            strat = {n: (lambda v: v) for n in values}
        r = run_auction(mechanism, values, strat, reserve_override=reserve_override)
        revenues.append(r["revenue"]); welfares.append(r["welfare"])
        sold_count += int(r["sold"])
    return {"mean_revenue": statistics.fmean(revenues),
            "mean_welfare": statistics.fmean(welfares),
            "sell_rate": sold_count/rounds}


print("== 单场拍卖示例 ==")
values = {"B0": 82.3, "B1": 65.1, "B2": 47.8, "B3": 91.0}
truth = {n: (lambda v: v) for n in values}
shade = {n: (lambda v: v*0.8) for n in values}
for name in MECHANISMS:
    r = run_auction(name, values, truth)
    print(f"  {name:<12}: 赢家={r['winner']}, 卖家收入={r['revenue']:.2f}, "
          f"社会福利={r['welfare']:.2f}, 成交={r['sold']}")

print("\n== 诚实性：二价下压价会变差吗 ==")
for name, strat in (("诚实", truth), ("八折压价", shade)):
    r = run_auction("二价密封", values, strat)
    # B3 真实估值 91
    print(f"  {name}: B3 效用={r['utilities']['B3']:.2f}, 赢家={r['winner']}")
print("  二价下压价只可能丢失本可赢的交易，不改变支付 -> 诚实占优")

print("\n== 一价下压价才有意义 ==")
for name, strat in (("诚实", truth), ("八折压价", shade)):
    r = run_auction("一价密封", values, strat)
    print(f"  {name}: 赢家={r['winner']}, B3 效用={r['utilities']['B3']:.2f}")

print("\n== 3000 场蒙特卡洛：期望收入与福利 ==")
for mech in MECHANISMS:
    s = simulate(mech, rounds=3000, seed=7)
    print(f"  {mech:<12}: 期望收入={s['mean_revenue']:.2f}, "
          f"期望福利={s['mean_welfare']:.2f}, 成交率={s['sell_rate']:.1%}")
print("  收入等价：风险中性下，一价(压价后)与二价期望收入接近")
print("  保留价提高单场收入但牺牲成交率；全支付收入高但参与者风险大")

print("\n== 保留价扫描（二价+保留价）==")
for reserve in (0, 30, 50, 60, 70, 85, 100):
    # 用 uniform(10,100)、4 人：最高价期望约 82，次高约 64
    s = simulate("二价+保留价", rounds=1500, seed=7, reserve_override=reserve)
    print(f"  reserve={reserve:>3}: 期望收入={s['mean_revenue']:.2f} "
          f"成交率={s['sell_rate']:.1%}")
print("  最优保留价需权衡「多收一点」与「流拍损失」；Myerson 给出解析解")

print("\n== 策略演化：简单最优反应 ==")
# 重复一价拍卖，玩家根据历史「最高对手出价」调整自己的加价
def adaptive_first_price(rounds=2000, seed=3):
    rng = random.Random(seed)
    shade_factor = 0.5
    revenues = []
    for t in range(rounds):
        vals = {f"B{i}": rng.uniform(*VAL_RANGE) for i in range(4)}
        bids = [(n, v*(1-shade_factor*rng.uniform(0.3,0.7))) for n,v in vals.items()]
        w, pay, _ = first_price(bids)
        revenues.append(pay)
        # 观察：压价系数缓慢向「次高价/最高价」靠拢
        target = 1 - (sorted([b for _,b in bids])[-2] / max(b for _,b in bids))
        shade_factor += 0.01*(target - shade_factor)
    return statistics.fmean(revenues), shade_factor
rev, f = adaptive_first_price()
print(f"  自适应压价后：平均压价系数≈{f:.3f}, 卖家平均收入≈{rev:.2f}")
print("  学习者会收敛到贝叶斯纳什均衡的压价策略（收入等价的动态版）")

print("\n== 分层回顾 ==")
for line in [
    "  博弈层  : 收益矩阵、最优反应、纳什均衡（第771课）",
    "  机制层  : 拍卖规则决定支付与分配（第773课）",
    "  激励层  : DSIC / 显示原理判断能否说真话（第774课）",
    "  评价层  : 收入、福利、成交率、诚实率多维对比",
    "  动态层  : 重复互动与学习（第772课）",
    "  扩展层  : 匹配市场（第775课）、公共品（第776课）、拥塞（第777课）",
]:
    print("  -", line)

print("\n== 与真实平台的差距 ==")
for line in [
    "  假设独立私有估值、风险中性、无预算约束、无串谋",
    "  真实广告拍卖还要处理质量分、保留价、点击率预估、预算平滑",
    "  未做机制学到的均衡求解（用蒙特卡洛 + 简单自适应代替）",
    "  目标是把本章概念串成可量化的机制比较框架",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 加入 GSP 多广告位拍卖，验证它不是 DSIC（第773课）。
# 2. 实现 Myerson 最优保留价（虚拟估值 = v - (1-F)/f），对比扫描结果。
# 3. 允许竞价者串谋（压低最高价），测量卖家收入损失。
# 4. 思考：为什么「收入等价定理」在风险厌恶或预算约束下会失效？
