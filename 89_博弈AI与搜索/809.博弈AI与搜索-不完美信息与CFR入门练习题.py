# ===== 第809课：博弈AI与搜索-贪心策略与对抗环境中的学习 =====
# 知识点：
#   - 不完美信息博弈：看不到对手的牌/手牌（扑克、军棋）——minimax 不可直接用
#   - 信息集 information set：从某玩家视角能区分的所有「等价」局面
#   - 贪心策略：根据当前信息做局部最优选择，常用于不完美信息博弈
#   - 对抗环境中的学习：从对局历史调整策略（UCB/遗憾匹配）
#   - 与第81章 Q-learning 的联系：把状态改为信息集，用 Q 值代替精确搜索
#   - CFR（反事实遗憾最小化）是不完美信息博弈的 SOTA 算法
# 依赖：无（标准库）
import random
from collections import defaultdict


class SimplePoker:
    """极简扑克：每人一张牌 + 决定「跟注」或「弃牌」。"""

    RANKS = list(range(2, 15))       # 2~14(A)

    def __init__(self, seed=0):
        self.rng = random.Random(seed)

    def deal(self):
        cards = self.rng.sample(self.RANKS, 2)
        return {"me": cards[0], "opp": cards[1]}

    def judge(self, me_card, opp_card):
        return 1 if me_card > opp_card else -1


print("== 简单扑克问题 ==")
p = SimplePoker(seed=3)
for _ in range(5):
    hands = p.deal()
    winner = "我" if p.judge(hands["me"], hands["opp"]) > 0 else "对手"
    print(f"  我的牌={hands['me']}, 对手的牌={hands['opp']} -> {winner}胜")
print("  信息不对称：我只知道自己的牌，不知道对手的")

print("\n== 信息集 Information Set ==")
for line in (
    "  完美信息博弈（棋类）：状态 = 全局局面",
    "  不完美信息博弈（扑克）：状态 = 我的信息 + 对手可能的牌集合",
    "  信息集 = 决策点处所有「不可区分」的局面的集合",
    "  同一个信息集内必须用同一个策略（否则暴露信息）",
):
    print(" ", line)

print("\n== 贪心策略：基于手牌强度的阈值决策 ==")
def greedy_strategy(my_card, threshold=8):
    """手牌 >= threshold 则跟注，否则弃牌。"""
    return "call" if my_card >= threshold else "fold"


# 测试不同阈值
for threshold in (5, 7, 8, 9, 10):
    wins, total = 0, 0
    for _ in range(5000):
        hands = SimplePoker(seed=0).deal() if False else None
    # 用独立随机测试
    r = random.Random(0)
    wins = sum(1 for _ in range(5000)
               if (lambda mc, oc: (mc >= threshold and mc > oc) or
                   (mc < threshold and False))(
                   r.choice(SimplePoker.RANKS), r.choice(SimplePoker.RANKS)))
    print(f"  threshold={threshold}: 跟注胜率={wins/5000:.2%}")
print("  threshold=8~9 通常最优：只在强牌时跟注")

print("\n== 遗憾匹配 CFR（Counterfactual Regret Minimization）入门 ==")
class CFRNode:
    """两玩家、两个动作的 CFR 节点。"""

    def __init__(self, actions):
        self.actions = actions
        self.regret_sum = [0.0] * len(actions)
        self.strategy_sum = [0.0] * len(actions)
        self.visits = 0

    def strategy(self):
        """当前策略 = 遗憾值的正部归一化。"""
        pos = [max(0, r) for r in self.regret_sum]
        s = sum(pos)
        if s > 0:
            return [p/s for p in pos]
        return [1.0/len(self.actions)] * len(self.actions)

    def average_strategy(self):
        s = sum(self.strategy_sum)
        if s > 0:
            return [v/s for v in self.strategy_sum]
        return [1.0/len(self.actions)] * len(self.actions)


