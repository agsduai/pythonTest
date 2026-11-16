# ===== 第803课：博弈AI与搜索-极小极大与井字棋 =====
# 知识点：
#   - 零和博弈：我赢 = 你输；总收益恒为 0，可只用「我方视角」评分
#   - 极小极大 minimax：假设双方都最优，递归取 max(我)/min(对手)
#   - 博弈树节点 = 状态；分支 = 合法走法；叶 = 终局(+1/-1/0)或深度限制
#   - 与第85章纳什均衡的关系：minimax 给出的是「完美信息下的最优策略」
#   - 井字棋是零和博弈教学标准：解空间 9! = 362850，可穷举验证最优
#   - 剪枝预告：minimax 存在大量重复计算，alpha-beta（第804课）能剪掉一半以上
# 依赖：无（标准库）
import math

WINS = [(0,1,2),(3,4,5),(6,7,8),  # 行
        (0,3,6),(1,4,7),(2,5,8),  # 列
        (0,4,8),(2,4,6)]          # 对角

EMPTY = "."


class TicTacToe:
    def __init__(self):
        self.board = [EMPTY]*9

    def moves(self):
        return [i for i, v in enumerate(self.board) if v == EMPTY]

    def make(self, pos, player):
        self.board[pos] = player

    def undo(self, pos):
        self.board[pos] = EMPTY

    def winner(self):
        for a, b, c in WINS:
            if self.board[a] != EMPTY and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        return None

    def is_full(self):
        return EMPTY not in self.board

    def render(self):
        return "\n".join(" ".join(self.board[r*3:(r+1)*3]) for r in range(3))


_cache = {}    # (tuple(board), player) -> (score, best_move)


def minimax(board, player, depth=0):
    """返回 (最优评分, 最优走法)。加 memoize 缓存避免重复搜索。"""
    key = (tuple(board.board), player)
    if key in _cache:
        return _cache[key]
    w = board.winner()
    if w == "X": return (1, None)
    if w == "O": return (-1, None)
    if board.is_full(): return (0, None)

    scores = []
    for mv in board.moves():
        board.make(mv, player)
        val, _ = minimax(board, "O" if player == "X" else "X", depth+1)
        board.undo(mv)
        scores.append((val, mv))

    if player == "X":
        result = max(scores)
    else:
        result = min(scores)
    _cache[key] = result
    return result


def minimax_count(board, player):
    """统计搜索节点数（带缓存，与 minimax 共享 _cache 减少重复）。"""
    w = board.winner()
    if w or board.is_full(): return 1
    nodes = 1
    for mv in board.moves():
        board.make(mv, player)
        nodes += minimax_count(board, "O" if player == "X" else "X")
        board.undo(mv)
    return nodes


print("== 井字棋 ==")
g = TicTacToe()
print(g.render())

print("\n== 空盘的最优评分（minimax + memoize）==")
score, move = minimax(g, "X")
nodes = minimax_count(TicTacToe(), "X")
print(f"  最优评分 = {score}（先手 X 必不败，即至少平局）")
print(f"  首选走法 = 位置 {move}")
print(f"  搜索节点（含缓存命中）= {nodes:,}  缓存条目 = {len(_cache):,}")
print(f"  memoize 减少了重复搜索：实际耗时 ≈ {len(_cache)/(nodes+1):.0%} of 穷举")

print("\n== 各开局位置的最优评分 ==")
g2 = TicTacToe()
for mv in g2.moves():
    g2.make(mv, "X")
    s, _ = minimax(g2, "O")
    g2.undo(mv)
    r, c = mv % 3, mv // 3
    print(f"  走位置 {mv} (行{r}列{c}): 评分={s:>2}  "
          f"{'最优' if s == 0 else '次优' if s == -1 else '最优'}")
print("  评分 0 = 至少平局；任何开局 X 都能保证不败")

print("\n== 最优 vs 随机 AI 对局 ==")
def ai_minimax(board, player, rng=None):
    _, mv = minimax(board, player)
    return mv

def ai_random(board, player, rng):
    return rng.choice(board.moves())

def play_game(black_strategy, white_strategy, seed=0):
    b = TicTacToe()
    rng = random.Random(seed)
    strategies = {"X": black_strategy, "O": white_strategy}
    player = "X"
    while True:
        w = b.winner()
        if w or b.is_full():
            return w
        mv = strategies[player](b, player) if player == "X" else strategies[player](b, player, rng)
        b.make(mv, player)
        player = "O" if player == "X" else "X"

import random
wins = {"X": 0, "O": 0, "draw": 0}
rng = random.Random(0)
for s in range(100):
    w = play_game(ai_minimax, lambda b, p, r=rng: rng.choice(b.moves()), seed=s)
    if w: wins[w] += 1
    else: wins["draw"] += 1
print(f"  minimax vs random (100 局): X 赢={wins['X']} O 赢={wins['O']} 平={wins['draw']}")
print("  minimax 永不输")

print("\n== minimax vs minimax ==")
w = play_game(ai_minimax, ai_minimax)
print(f"  双方都最优: 结果={w or '平局'}（理论上井字棋先手最优也只能平局）")

print("\n== 搜索节点数对比（后续课预告） ==")
for depth_label, note in (
    ("minimax 穷举", f"{nodes:,} 个节点"),
    ("alpha-beta 剪枝", "同结果但节点数减半以上（第804课）"),
    ("启发式 + 深度限制", "节点数指数→常数，但可能错过最优（第805课）"),
):
    print(f"  {depth_label:<20} {note}")

print("\n== minimax 的递归结构 ==")
for line in (
    "  maximize(player) = max(minimize(child) for child in moves)",
    "  minimize(player) = min(maximize(child) for child in moves)",
    "  终止: 终局节点返回 ±1/0；或达到深度限制返回评估函数值",
    "  零和简化: 对手评分 = -我方评分，只需一个方向的比较",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  make/undo 配对比复制棋盘快（不分配新对象）",
    "  转置表 transposition table 缓存已搜索过的局面（第82章 Zobrist 哈希）",
    "  对称性可进一步减少搜索：井字棋有 8 种对称（旋转+翻转）",
    "  大型博弈（围棋/国际象棋）必须加启发式与深度限制",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「对称剪枝」：利用棋盘旋转/翻转减少 8 倍搜索。
# 2. 实现 negamax（零和简化版）：只返回一个方向的评分。
# 3. 统计「先手选角 vs 选边」的搜索树大小差异。
# 4. 思考：为什么井字棋完美对弈永远是平局？证明或解释。
