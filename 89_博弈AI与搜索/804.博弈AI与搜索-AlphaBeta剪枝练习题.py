# ===== 第804课：博弈AI与搜索-Alpha-Beta剪枝 =====
# 知识点：
#   - Alpha-Beta：在 minimax 基础上维护 [α, β] 窗口，不可能影响结果的子树直接剪掉
#   - α = 当前 max 方已知最优下界；β = 当前 min 方已知最优上界
#   - 剪枝条件：α >= β 时当前节点的后续兄弟不会影响结果，立即返回
#   - 效果：同样的最优结果，搜索节点数从 O(b^d) 降到 O(b^(d/2))（最好情况）
#   - 走法顺序至关重要：先搜最好的走法能最大化剪枝（用启发式排序）
#   - 最坏情况（乱序）alpha-beta 与纯 minimax 相同
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


nodes_minimax = [0]
nodes_ab = [0]


def minimax(board, player):
    nodes_minimax[0] += 1
    w = board.winner()
    if w == "X": return 1
    if w == "O": return -1
    if board.is_full(): return 0
    vals = []
    for mv in board.moves():
        board.make(mv, player)
        vals.append(minimax(board, "O" if player=="X" else "X"))
        board.undo(mv)
    return max(vals) if player == "X" else min(vals)


def alpha_beta(board, player, alpha=-math.inf, beta=math.inf):
    nodes_ab[0] += 1
    w = board.winner()
    if w == "X": return 1
    if w == "O": return -1
    if board.is_full(): return 0
    if player == "X":                        # 最大化方
        val = -math.inf
        for mv in board.moves():
            board.make(mv, player)
            val = max(val, alpha_beta(board, "O", alpha, beta))
            board.undo(mv)
            if val >= beta:
                break                        # β 剪枝：对手已有更优选择
            alpha = max(alpha, val)
        return val
    else:                                    # 最小化方
        val = math.inf
        for mv in board.moves():
            board.make(mv, player)
            val = min(val, alpha_beta(board, "X", alpha, beta))
            board.undo(mv)
            if val <= alpha:
                break                        # α 剪枝：我方已有更优选择
            beta = min(beta, val)
        return val


def alpha_beta_sorted(board, player, alpha=-math.inf, beta=math.inf):
    """带启发式排序的 alpha-beta：优先搜中心/角落，最大化剪枝。"""
    nodes_ab[0] += 1
    w = board.winner()
    if w == "X": return 1
    if w == "O": return -1
    if board.is_full(): return 0
    # 启发式排序：中心(4) > 角(0,2,6,8) > 边(1,3,5,7)
    PRIORITY = {4:3, 0:2, 2:2, 6:2, 8:2, 1:1, 3:1, 5:1, 7:1}
    moves = sorted(board.moves(), key=lambda m: -PRIORITY[m])
    if player == "X":
        val = -math.inf
        for mv in moves:
            board.make(mv, player)
            val = max(val, alpha_beta_sorted(board, "O", alpha, beta))
            board.undo(mv)
            if val >= beta: break
            alpha = max(alpha, val)
        return val
    else:
        val = math.inf
        for mv in moves:
            board.make(mv, player)
            val = min(val, alpha_beta_sorted(board, "X", alpha, beta))
            board.undo(mv)
            if val <= alpha: break
            beta = min(beta, val)
        return val


print("== 井字棋空盘搜索：三种算法 ==")
b = Board()

nodes_minimax[0] = 0
score_mm = minimax(b, "X")

nodes_ab[0] = 0
score_ab = alpha_beta(b, "X")

nodes_ab[0] = 0
score_sorted = alpha_beta_sorted(b, "X")

print(f"  minimax        : 评分={score_mm}, 节点={nodes_minimax[0]:,}")
print(f"  alpha-beta     : 评分={score_ab}, 节点={nodes_ab[0]:,}")
print(f"  alpha-beta+排序: 评分={score_sorted}, 节点={nodes_ab[0]:,}")
print(f"  结果一致: {score_mm == score_ab == score_sorted}")
print(f"  剪枝率（vs minimax）: {1 - nodes_ab[0]/nodes_minimax[0]:.1%}")

