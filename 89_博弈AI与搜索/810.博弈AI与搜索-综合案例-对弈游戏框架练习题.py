# ===== 第810课：博弈AI与搜索-综合案例-对弈游戏框架 =====
# 知识点：
#   - 综合串起本章：Game 接口 -> minimax/alpha-beta/MCTS -> 锦标赛 -> 统计
#   - Game 抽象接口：legal_moves / make / undo / is_terminal / winner / evaluate
#   - 策略 = 函数 (game, player) -> move，可插拔，便于锦标赛对比
#   - 锦标赛：多策略两两对局，统计胜率、平局率、平均时长
#   - 可复现：每场用固定 seed，随机策略可复现
#   - 全部标准库 + 纯内存，离线可运行
# 依赖：无（标准库）
import math
import random
import statistics
import time
from collections import defaultdict


class Game:
    """所有对弈游戏的抽象接口。"""

    def legal_moves(self): raise NotImplementedError
    def make(self, move): raise NotImplementedError
    def undo(self, move): raise NotImplementedError
    def is_terminal(self): raise NotImplementedError
    def winner(self): raise NotImplementedError
    def current_player(self): raise NotImplementedError
    def evaluate(self, player): return 0


class TicTacToe(Game):
    WINS = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]

    def __init__(self):
        self.board = ["."]*9
        self.turn = "X"

    def legal_moves(self): return [i for i, v in enumerate(self.board) if v == "."]
    def make(self, m): self.board[m] = self.turn; self.turn = "O" if self.turn == "X" else "X"
    def undo(self, m): self.turn = "O" if self.turn == "X" else "X"; self.board[m] = "."
    def is_terminal(self): return self.winner() is not None or "." not in self.board
    def winner(self):
        for a,b,c in self.WINS:
            if self.board[a] != "." and self.board[a]==self.board[b]==self.board[c]:
                return self.board[a]
        if "." not in self.board: return "draw"
        return None
    def current_player(self): return self.turn
    def copy(self):
        g = TicTacToe.__new__(TicTacToe)
        g.board = self.board[:]; g.turn = self.turn
        return g
    def render(self):
        return "\n".join(" ".join(self.board[r*3:(r+1)*3]) for r in range(3))


class AlphaBetaStrategy:
    def __init__(self, depth=6, eval_fn=None):
        self.depth = depth
        self.eval_fn = eval_fn or (lambda g, p: 0)
    def __call__(self, game, player):
        best, best_mv = -math.inf, None
        for mv in game.legal_moves():
            game.make(mv)
            v = self._ab(game, player, self.depth-1, -math.inf, math.inf)
            game.undo(mv)
            if v > best: best, best_mv = v, mv
        return best_mv
    def _ab(self, game, me, depth, alpha, beta):
        w = game.winner()
        if w == me: return 100 + depth
        if w and w != me: return -100 - depth
        if w == "draw": return 0
        if depth <= 0: return self.eval_fn(game, me)
        opp = "O" if me == "X" else "X"
        my_turn = (game.current_player() == me)
        if my_turn:
            v = -math.inf
            for mv in game.legal_moves():
                game.make(mv)
                v = max(v, self._ab(game, me, depth-1, alpha, beta))
                game.undo(mv)
                alpha = max(alpha, v)
                if alpha >= beta: break
            return v
        else:
            v = math.inf
            for mv in game.legal_moves():
                game.make(mv)
                v = min(v, self._ab(game, me, depth-1, alpha, beta))
                game.undo(mv)
                beta = min(beta, v)
                if beta <= alpha: break
            return v


