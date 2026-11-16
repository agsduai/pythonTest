# ===== 第772课：博弈论与机制设计-重复博弈与合作演化 =====
# 知识点：
#   - 重复博弈：同一阶段博弈反复进行，玩家能根据历史调整策略
#   - 贴现因子 δ：未来收益按 δ^t 折现；δ 越大越看重长期，合作越可能维持
#   - 冷酷策略 grim trigger：一旦对方背叛就永远背叛；触发策略可支撑合作均衡
#   - 无名氏定理 folk theorem：δ 足够大时，任何个体理性且可行的收益都能成为均衡
#   - 以牙还牙 TFT：首轮合作，之后复制对方上一轮动作；Axelrod 锦标赛冠军
#   - 演化博弈：复制子动态 replicator dynamics，策略占比按收益差演化
# 依赖：无（标准库）
import random

# 囚徒困境阶段收益：(合作,合作)=(3,3), (背叛,合作)=(5,0), (背叛,背叛)=(1,1)
PD = {(0,0):(3,3), (0,1):(0,5), (1,0):(5,0), (1,1):(1,1)}   # 0=合作 1=背叛

print("== 一次性囚徒困境：背叛占优 ==")
for a in (0,1):
    print(f"  我选{'合作' if a==0 else '背叛'}: 对方合作得{PD[(a,0)][0]}, "
          f"对方背叛得{PD[(a,1)][0]}")
print("  单次博弈 (背叛,背叛) 是唯一 NE")

print("\n== 重复博弈：冷酷策略能维持合作吗 ==")
# 合作 forever 收益 = 3/(1-δ)；一次背叛得 5，之后永远 1：5 + δ·1/(1-δ)
def grim_incentive(delta, T=100):
    coop = sum(delta**t * 3 for t in range(T))
    deviate = 5 + sum(delta**t * 1 for t in range(1, T))
    return coop, deviate
for delta in (0.1, 0.3, 0.5, 0.7, 0.9, 0.99):
    c, d = grim_incentive(delta)
    print(f"  δ={delta:<5}: 一直合作={c:.2f} 先背叛再被惩罚={d:.2f} "
          f"-> {'合作可维持' if c >= d else '背叛更划算'}")
print("  解析阈值：3/(1-δ) >= 5 + δ/(1-δ) -> δ >= 2/3 ≈ 0.667")


# ---- 策略集合 ----
def always_cooperate(hist, t): return 0
def always_defect(hist, t): return 1
def tit_for_tat(hist, t):
    if t == 0: return 0
    return hist[t-1][1]                  # 复制对方上一轮
def grim(hist, t):
    return 1 if any(h[1] == 1 for h in hist) else 0
def pavlov(hist, t):
    """赢则保持、输则改变（win-stay lose-shift）。"""
    if t == 0: return 0
    my_last, op_last = hist[t-1]
    payoff = PD[(my_last, op_last)][0]
    return my_last if payoff >= 3 else 1-my_last

STRATS = {"ALLC": always_cooperate, "ALLD": always_defect,
          "TFT": tit_for_tat, "GRIM": grim, "PAVLOV": pavlov}


def match(f1, f2, T=100, delta=0.95):
    h1, h2 = [], []             # 各自视角的 (我, 对手)
    s1 = s2 = 0.0
    for t in range(T):
        a1, a2 = f1(h1, t), f2(h2, t)
        u1, u2 = PD[(a1,a2)]
        s1 += delta**t * u1; s2 += delta**t * u2
        h1.append((a1,a2)); h2.append((a2,a1))
    return s1, s2

print("\n== 两两对局平均收益矩阵（δ=0.95, T=100）==")
names = list(STRATS)
print("        " + "".join(f"{n:>8}" for n in names))
for n1 in names:
    row = []
    for n2 in names:
        s,_ = match(STRATS[n1], STRATS[n2])
        row.append(f"{s:>8.1f}")
    print(f"  {n1:<6}" + "".join(row))

print("\n== 锦标赛总分（Axelrod 风格）==")
totals = {n: 0.0 for n in names}
for n1 in names:
    for n2 in names:
        s,_ = match(STRATS[n1], STRATS[n2])
        totals[n1] += s
for n, v in sorted(totals.items(), key=lambda x:-x[1]):
    print(f"  {n:<8}: 总分={v:.1f}")
print("  TFT 善良(首轮合作)、可激怒(会报复)、宽容(对方合作即原谅)、简单 -> 综合表现好")

print("\n== 带噪声环境：TFT 会陷入互相报复 ==")
def match_noisy(f1, f2, T=30, noise=0.05, seed=1):
    rng = random.Random(seed)
    h1,h2,total = [],[],0.0
    for t in range(T):
        a1,a2 = f1(h1,t), f2(h2,t)
        if rng.random() < noise: a1 ^= 1        # 执行误差
        if rng.random() < noise: a2 ^= 1
        u1,_ = PD[(a1,a2)]
        total += u1
        h1.append((a1,a2)); h2.append((a2,a1))
    return total
print(f"  TFT vs TFT 无噪声={match(STRATS['TFT'],STRATS['TFT'],T=30)[0]:.1f}")
print(f"  TFT vs TFT 有 5% 噪声={match_noisy(STRATS['TFT'],STRATS['TFT']):.1f}")
print("  一次误判引发连锁报复 -> 实际系统常用「宽容 TFT」或「 generous TFT」")

print("\n== 演化博弈：复制子动态 ==")
def replicator(p_cooperators, rounds=60):
    """p = 合作者占比；收益决定下一代占比。"""
    p = p_cooperators
    history = [p]
    for _ in range(rounds):
        # 随机配对下的期望收益
        pi_c = p*3 + (1-p)*0        # 遇合作 3，遇背叛 0
        pi_d = p*5 + (1-p)*1        # 遇合作 5，遇背叛 1
        avg = p*pi_c + (1-p)*pi_d
        p = p * pi_c / avg if avg else p
        p = max(0.0, min(1.0, p))
        history.append(p)
    return history

for p0 in (0.9, 0.5, 0.1):
    h = replicator(p0)
    print(f"  初始合作者 {p0:.0%} -> 60 代后 {h[-1]:.2%} "
          f"（轨迹 {[round(x,2) for x in h[:5]]} -> {round(h[-1],2)}）")
print("  标准 PD 里合作被背叛侵蚀；若有重复互动/亲缘/惩罚机制，合作可稳定")

print("\n== 无名氏定理直觉 ==")
for line in (
    "  只要 δ 足够接近 1，未来惩罚的威胁就能约束当下背叛",
    "  可支撑的均衡收益集合远大于一次性博弈的 NE",
    "  但均衡太多也带来「协调问题」：大家会收敛到哪个？",
    "  有限次重复且终点已知时，逆推归纳又回到每轮背叛",
):
    print(" ", line)

print("\n== 应用 ==")
for line in [
    "  国际关系/军备控制、商业长期合作、平台信誉机制",
    "  分布式系统：节点是否诚实转发（重复互动支撑合作）",
    "  生物：互惠利他、演化稳定策略 ESS",
    "  与第771课 NE、第81章多智能体 RL 串联",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「宽容 TFT」（以概率原谅），验证噪声环境下的鲁棒性。
# 2. 用 Axelrod 锦标赛加入更多策略（如 tester、random）重排总分。
# 3. 给复制子动态加入「空间结构」（网格邻居互动），观察合作能否存活。
# 4. 思考：为什么有限次且终点已知的重复博弈仍会每轮背叛？
