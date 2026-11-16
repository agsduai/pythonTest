# ===== 第808课：博弈AI与搜索-Expectimax与随机博弈 =====
# 知识点：
#   - Expectimax：对手是「随机」而非「最优」时，用期望值代替 minimax 的 min
#   - max 节点（我方）不变，chance 节点（随机事件）取期望 E = ΣP(a)·val(a)
#   - 与 minimax 对比：minimax 假设对手最坏，expectimax 假设对手随机
#   - 骰子游戏、2048、纸牌游戏都有 chance 节点
#   - 期望值可能比 minimax 值高（对手不总是最优的）
#   - 用蒙特卡洛近似 expectimax（分支太多时采样子集）
# 依赖：无（标准库）
import math
import random


class DiceGame:
    """掷骰子冲关：每回合掷骰子，6 以下累加，6 则清零并结束回合。"""

    def __init__(self, score=0, rolls_left=5):
        self.score = score
        self.rolls_left = rolls_left

    def is_terminal(self):
        return self.rolls_left <= 0

    def moves(self):
        """两个选择：继续掷(roll) 或 停止收分(bank)。"""
        return ["roll", "bank"]

    def chance_children(self, action):
        """roll 的所有可能结果。"""
        if action == "roll":
            return [(self.make_copy(score=new_score), 1/6)
                    for new_score in range(1, 7)]
        return [(self, 1.0)]

    def make_copy(self, score=None, rolls_left=None):
        return DiceGame(
            score if score is not None else self.score,
            rolls_left if rolls_left is not None else self.rolls_left)

    def apply_roll(self, die):
        if die == 6:
            return DiceGame(0, 0), -self.score        # 清零，失去所有分
        return DiceGame(self.score + die, self.rolls_left - 1), die

    def apply_bank(self):
        return DiceGame(self.score, 0), self.score    # 锁定当前得分


def expectimax(state, depth, rng=None, is_chance=False):
    """返回期望效用。chance 节点取加权平均，max 节点取最大。"""
    if state.is_terminal():
        return state.score
    if depth <= 0:
        return state.score                        # 简化：当前分数作为评估

    if is_chance:
        total = 0.0
        for outcome, prob in state.chance_children("roll"):
            total += prob * expectimax(outcome, depth-1, rng, is_chance=False)
        return total

    # max 节点
    best = -math.inf
    for action in state.moves():
        if action == "bank":
            child = state.apply_bank()[0]
            val = expectimax(child, depth-1, rng, is_chance=False)
            best = max(best, state.score)         # bank 的收益 = 当前分
        elif action == "roll":
            # 期望 = ΣP(结果)·后续期望
            expected = 0.0
            for die in range(1, 7):
                child, reward = state.apply_roll(die)
                if die == 6:
                    expected += (1/6) * 0         # 掷出 6 清零
                else:
                    expected += (1/6) * expectimax(child, depth-1, rng, is_chance=True)
            best = max(best, expected)
    return best


def expectimax_move(state, depth=5):
    best_action, best_val = None, -math.inf
    for action in state.moves():
        if action == "bank":
            val = state.score                     # 停止 = 拿到当前分
        elif action == "roll":
            expected = 0.0
            for die in range(1, 7):
                child, _ = state.apply_roll(die)
                if die == 6:
                    expected += (1/6) * 0
                else:
                    expected += (1/6) * expectimax(child, depth-1)
            val = expected
        if val > best_val:
            best_val, best_action = val, action
    return best_action, best_val


def minimax_move(state, depth=5):
    """对照：minimax 假设骰子「故意给出最坏结果」。"""
    if state.is_terminal() or depth <= 0:
        return "bank", state.score
    roll_val = math.inf
    for die in range(1, 7):
        child, _ = state.apply_roll(die)
        if die == 6:
            roll_val = min(roll_val, 0)
        else:
            roll_val = min(roll_val, child.score)
    if roll_val >= state.score:
        return "roll", roll_val
    return "bank", state.score


print("== 掷骰子冲关：继续 vs 停止 ==")
for score in (5, 10, 15, 20, 25, 30):
    state = DiceGame(score, rolls_left=5)
    exp_move, exp_val = expectimax_move(state, depth=5)
    mm_move, mm_val = minimax_move(state, depth=5)
    print(f"  score={score:>3}: expectimax={exp_move}({exp_val:.1f}) "
          f"minimax={mm_move}({mm_val})")

