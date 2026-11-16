# ===== 第806课：博弈AI与搜索-蒙特卡洛树搜索MCTS =====
# 知识点：
#   - MCTS 四阶段：选择(Select) -> 扩展(Expand) -> 模拟(Simulate) -> 回传(Backup)
#   - UCB1 选择公式：child_score = win/(visit) + C·√(ln(parent)/visit)
#   - 与 alpha-beta 的区别：不需要评估函数、用随机模拟代替、统计而非穷举
#   - AlphaGo 的核心 = MCTS + 策略网络(引导模拟) + 价值网络(替代随机模拟)
#   - Pure MCTS 在小博弈上也能达到不错水平；大博弈需要好的模拟策略
#   - 参数：探索常数 C、模拟次数/时间限制
# 依赖：无（标准库）
import math
import random


class TicTacToe:
    WINS = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]

    def __init__(self, board=None, player="X"):
        self.board = board or ["."]*9
        self.player = player

    def moves(self):
        return [i for i, v in enumerate(self.board) if v == "."]

    def make(self, pos):
        b = self.board[:]
        b[pos] = self.player
        return TicTacToe(b, "O" if self.player == "X" else "X")

    def winner(self):
        for a,b,c in self.WINS:
            if self.board[a] != "." and self.board[a]==self.board[b]==self.board[c]:
                return self.board[a]
        return None

    def is_full(self): return "." not in self.board

    def render(self):
        return "\n".join(" ".join(self.board[r*3:(r+1)*3]) for r in range(3))


def random_rollout(state, rng):
    """随机模拟到终局，返回 +1(X 赢)/-1(O 赢)/0。"""
    cur = state
    while True:
        w = cur.winner()
        if w == "X": return 1
        if w == "O": return -1
        if cur.is_full(): return 0
        cur = cur.make(rng.choice(cur.moves()))


