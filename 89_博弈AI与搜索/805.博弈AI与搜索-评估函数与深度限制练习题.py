# ===== 第805课：博弈AI与搜索-评估函数与深度限制 =====
# 知识点：
#   - 大博弈无法搜到终局 → 限制深度，用「评估函数」估分
#   - 评估函数 eval(state) → 数值：正=我方优，负=对手优
#   - 评估函数设计 = 特征选择 + 权重调整，是博弈 AI 的核心竞争力
#   - 深度限制 quiescence search：在「静止」位置才截断，避免地平线效应
#   - 与第81章 RL 的关系：RL 用自博弈学评估函数（AlphaGo 的价值网络）
#   - 本课实现井字棋评估函数 + 深度限制 alpha-beta，对比不同评估的质量
# 依赖：无（标准库）
import math

WINS = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
EMPTY = "."


class Board:
    def __init__(self):
        self.board = [EMPTY]*9
    def moves(self): return [i for i, v in enumerate(self.board) if v == EMPTY]
    def make(self, pos, p): self.board[pos] = p
    def undo(self, pos): self.board[pos] = EMPTY
    def winner(self):
        for a,b,c in WINS:
            if self.board[a] != EMPTY and self.board[a]==self.board[b]==self.board[c]:
                return self.board[a]
        return None
    def is_full(self): return EMPTY not in self.board
    def render(self):
        return "\n".join(" ".join(self.board[r*3:(r+1)*3]) for r in range(3))


def eval_zero(board, me):
    """零评估：不区分好坏（纯深度搜索退化为广度优先）。"""
    return 0


def eval_count(board, me):
    """简单计数：我方棋子数 - 对方棋子数（太粗糙）。"""
    opp = "O" if me == "X" else "X"
    return board.board.count(me) - board.board.count(opp)


def eval_lines(board, me):
    """基于行/列/对角的「潜在赢线」评估（比计数更准）。"""
    opp = "O" if me == "X" else "X"
    score = 0
    for a, b, c in WINS:
        line = [board.board[a], board.board[b], board.board[c]]
        mine = line.count(me)
        theirs = line.count(opp)
        empties = line.count(EMPTY)
        if theirs == 0 and mine > 0:
            score += 10 ** mine               # 我方占 1/2/3 格的线
        elif mine == 0 and theirs > 0:
            score -= 10 ** theirs              # 对方占的线（威胁）
    return score


def eval_weighted(board, me):
    """带位置权重的评估：中心 > 角 > 边。"""
    weights = [3,2,3, 2,4,2, 3,2,3]           # 中心最值钱
    opp = "O" if me == "X" else "X"
    pos_score = sum(weights[i] * (1 if board.board[i] == me else -1 if board.board[i] == opp else 0)
                    for i in range(9))
    return eval_lines(board, me) * 10 + pos_score


EVALS = [("零", eval_zero), ("计数", eval_count),
         ("赢线", eval_lines), ("加权", eval_weighted)]


def alphabeta_limited(board, me, depth, alpha, beta, eval_fn):
    """带深度限制的 alpha-beta；终局或有评估值时返回。"""
    w = board.winner()
    if w == me: return 1000 + depth            # 越早赢越好
    if w and w != me: return -1000 - depth
    if board.is_full(): return 0
    if depth <= 0:
        return eval_fn(board, me)
    opp = "O" if me == "X" else "X"
    moves = board.moves()
    # 轮到谁：X 先走，所以棋子数相等时轮到我
    my_count = board.board.count(me)
    opp_count = board.board.count(opp)
    is_my_turn = my_count == opp_count         # X 先走
    if is_my_turn:
        val = -math.inf
        for mv in moves:
            board.make(mv, me)
            v = alphabeta_limited(board, me, depth-1, alpha, beta, eval_fn)
            board.undo(mv)
            val = max(val, v); alpha = max(alpha, val)
            if alpha >= beta: break
        return val
    else:
        val = math.inf
        for mv in moves:
            board.make(mv, opp)
            v = alphabeta_limited(board, me, depth-1, alpha, beta, eval_fn)
            board.undo(mv)
            val = min(val, v); beta = min(beta, val)
            if beta <= alpha: break
        return val


