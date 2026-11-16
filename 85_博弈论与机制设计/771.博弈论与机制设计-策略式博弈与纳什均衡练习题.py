# ===== 第771课：博弈论与机制设计-策略式博弈与纳什均衡 =====
# 知识点：
#   - 策略式博弈：玩家集合 N、策略集 S_i、收益函数 u_i(s1,...,sn)
#   - 最优反应 best response：给定他人策略，使自己收益最大的策略
#   - 纳什均衡 NE：每个玩家都在对他人做最优反应，没人有单方面偏离动机
#   - 纯策略 NE 可能不存在（如猜硬币）；混合策略 NE 按纳什定理必存在
#   - 占优策略：无论别人怎么选都最优；严格占优可被迭代剔除
#   - 经典例子：囚徒困境、协调博弈、猜硬币、性别战
# 依赖：无（标准库）
from itertools import product

# 收益矩阵：payoff[a][b] = (u_A, u_B)
GAMES = {
    "囚徒困境": {
        "A": ["抵赖", "招供"], "B": ["抵赖", "招供"],
        "payoff": {(0,0):(-1,-1), (0,1):(-5,0), (1,0):(0,-5), (1,1):(-3,-3)},
    },
    "协调博弈": {
        "A": ["左", "右"], "B": ["左", "右"],
        "payoff": {(0,0):(2,2), (0,1):(0,0), (1,0):(0,0), (1,1):(1,1)},
    },
    "猜硬币": {
        "A": ["正", "反"], "B": ["正", "反"],
        "payoff": {(0,0):(1,-1), (0,1):(-1,1), (1,0):(-1,1), (1,1):(1,-1)},
    },
    "性别战": {
        "A": ["球赛", "歌剧"], "B": ["球赛", "歌剧"],
        "payoff": {(0,0):(2,1), (0,1):(0,0), (1,0):(0,0), (1,1):(1,2)},
    },
}


def best_responses(game, player, other_action):
    payoffs = game["payoff"]
    n = len(game["A"])
    rng = range(n)
    if player == 0:   # A 选 i，B 固定 other_action
        vals = [payoffs[(i, other_action)][0] for i in rng]
    else:
        vals = [payoffs[(other_action, j)][1] for j in rng]
    m = max(vals)
    return [i for i, v in enumerate(vals) if v == m]


def pure_nash(game):
    out = []
    for i, j in product(range(len(game["A"])), range(len(game["B"]))):
        br_a = best_responses(game, 0, j)
        br_b = best_responses(game, 1, i)
        if i in br_a and j in br_b:
            out.append((i, j, game["payoff"][(i,j)]))
    return out


def dominated_strategies(game, player):
    """返回被严格占优的策略索引。"""
    payoffs = game["payoff"]
    n = len(game["A"]) if player == 0 else len(game["B"])
    out = []
    for s in range(n):
        for t in range(n):
            if s == t: continue
            better = True
            for opp in range(n):
                key = (s, opp) if player == 0 else (opp, s)
                key2 = (t, opp) if player == 0 else (opp, t)
                if payoffs[key][player] >= payoffs[key2][player]:
                    better = False; break
            if better:
                out.append((s, t)); break
    return out


print("== 收益矩阵（囚徒困境）==")
g = GAMES["囚徒困境"]
print("        B:抵赖   B:招供")
for i, a in enumerate(g["A"]):
    print(f"  A:{a}  " + "  ".join(f"{g['payoff'][(i,j)]}" for j in range(2)))

print("\n== 各博弈的纯策略纳什均衡 ==")
for name, game in GAMES.items():
    ne = pure_nash(game)
    print(f"  {name}: {len(ne)} 个")
    for i, j, u in ne:
        print(f"    ({game['A'][i]}, {game['B'][j]}) -> 收益 {u}")
    if not ne:
        print("    无纯策略 NE（猜硬币需要混合策略）")

print("\n== 最优反应分析（囚徒困境）==")
for j, b in enumerate(g["B"]):
    print(f"  B 选 {b}: A 的最优反应 = {[g['A'][i] for i in best_responses(g,0,j)]}")
for i, a in enumerate(g["A"]):
    print(f"  A 选 {a}: B 的最优反应 = {[g['B'][j] for j in best_responses(g,1,i)]}")
print("  双方都招供是 NE，但 (抵赖,抵赖) 帕累托更优 -> 个体理性导致集体次优")

print("\n== 严格占优策略 ==")
for name, game in GAMES.items():
    d0, d1 = dominated_strategies(game,0), dominated_strategies(game,1)
    print(f"  {name}: A 被占优={d0}, B 被占优={d1}")

print("\n== 帕累托最优 vs 纳什均衡 ==")
all_outcomes = list(g["payoff"].items())
def pareto_dominates(u, v):
    return all(a>=b for a,b in zip(u,v)) and any(a>b for a,b in zip(u,v))
pareto = [k for k,u in all_outcomes
          if not any(pareto_dominates(v,u) for k2,v in all_outcomes if k2!=k)]
print("  囚徒困境的帕累托最优结果:", [( (g['A'][i],g['B'][j]), g['payoff'][(i,j)] )
                                   for i,j in pareto])
print("  NE 结果:", [((g['A'][i],g['B'][j]), u) for i,j,u in pure_nash(g)])

print("\n== 混合策略 NE：猜硬币 ==")
# A 以 p 出正，B 以 q 出正；无差异条件求 p,q
# A 出正收益 = q*1 + (1-q)*(-1) = 2q-1；出反 = q*(-1)+(1-q)*1 = 1-2q
# 令相等 -> q=0.5；同理 p=0.5
p = q = 0.5
print(f"  A 以 p={p} 出正，B 以 q={q} 出正")
exp_a_pos = q*1 + (1-q)*(-1)
exp_a_neg = q*(-1) + (1-q)*1
print(f"  A 出正期望={exp_a_pos}, 出反期望={exp_a_neg} -> 无差异（才会愿意混合）")
print(f"  均衡期望收益: A=0, B=0（零和博弈）")

print("\n== 纳什定理（存在性）==")
for line in (
    "  有限博弈（有限玩家、有限策略）必存在混合策略纳什均衡",
    "  证明用不动点定理（Brouwer / Kakutani），非构造性",
    "  求 NE 是 PPAD-完全，大规模博弈没有已知多项式算法",
    "  纯策略 NE 可能多个（协调博弈有 2 个）或不存在（猜硬币）",
):
    print(" ", line)

print("\n== 应用 ==")
for line in [
    "  经济学：寡头定价（古诺/伯特兰）、拍卖设计",
    "  网络：路由博弈、拥塞控制、自私路由的代价（第772课）",
    "  AI：多智能体 RL、GAN 的均衡视角（第81章）",
    "  机制设计：反过来设计规则让均衡达成目标（第773课起）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「迭代剔除严格占优策略」，观察囚徒困境是否收敛到唯一解。
# 2. 用支撑枚举法求 3×3 博弈的所有混合策略 NE。
# 3. 计算「无政府代价 PoA」：囚徒困境 NE 收益 / 社会最优收益。
# 4. 思考：为什么 (抵赖,抵赖) 帕累托更优却不是均衡？