class MCTSNode:
    __slots__ = ("state", "parent", "move", "children", "wins", "visits", "untried")

    def __init__(self, state, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move            # 从父到本节点走的那个位置
        self.children = []
        self.wins = 0.0             # 从本节点方视角的累计胜次
        self.visits = 0
        self.untried = state.moves()[:]

    def ucb1(self, C=1.4):
        if self.visits == 0:
            return math.inf
        return self.wins / self.visits + C * math.sqrt(
            math.log(self.parent.visits + 1) / self.visits)

    def best_child(self, C=1.4):
        return max(self.children, key=lambda c: c.ucb1(C))

    def best_move(self):
        """最终选择：访问次数最多（而非胜率最高）——更稳定。"""
        return max(self.children, key=lambda c: c.visits).move if self.children else None


def mcts(state, iterations=2000, C=1.4, seed=0):
    rng = random.Random(seed)
    root = MCTSNode(state)
    me = state.player

    for _ in range(iterations):
        node = root
        cur = state
        # 1) 选择：沿 UCB1 最优子节点下行直到有未尝试走法或终局
        while node.untried == [] and node.children:
            node = node.best_child(C)
            cur = cur.make(node.move)
        # 2) 扩展：加一个未尝试的子节点
        if node.untried:
            mv = rng.choice(node.untried)
            node.untried.remove(mv)
            cur = cur.make(mv)
            child = MCTSNode(cur, parent=node, move=mv)
            node.children.append(child)
            node = child
        # 3) 模拟：随机走到底
        w = random_rollout(cur, rng)
        # 4) 回传：从当前节点回溯到根，按「谁在走」视角更新胜负
        while node is not None:
            node.visits += 1
            if node.state.player != me:
                # 这个节点是对手回合 -> 我赢记为正
                node.wins += (1 if w == 1 else (-1 if w == -1 else 0))
            else:
                node.wins += (1 if w == -1 else (-1 if w == 1 else 0))
            node = node.parent

    return root.best_move(), root


print("== MCTS 参数对结果的影响 ==")
for iters in (100, 500, 2000, 8000):
    for C in (0.5, 1.4, 3.0):
        s = TicTacToe()
        mv, root = mcts(s, iterations=iters, C=C, seed=3)
        print(f"  iters={iters:>5} C={C:>3}: 建议走 {mv}")

print("\n== 探索常数 C 的影响 ==")
# 看 C 大时是否每个位置都被探索到
for C in (0.3, 1.4, 3.0):
    s = TicTacToe()
    mv, root = mcts(s, iterations=1000, C=C, seed=1)
    visited = len(root.children)
    print(f"  C={C}: 首层探索 {visited}/9 个位置, 根的子节点访问分布="
          f"{[c.visits for c in sorted(root.children, key=lambda c:c.move)]}")
print("  C 大 -> 均匀探索；C 小 -> 集中在好走法（可能错过最优）")

print("\n== MCTS vs minimax 对局 ==")
def mcts_move(state, iters=2000):
    return mcts(state, iterations=iters, seed=hash(str(state)) % 10000)[0]

def minimax_move(board_state, me="X"):
    # 用第803课的 minimax
    WINS2 = TicTacToe.WINS
    def mm(b, p):
        for a,bb,c in WINS2:
            if b[a]!="." and b[a]==b[bb]==b[c]: return (1 if b[a]=="X" else -1)
        if "." not in b: return 0
        vals = []
        for m in range(9):
            if b[m] == ".":
                b[m] = p
                vals.append(mm(b, "O" if p=="X" else "X"))
                b[m] = "."
        return max(vals) if p == "X" else min(vals)
    best, best_m = -math.inf, None
    for m in range(9):
        if board_state.board[m] == ".":
            b2 = board_state.board[:]
            b2[m] = me
            v = mm(b2, "O" if me=="X" else "X")
            if v > best: best, best_m = v, m
    return best_m

def play_vs(mcts_iters, opponent="minimax", seed=0):
    rng = random.Random(seed)
    s = TicTacToe()
    while True:
        w = s.winner()
        if w or s.is_full(): return w
        if s.player == "X":
            mv = mcts_move(s, mcts_iters)
        else:
            mv = minimax_move(s, "O")
        s = s.make(mv)

mcts_wins = minimax_wins = draws = 0
for s in range(30):
    w = play_vs(2000, "minimax", seed=s)
    if w == "X": mcts_wins += 1
    elif w == "O": minimax_wins += 1
    else: draws += 1
print(f"  MCTS(2000 iter) vs minimax (30 局): MCTS 赢={mcts_wins} "
      f"minimax 赢={minimax_wins} 平={draws}")
print("  minimax 是完美的，MCTS 用随机模拟近似 -> 通常平局或略逊")

print("\n== MCTS vs 随机 ==")
rand_wins = mcts_rand_wins = draws2 = 0
for s in range(50):
    s2 = TicTacToe()
    while True:
        w = s2.winner()
        if w or s2.is_full():
            if w == "X": mcts_rand_wins += 1
            elif w == "O": rand_wins += 1
            else: draws2 += 1
            break
        if s2.player == "X":
            s2 = s2.make(mcts_move(s2, 1000))
        else:
            s2 = s2.make(random.Random(s+1000).choice(s2.moves()))
print(f"  MCTS(1000 iter) vs random (50 局): MCTS 赢={mcts_rand_wins} "
      f"random 赢={rand_wins} 平={draws2}")

print("\n== MCTS 四阶段 ==")
for line in (
    "  Select: 沿 UCB1 最优子节点下行（exploitation + exploration）",
    "  Expand: 在有未尝试走法的节点加一个子节点",
    "  Simulate: 从新节点随机走到底，得到胜负",
    "  Backup: 把结果沿路径回传给所有祖先",
    "  与第81章 RL 的 MCTS 不同：这里用纯随机 rollout，AlphaGo 用策略网络",
):
    print(" ", line)

print("\n== MCTS vs Alpha-Beta ==")
print(f"  {'维度':<16}{'Alpha-Beta':<24}{'MCTS'}")
for row in (("评估", "需要评估函数", "不需要（随机模拟）"),
            ("性能", "确定性，可证最优", "统计近似，收敛慢"),
            ("适用", "分支少、评估准", "分支多、评估难"),
            ("并行", "难（顺序依赖）", "天然可并行"),
            ("AlphaGo", "不用", "核心引擎 + 神经网络引导")):
    print(f"  {row[0]:<16}{row[1]:<24}{row[2]}")

# ===== 练习题 =====
# 1. 实现带「渐进加宽 progressive widening」的 MCTS，限制子节点数。
# 2. 用「策略网络替代随机 rollout」（简单：用历史胜率引导模拟走法）。
# 3. 把 MCTS 扩展到 Connect Four（7×7 更大分支），调整参数。
# 4. 思考：为什么 MCTS 的最终选择用访问次数而不是胜率？