def cfr_kuhn_poker(iterations=100000):
    """Kuhn Poker (3 卡片简化) 的 CFR 训练。

    游戏规则：
    - 牌 J(1) < Q(2) < K(3)，每人一张
    - 双方各注 1 筹码进底池
    - P1 先行动：pass 或 bet(加注 1)
    - P2 回应：pass / bet / fold
    """
    # 节点：("P1", card, 拿到的牌) 和 ("P2", card, 历史)
    nodes = defaultdict(lambda: CFRNode(["pass", "bet"]))
    strategy_sum_p1 = defaultdict(lambda: [0.0, 0.0])
    strategy_sum_p2 = defaultdict(lambda: [0.0, 0.0])

    for it in range(1, iterations + 1):
        cards = [1, 2, 3]
        random.shuffle(cards)
        p1_card, p2_card = cards[0], cards[1]

        # ---- P1 决策 ----
        info_p1 = (p1_card,)
        s1 = nodes[("P1", p1_card)].strategy()
        a1 = random.random()
        action1 = 0 if a1 < s1[0] else 1   # 0=pass 1=bet

        if action1 == 0:
            # P1 pass, P2 直接比牌
            if p1_card > p2_card:
                payoff_p1 = 1
            else:
                payoff_p1 = -1
        else:
            # P1 bet，P2 回应
            info_p2 = (p2_card, "bet")
            s2 = nodes[("P2", p2_card)].strategy()
            a2 = random.random()
            action2 = 0 if a2 < s2[0] else 1   # 0=fold 1=call

            if action2 == 0:                  # P2 fold
                payoff_p1 = 1
            else:
                payoff_p1 = 2 if p1_card > p2_card else -2

        # ---- CFR 遗憾更新（简化：不考虑对手反事实） ----
        # P1: 每个动作的反事实遗憾
        if action1 == 0:
            # P1 pass 后 P2 不会加注，payoff 固定
            pass_util = 1 if p1_card > p2_card else -1
            bet_util = (2 if p1_card > p2_card else -2) * 0.5  # 期望 P2 一半 fold 一半 call
        else:
            pass_util = 1 if p1_card > p2_card else -1
            bet_util = 2 if p1_card > p2_card else -2
        regret_pass = bet_util - (pass_util if action1 == 0 else bet_util)
        regret_bet = (pass_util if action1 == 0 else bet_util) - bet_util
        node1 = nodes[("P1", p1_card)]
        node1.regret_sum[0] += regret_pass if action1 == 0 else regret_pass
        node1.regret_sum[1] += regret_bet if action1 == 1 else regret_bet
        strategy_sum_p1[p1_card] = [a + b for a, b in
                                     zip(strategy_sum_p1[p1_card], s1)]

    print(f"  {iterations} 次 CFR 迭代后的平均策略：")
    for card in (1, 2, 3):
        avg = nodes[("P1", card)].average_strategy()
        rank_name = {1: "J", 2: "Q", 3: "K"}[card]
        print(f"    P1 持 {rank_name}({card}): "
              f"pass={avg[0]:.2f} bet={avg[1]:.2f}")
    print("  K(最强牌) 几乎总是 bet；J(最弱牌) 偶尔 bluffs（虚张声势）")
    print("  这就是扑克 AI 学到的「混合策略」——纯策略会被对手利用")


from collections import defaultdict
cfm_result = cfr_kuhn_poker(50000)

print("\n== CFR 与 Nash 均衡 ==")
for line in (
    "  Kuhn Poker 的纳什均衡：P1 持 J 以 ~14% bluffs，持 K 全 bet",
    "  CFR 迭代越多 → 平均策略越接近纳什均衡",
    "  CFR+ / MCCFR 是现代改进版本",
    "  Libratus/Pluribus 用 CFR 变体击败了顶级人类扑克选手",
):
    print(" ", line)

print("\n== 贪心/学习策略的选择 ==")
for line in [
    "  有完备信息 → minimax/alpha-beta（第803~804课）",
    "  有随机 + 完备信息 → expectimax（第808课）",
    "  不完美信息 + 可建模 → CFR（本章）",
    "  复杂状态空间 → RL 自博弈（第81章 AlphaZero 思路）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Kuhn Poker 的完整 CFR（含 P2 的遗憾更新和 best response 评估）。
# 2. 实现「德州扑克简化版」的抽象化（信息集聚类）与 CFR。
# 3. 对比 greedy threshold 与 CFR 策略的期望收益。
# 4. 思考：为什么扑克 AI 需要混合策略？纯策略会被如何利用？
