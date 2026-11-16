# ===== 第774课：博弈论与机制设计-显示原理与激励相容 =====
# 知识点：
#   - 直接机制 direct mechanism：参与者直接报告自己的类型（估值/偏好），机制算结果
#   - 显示原理 revelation principle：任何间接机制的均衡结果，都能被某个「诚实均衡」的直接机制复制
#   - 激励相容 IC（策略防护）：如实报告是占优策略（DSIC）或贝叶斯均衡（BIC）
#   - 个人理性 IR（参与约束）：参与者的期望效用 >= 不参与时的保留效用
#   - 迈尔森引理 Myerson：单参数环境下，分配规则单调 + 支付公式唯一确定 DSIC 机制
#   - 社会选择：不可能定理（Arrow）、Gibbard-Satterthwaite 说明「独裁以外无万能诚实机制」
# 依赖：无（标准库）
import itertools
import math

print("== 直接机制：报告估值 -> 分配 + 支付 ==")
# 单物品，两个买家，二价规则（DSIC）
def direct_mechanism(reports):
    ranked = sorted(reports.items(), key=lambda x: -x[1])
    winner, second = ranked[0][0], ranked[1][1]
    alloc = {n: (1 if n == winner else 0) for n in reports}
    pay = {n: (second if n == winner else 0) for n in reports}
    return alloc, pay

types = {"A": 70, "B": 55}
alloc, pay = direct_mechanism(types)
print(f"  报告={types} -> 分配={alloc}, 支付={pay}")
print(f"  效用: A={types['A']*alloc['A']-pay['A']}, B={types['B']*alloc['B']-pay['B']}")

print("\n== DSIC 验证：A 的所有可能谎报都不更好 ==")
TRUE_A = 70
B = 55
best_utility = -1
for fake in range(0, 101, 5):
    a, p = direct_mechanism({"A": fake, "B": B})
    u = TRUE_A*a["A"] - p["A"]      # 用真实估值算效用
    best_utility = max(best_utility, u)
print(f"  A 真实估值={TRUE_A}, B 报 {B}")
for fake in (30, 50, 55, 60, 70, 80, 90):
    a, p = direct_mechanism({"A": fake, "B": B})
    u = TRUE_A*a["A"] - p["A"]
    print(f"    报 {fake:>3}: 得标={bool(a['A'])}, 支付={p['A']}, 效用={u}")
print(f"  最优效用={best_utility}，在诚实报 {TRUE_A} 时取得 -> DSIC 成立")

print("\n== 个人理性 IR ==")
for t in (10, 55, 70, 90):
    a, p = direct_mechanism({"A": t, "B": 55})
    u = t*a["A"] - p["A"]
    print(f"  真实估值 {t:>3}: 效用={u} >= 0 -> {'参与' if u>=0 else '退出'}")

print("\n== 显示原理示意 ==")
for line in (
    "  间接机制（如英式拍卖）：玩家策略是「什么时候退出」",
    "  均衡下退出价格恰好等于真实估值（等价于报告了类型）",
    "  直接机制只需让玩家报估值、按二价结算，就复制了同一结果",
    "  因此设计者只需在「诚实直接机制」集合里搜索，不必枚举所有博弈",
):
    print(" ", line)

print("\n== 迈尔森引理：单调分配 + 临界支付 ==")
# 单参数：分配概率 x_i(v) 必须随 v 非递减；支付 = v·x(v) - ∫₀^v x(z)dz
def myerson_payment(alloc_rule, v, steps=1000):
    """数值积分求 DSIC 支付（临界值法）。"""
    integ = sum(alloc_rule(v*k/steps)*(v/steps) for k in range(steps))
    return v*alloc_rule(v) - integ

def alloc_step(v):
    """估值 >= 50 才得物品（0/1 分配，单调）。"""
    return 1.0 if v >= 50 else 0.0
for v in (30, 49, 50, 60, 70):
    p = myerson_payment(alloc_step, v)
    print(f"  v={v:>3}: 分配={alloc_step(v):.0f}, 支付≈{p:.2f} "
          f"（临界值=50，得标者付 50）")
print("  分配单调是 DSIC 的充要条件；支付由公式唯一确定")

print("\n== 非单调分配会破坏诚实性 ==")
def alloc_weird(v):
    """故意做成非单调：估值中等反而更容易得标。"""
    return 1.0 if 40 <= v <= 60 else 0.0
print("  分配规则: 只在 40~60 之间给物品（非单调）")
for fake in (39, 45, 55, 61, 70):
    print(f"    报 {fake}: 分配={alloc_weird(fake):.0f}")
print("  真实估值 70 的人若报 55 反而能得标 -> 有说谎动机，不可能是 DSIC")

print("\n== 社会选择与不可能定理 ==")
print("  Arrow: 3+ 候选人、满足无限制域/帕累托/无关选项独立/无独裁的投票规则不存在")
print("  Gibbard-Satterthwaite: 任何非独裁、满射的投票规则都可被策略性操纵")
print("  -> 一般社会选择里「完全诚实」办不到；但「拟线性效用 + 可转移支付」下 VCG 可行")

print("\n== BIC vs DSIC ==")
for line in (
    "  DSIC（占优策略 IC）: 无论别人报什么，诚实都最优（VCG/二价）",
    "  BIC（贝叶斯 IC）  : 只知道别人的类型分布，诚实在期望上最优",
    "  DSIC 更强、不依赖先验，工程上更受欢迎",
    "  期望外部性机制（dAGVA）在预算平衡上比 VCG 更好，但只满足 BIC",
):
    print(" ", line)

print("\n== 机制设计目标清单 ==")
for line in [
    "  社会福利最大化 / 卖家收入最大化（最优拍卖 Myerson 1981）",
    "  预算平衡、计算可行性、公平性、抗串谋、隐私",
    "  这些目标常互相冲突，需要按场景取舍",
    "  与第773课 VCG、第775课匹配市场串联",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 验证「一价拍卖」的分配规则单调但支付公式不满足迈尔森 -> 不是 DSIC。
# 2. 实现 Myerson 最优拍卖（虚拟估值 + 保留价），对比二价拍卖的期望收入。
# 3. 用穷举验证 3 人 2 候选的投票规则可被操纵（G-S 小例）。
# 4. 思考：为什么显示原理能把「设计博弈」简化成「设计直接机制」？