print("\n== alpha-beta 的剪枝过程 ==")
b2 = Board()
nodes_ab[0] = 0
prunes = []

def alpha_beta_trace(board, player, alpha, beta, depth=0):
    nodes_ab[0] += 1
    w = board.winner()
    if w == "X": return 1
    if w == "O": return -1
    if board.is_full(): return 0
    indent = "  " * depth
    if player == "X":
        val = -math.inf
        for mv in board.moves():
            board.make(mv, player)
            v = alpha_beta_trace(board, "O", alpha, beta, depth+1)
            board.undo(mv)
            val = max(val, v)
            alpha = max(alpha, val)
            if val >= beta:
                prunes.append(f"{indent}β剪枝 @ depth={depth} (α={alpha},β={beta})")
                break
        return val
    else:
        val = math.inf
        for mv in board.moves():
            board.make(mv, player)
            v = alpha_beta_trace(board, "X", alpha, beta, depth+1)
            board.undo(mv)
            val = min(val, v)
            beta = min(beta, val)
            if val <= alpha:
                prunes.append(f"{indent}α剪枝 @ depth={depth} (α={alpha},β={beta})")
                break
        return val

alpha_beta_trace(Board(), "X", -math.inf, math.inf)
print(f"  共 {len(prunes)} 次剪枝")
for p in prunes[:6]:
    print("   ", p)

print("\n== 走法顺序对剪枝率的影响 ==")
for order_name, sorter in (
    ("无排序（原始顺序）", lambda ms: ms),
    ("中心优先", lambda ms: sorted(ms, key=lambda m: -(4 if m==4 else (1 if m in (0,2,6,8) else 0)))),
    ("中心>角>边（最优）", lambda ms: sorted(ms, key=lambda m: -{4:3, 0:2, 2:2, 6:2, 8:2}.get(m, 1))),
):
    nodes_ab[0] = 0
    # 重新运行带排序的 alpha-beta
    def ab_sorted(board, player, alpha, beta):
        nodes_ab[0] += 1
        w = board.winner()
        if w == "X": return 1
        if w == "O": return -1
        if board.is_full(): return 0
        moves = sorter(board.moves())
        if player == "X":
            val = -math.inf
            for mv in moves:
                board.make(mv, player)
                val = max(val, ab_sorted(board, "O", alpha, beta))
                board.undo(mv)
                if val >= beta: break
                alpha = max(alpha, val)
            return val
        else:
            val = math.inf
            for mv in moves:
                board.make(mv, player)
                val = min(val, ab_sorted(board, "X", alpha, beta))
                board.undo(mv)
                if val <= alpha: break
                beta = min(beta, val)
            return val

    ab_sorted(Board(), "X", -math.inf, math.inf)
    print(f"  {order_name:<20}: 节点={nodes_ab[0]:,}")

print("\n== 理论界 ==")
for line in (
    "  最好情况: O(b^(d/2)) —— 相当于搜索深度翻倍",
    "  最坏情况: O(b^d) —— 顺序完全乱时退化为 minimax",
    "  走法排序好的标准：用上一层的结果/历史启发式/评估函数预估",
    "  Killer heuristic: 上一轮剪掉兄弟的走法往往这轮也能剪",
):
    print(" ", line)

print("\n== 与迭代加深结合 ==")
for line in [
    "  迭代加深：深度 1→2→3→... 逐步搜索，时间到就停",
    "  每层结果可用来排序下一层的走法（PV 优先），alpha-beta 剪枝率更高",
    "  总代价 ≈ 最深一层的代价（前面的层数可以忽略）",
    "  这是国际象棋引擎（Stockfish）的标准做法",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 negamax 版的 alpha-beta（零和简化，代码更短）。
# 2. 统计 8 个开局位置的 alpha-beta 搜索节点数，找最优开局。
# 3. 实现转置表（用局面哈希做 key），与纯 alpha-beta 对比节点数。
# 4. 思考：为什么 alpha-beta 返回值与纯 minimax 完全一致？
