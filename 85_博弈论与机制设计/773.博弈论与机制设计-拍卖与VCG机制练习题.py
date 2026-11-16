# ===== 第773课：博弈论与机制设计-拍卖与 VCG 机制 =====
# 知识点：
#   - 四种标准拍卖：英式(升价)、荷式(降价)、一价密封、二价密封(Vickrey)
#   - 二价拍卖：出最高者得、付第二高价；说真话是弱占优策略
#   - 机制设计：反过来设计规则，让自利参与者在均衡下实现社会目标
#   - 策略防护 strategyproof / 激励相容 IC：如实报告自己的估值是占优策略
#   - VCG = 二价拍卖的一般化：按「对他人造成的外部性」付费
#   - VCG 性质：社会福利最大化 + 占优策略诚实 + 个人理性（但可能收入低/易串谋）
# 依赖：无（标准库）
from itertools import product

print("== 二价拍卖：说真话是占优策略 ==")
def second_price(bids):
    """bids: [(名字, 出价)] -> (赢家, 支付价, 真实收益)。"""
    ranked = sorted(bids, key=lambda x: -x[1])
    winner, pay = ranked[0][0], ranked[1][1]
    return winner, pay

TRUE_VALUE = 70
for bid in (40, 60, 70, 80, 95):
    others = [("B", 55), ("C", 30)]
    w, pay = second_price([("A", bid)] + others)
    utility = (TRUE_VALUE - pay) if w == "A" else 0
    print(f"  我真实估值={TRUE_VALUE}, 出价={bid:>3}: 赢={w=='A'}, "
          f"支付={pay if w=='A' else 0}, 效用={utility}")
print("  出价 < 55 会输掉本可赢的交易；出价 > 70 可能以 >70 的价格赢 -> 都变差，说真话最优")

print("\n== 一价拍卖：需要压价（不诚实）==")
for bid in (50, 55, 60, 70):
    others = [("B", 55), ("C", 30)]
    ranked = sorted([("A",bid)]+others, key=lambda x:-x[1])
    win = ranked[0][0] == "A"
    utility = (TRUE_VALUE - bid) if win else 0
    print(f"  出价={bid}: 赢={win}, 效用={utility}")
print("  一价拍卖要「低于真实估值、略高于对手」才最优 -> 不激励相容")

print("\n== VCG：单物品拍卖 = 二价 ==")
def vcg_single_item(values):
    """values: {名字: 真实估值}；返回分配、支付、社会福利。"""
    ranked = sorted(values.items(), key=lambda x:-x[1])
    winner = ranked[0][0]
    welfare_with = ranked[0][1]
    # 其他人若没有赢家参与时的最大福利
    welfare_without = max(v for n,v in values.items() if n != winner)
    payment = welfare_without - (welfare_with - values[winner])
    # 化简为第二高价
    return winner, payment, welfare_with

vals = {"A":70, "B":55, "C":30}
w, p, sw = vcg_single_item(vals)
print(f"  估值={vals} -> 赢家={w}, 支付={p}, 社会福利={sw}")
print("  VCG 支付 = 我给别人造成的福利损失 = 第二高价 55")

print("\n== VCG：多物品 / 组合分配 ==")
# 两个相同物品分给 3 人，每人最多 1 个，估值不同
BIDDERS = ["A","B","C"]
def welfare(alloc, v):
    return sum(v[n] for n in alloc)
def vcg_multi(v, k=2):
    # 枚举所有最多 k 人的分配，最大化社会福利
    best_alloc, best_w = (), 0
    for r in range(k+1):
        for combo in product(BIDDERS, repeat=r):
            if len(set(combo)) != r: continue
            a = tuple(sorted(combo))
            wv = welfare(a, v)
            if wv > best_w:
                best_w, best_alloc = wv, a
    payments = {}
    for n in best_alloc:
        others = {m: v[m] for m in v if m != n}
        # 没有 n 时的最优福利（同样枚举）
        w_without = 0
        for r in range(k+1):
            for combo in product(others, repeat=r):
                if len(set(combo)) != r: continue
                w_without = max(w_without, welfare(combo, others))
        others_w = sum(v[m] for m in best_alloc if m != n)
        payments[n] = w_without - others_w
    return best_alloc, payments, best_w

v2 = {"A":100, "B":80, "C":60}
alloc, pays, total = vcg_multi(v2, k=2)
print(f"  估值={v2}, 2 个物品")
print(f"  最优分配={alloc}, 社会福利={total}")
print(f"  VCG 支付={pays}（A 付 60、B 付 60：都是「挤掉 C」的外部性）")
print(f"  各人效用 = 估值 - 支付: "
      f"{ {n: v2[n]-pays.get(n,0) for n in alloc} }")

print("\n== VCG 的诚实性验证 ==")
# A 若虚报低一点，可能失去物品
for fake in (100, 90, 70, 50):
    v3 = dict(v2); v3["A"] = fake
    alloc2, pays2, _ = vcg_multi(v3, k=2)
    u = (v2["A"] - pays2.get("A",0)) if "A" in alloc2 else 0
    print(f"  A 报告 {fake:>3}（真实 100）-> 得标={'A' in alloc2}, 效用={u}")
print("  虚报低可能丢标，虚报高不改变支付（由他人决定）-> 诚实最优")

print("\n== 拍卖形式对比 ==")
print(f"  {'形式':<14}{'支付':<16}{'诚实?':<8}{'收入等价'}")
for row in (("英式升价", "第二高价+ε", "是", "≈二价"),
            ("荷式降价", "自己出价", "否", "≈一价"),
            ("一价密封", "自己出价", "否", "基准"),
            ("二价密封", "第二高价", "是", "≈一价(风险中性)")):
    print(f"  {row[0]:<14}{row[1]:<16}{row[2]:<8}{row[3]}")
print("  收入等价定理：风险中性、独立私有估值下，四种拍卖期望收入相同")

print("\n== VCG 的局限 ==")
for line in (
    "  计算复杂：组合拍卖里求最优分配是 NP 难（第78章）",
    "  收入可能很低（甚至 0），且对串谋/虚假身份（shill bidding）脆弱",
    "  预算不平衡：机制可能要补贴参与者",
    "  实际用「保留价 / 核心定价 / 近似 VCG」修补",
):
    print(" ", line)

print("\n== 应用 ==")
for line in [
    "  搜索广告位分配（GSP，VCG 的近似）、频谱拍卖",
    "  云计算资源定价、区块链 Gas / EIP-1559 机制",
    "  公共项目决策、任务众包激励",
    "  与第771课 NE、第774课显示原理串联",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 GSP（广义第二价格）广告拍卖，验证它不是策略防护的。
# 2. 给组合拍卖加入「保留价」，观察卖家收入变化。
# 3. 用蒙特卡洛验证收入等价定理（一价 vs 二价期望收入）。
# 4. 思考：为什么 VCG 支付等于「给他人造成的福利损失」？