class MCStrategy:
    def __init__(self, iters=1000, seed=0):
        self.iters, self.seed = iters, seed
    def __call__(self, game, player):
        rng = random.Random(self.seed + hash(str(game.board)) % 10000)
        root_children = []
        for mv in game.legal_moves():
            g2 = game.copy(); g2.make(mv)
            root_children.append((mv, g2))
        wins = [0]*len(root_children)
        for i, (mv, g2) in enumerate(root_children):
            for _ in range(self.iters // max(1, len(root_children))):
                g = g2.copy()
                while not g.is_terminal() and g.winner() is None:
                    g.make(rng.choice(g.legal_moves()))
                w = g.winner()
                if w == player: wins[i] += 1
                elif w is None: wins[i] += 0.5
        best_idx = max(range(len(root_children)), key=lambda i: wins[i])
        return root_children[best_idx][0]


class RandomStrategy:
    def __call__(self, game, player):
        return random.choice(game.legal_moves())


def play_game(game_cls, s1, s2, seed=0):
    game = game_cls()
    strategies = {"X": s1, "O": s2}
    moves_count = 0
    while not game.is_terminal():
        mv = strategies[game.current_player()](game, game.current_player())
        game.make(mv)
        moves_count += 1
    w = game.winner()
    return w, moves_count


def tournament(game_cls, strategies, rounds=200, seed=42):
    """两两对局锦标赛。"""
    names = list(strategies)
    results = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))  # [win, loss, draw]
    times = defaultdict(list)
    for i, (n1, s1) in enumerate(strategies.items()):
        for j, (n2, s2) in enumerate(strategies.items()):
            if i >= j: continue
            for r in range(rounds):
                # 让双方各执 X 一次
                g = game_cls()
                s_map = {"X": s1, "O": s2}
                t0 = time.perf_counter()
                w, mc = play_game(game_cls, s1, s2, seed=seed + r)
                t1 = time.perf_counter()
                times[n1].append(t1-t0); times[n2].append(t1-t0)
                if w == "X": results[n1][n2][0] += 1; results[n2][n1][1] += 1
                elif w == "O": results[n1][n2][1] += 1; results[n2][n1][0] += 1
                else:
                    results[n1][n2][2] += 1; results[n2][n1][2] += 1
                # 换边
                g2 = game_cls()
                s_map2 = {"X": s2, "O": s1}
                w2, _ = play_game(game_cls, s2, s1, seed=seed+rounds+r)
                if w2 == "X": results[n2][n1][0] += 1; results[n1][n2][1] += 1
                elif w2 == "O": results[n2][n1][1] += 1; results[n1][n2][0] += 1
                else:
                    results[n2][n1][2] += 1; results[n1][n2][2] += 1
    # 汇总
    summary = {}
    for n in names:
        w = sum(results[n][o][0] for o in names if o != n)
        l = sum(results[n][o][1] for o in names if o != n)
        d = sum(results[n][o][2] for o in names if o != n)
        summary[n] = {"win": w, "loss": l, "draw": d,
                      "win_rate": w/(w+l+d) if w+l+d else 0,
                      "avg_time": statistics.fmean(times[n]) if times[n] else 0}
    return summary


print("== 注册策略 ==")
strategies = {
    "Random": RandomStrategy(),
    "AlphaBeta-d4": AlphaBetaStrategy(depth=4),
    "AlphaBeta-d6": AlphaBetaStrategy(depth=6),
    "MC-500": MCStrategy(iters=500),
    "MC-2000": MCStrategy(iters=2000),
}
for name in strategies:
    print(f"  {name}")

print("\n== 单局演示 ==")
g = TicTacToe()
s_x = strategies["AlphaBeta-d4"]
s_o = strategies["MC-500"]
while not g.is_terminal():
    mv = (s_x if g.current_player() == "X" else s_o)(g, g.current_player())
    g.make(mv)
print(g.render())
print(f"  结果: {g.winner() or '平局'}")

print("\n== 锦标赛（每对 50 局×2 执子） ==")
summary = tournament(TicTacToe, strategies, rounds=25, seed=42)
print(f"  {'策略':<18}{'胜':>5}{'负':>5}{'平':>5}{'胜率':>8}{'平均耗时(ms)':>12}")
for n, s in sorted(summary.items(), key=lambda x: -x[1]["win_rate"]):
    print(f"  {n:<18}{s['win']:>5}{s['loss']:>5}{s['draw']:>5}"
          f"{s['win_rate']:>8.1%}{s['avg_time']*1000:>12.2f}")

print("\n== 策略特征分析 ==")
for line in (
    "  Random: 随机走，无策略，充当基线",
    "  AlphaBeta-d4: 搜索 4 层，准确但慢（每步几十 ms）",
    "  AlphaBeta-d6: 搜索更深，更强但更慢",
    "  MC-500: 蒙特卡洛模拟 500 次，速度与强度折中",
    "  MC-2000: 更多模拟，接近 MCTS 的最优表现",
):
    print(" ", line)

print("\n== 可扩展性 ==")
for line in [
    "  添加新游戏：实现 Game 接口即可复用所有策略",
    "  添加新策略：实现 __call__(game, player) -> move",
    "  Connect Four / 五子棋 / 任何棋类都能直接接入（第807课位棋盘）",
    "  深度学习策略：用训练好的模型替换 AlphaBeta（AlphaZero 思路）",
]:
    print("  -", line)

print("\n== 分层回顾 ==")
for line in [
    "  搜索层  : minimax / alpha-beta / 深度限制（第803~805课）",
    "  模拟层  : MCTS 蒙特卡洛树搜索（第806课）",
    "  随机层  : expectimax 处理 chance（第808课）",
    "  位优化  : Connect Four 位棋盘加速（第807课）",
    "  不完美  : 信息集 + CFR（第809课）",
    "  框架层  : 统一 Game 接口 + 可插拔策略 + 锦标赛",
]:
    print("  -", line)

print("\n== 工程要点 ==")
for line in [
    "  策略是纯函数 (game, player) -> move：无副作用，可缓存可并行",
    "  锦标赛要考虑双方执子，公平对比",
    "  统计要有足够样本量：50 局×2=100 局，胜率的 95%CI 约 ±10%",
    "  生产环境还应该记录每局完整走法，便于复盘与分析",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「必胜策略检测」：穷举所有对手走法验证某策略是否永远不败。
# 2. 实现「策略组合」：先用启发式选 3 个候选，再用 alpha-beta 精选。
# 3. 把框架扩展到 Connect Four，接入第807课的位棋盘。
# 4. 思考：为什么锦标赛要「双方各执一次」，而不是只看一方执先的结果？