print("  expectimax 会更激进（对手是骰子不是策略玩家）")
print("  分数高时两者都建议 bank；分数低时 expectimax 建议继续赌")

print("\n== 蒙特卡洛近似 expectimax ==")
def mc_expectimax(state, depth, n_samples=100, seed=0):
    """用随机采样近似期望值。"""
    rng = random.Random(seed)
    if state.is_terminal() or depth <= 0:
        return state.score
    if rng.random() < 0.5:                     # 我的回合：取 max
        vals = []
        for action in state.moves():
            child = state
            if action == "bank":
                vals.append(state.score)
            else:
                die = rng.randint(1, 6)
                child, _ = state.apply_roll(die)
                vals.append(mc_expectimax(child, depth-1, n_samples, seed+1))
        return max(vals) if vals else 0
    else:                                       # 随机回合：取平均
        vals = []
        for _ in range(n_samples):
            die = rng.randint(1, 6)
            child, _ = state.apply_roll(die)
            vals.append(mc_expectimax(child, depth-1, n_samples, seed+1))
        return statistics.fmean(vals) if vals else 0

import statistics
for score in (10, 20, 30):
    state = DiceGame(score, rolls_left=5)
    em = expectimax_move(state, depth=5)[1]
    mc = mc_expectimax(state, depth=5, n_samples=100)
    print(f"  score={score}: 解析期望={em:.2f} MC近似={mc:.2f}")
print("  采样越多 MC 越准；样本数不足会有方差")

print("\n== 策略对比：蒙特卡洛模拟 ==")
def simulate_strategy(strategy, rounds=5000, seed=0):
    rng = random.Random(seed)
    scores = []
    for _ in range(rounds):
        state = DiceGame(0, rolls_left=5)
        for _ in range(10):
            if state.is_terminal(): break
            a = strategy(state, rng)
            if a == "bank":
                scores.append(state.score); break
            die = rng.randint(1, 6)
            state, _ = state.apply_roll(die)
        else:
            scores.append(0)
    return statistics.fmean(scores) if scores else 0

def strat_expectimax(state, rng):
    mv, _ = expectimax_move(state, depth=3)
    return mv

def strat_minimax(state, rng):
    mv, _ = minimax_move(state, depth=3)
    return mv

def strat_always_roll(state, rng): return "roll"
def strat_bank_at_20(state, rng):
    return "bank" if state.score >= 20 else "roll"

for name, fn in (("expectimax", strat_expectimax),
                 ("minimax", strat_minimax),
                 ("always roll", strat_always_roll),
                 ("bank at 20", strat_bank_at_20)):
    avg = simulate_strategy(fn, rounds=3000, seed=7)
    print(f"  {name:<14}: 平均得分={avg:.2f}")
print("  expectimax 通常最优（它正确建模了骰子的随机性）")

print("\n== Expectimax vs Minimax ==")
print(f"  {'维度':<16}{'Minimax':<26}{'Expectimax'}")
for row in (("对手模型", "对手最优(最坏情况)", "随机/均匀"),
            ("Chance 节点", "取 min（最坏分支）", "取期望 E=ΣP·v"),
            ("适用游戏", "国际象棋、围棋", "骰子、2048、纸牌"),
            ("保守程度", "高（悲观）", "低（乐观/中性）")):
    print(f"  {row[0]:<16}{row[1]:<26}{row[2]}")

print("\n== 与 MCTS 的关系 ==")
for line in [
    "  Expectimax 的 chance 节点在 MCTS 中被「随机 rollout」代替",
    "  MCTS 不需要枚举所有 chance 分支，用采样近似期望",
    "  2048 AI（如 2048-AI 项目）用 expectimax + 评估函数",
    "  与第81章 RL 的联系：期望回报 = expectimax 的目标",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 2048 简化版的 expectimax（chance = 新方块出现位置）。
# 2. 比较 expectimax 在「对手最优」和「对手随机」下的实际胜率。
# 3. 实现 expectiminimax（允许 chance 节点嵌套在 max 节点内）。
# 4. 思考：为什么掷骰子游戏中 expectimax 通常优于 minimax？