def ai_with_eval(board, me, depth, eval_fn):
    """顶层选择最优走法。"""
    opp = "O" if me == "X" else "X"
    best_val, best_mv = -math.inf, None
    for mv in board.moves():
        board.make(mv, me)
        v = alphabeta_limited(board, me, depth-1, -math.inf, math.inf, eval_fn)
        board.undo(mv)
        if v > best_val:
            best_val, best_mv = v, mv
    return best_mv


print("== 不同评估函数的效果（深度 4）==")
for name, fn in EVALS:
    b = Board()
    b.make(4, "X")           # X 先占中心
    b.make(0, "O")
    score = alphabeta_limited(b, "X", depth=4, alpha=-math.inf, beta=math.inf, eval_fn=fn)
    mv = ai_with_eval(b, "X", depth=4, eval_fn=fn)
    print(f"  {name:<6}: 评估值={score:>5} 最优走法={mv}")

print("\n== 深度限制的权衡 ==")
b2 = Board()
b2.board = ["X","O",EMPTY, EMPTY,"X","O", EMPTY,EMPTY,EMPTY]  # X 需要走 (2,8) 或 (6,7)

for depth in (1, 2, 3, 4, 6):
    mv = ai_with_eval(b2, "X", depth=depth, eval_fn=eval_lines)
    print(f"  depth={depth}: 建议走 {mv}")

print("\n== 评估函数质量对比（不同深度 vs 完美搜索） ==")
def perfect_move(board, me):
    """穷举找完美走法。"""
    opp = "O" if me == "X" else "X"
    best, best_mv = -math.inf, None
    for mv in board.moves():
        board.make(mv, me)
        val = alphabeta_limited(board, me, depth=20, alpha=-math.inf,
                                beta=math.inf, eval_fn=eval_zero)
        board.undo(mv)
        if val > best:
            best, best_mv = val, mv
    return best_mv

for name, fn in EVALS:
    for depth in (2, 4, 6):
        b3 = Board()
        b3.make(4, "X"); b3.make(0, "O")
        mv_eval = ai_with_eval(b3, "X", depth=depth, eval_fn=fn)
        # 用完美搜索评估这个走法的结果
        b3.make(mv_eval, "X")
        result = alphabeta_limited(b3, "X", depth=20, alpha=-math.inf,
                                   beta=math.inf, eval_fn=eval_zero)
        b3.undo(mv_eval)
        perfect = perfect_move(b3, "X")
        print(f"  {name:<6} depth={depth}: 建议走 {mv_eval}, "
              f"后续评分={result:+.0f}, 完美走法={perfect}, "
              f"{'最优' if mv_eval == perfect else '次优'}")

print("\n== 评估函数设计要点 ==")
for line in (
    "  特征要「与胜负相关」：潜在赢线比棋子计数更准",
    "  量级要分层：赢线(10^n) > 位置(单位) > 噪声",
    "  评估要快速：每秒千万次调用，单次 O(1)~O(n) 最佳",
    "  与第81章 RL 的关系：RL 学到的价值函数就是一种自动调参的评估函数",
):
    print(" ", line)

print("\n== 地平线效应（Horizon Effect） ==")
for line in (
    "  深度限制把「即将发生的坏结果」推到搜索边界外",
    "  例：搜索深度不够时，看不到对手两步后的将杀",
    "  缓解：quiescence search 在「不稳」位置继续搜，直到局面安静",
    "  或：增加深度/用更准确的评估函数覆盖更远",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  评估函数特征与权重用位棋盘 + 查表可以极快",
    "  特征数量增加时用线性/神经网络组合（Stockfish NNUE）",
    "  AlphaGo 用策略网络生成走法 + 价值网络当评估函数（第81章 RL）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现井字棋的「必胜威胁检测」：找出一步赢的位置。
# 2. 实现 quiescence search：当有「立即赢/输」的可能时继续搜索。
# 3. 用不同的评估函数做自对弈锦标赛，统计胜率。
# 4. 思考：为什么「棋子数」作为评估函数效果很差？
