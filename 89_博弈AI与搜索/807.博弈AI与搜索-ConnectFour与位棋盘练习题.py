# ===== 第807课：博弈AI与搜索-Connect Four与位棋盘 =====
# 知识点：
#   - Connect Four（四子棋）：7 列 × 6 行，棋子重力下落，先连成 4 个者胜
#   - 分支因子 ~7、深度可达 42，比井字棋大得多，需要 alpha-beta + 好评估
#   - 位棋盘 bitboard：每方用一个 64 位整数表示棋盘，走法 = 位或运算
#   - 位运算判断胜负：4 个方向的位掩码做 AND 检查
#   - 列编码：每列 7 位（底部第 0 位），7 列共 49 位
#   - 本课实现位棋盘 + alpha-beta，并对比效率
# 依赖：无（标准库）
import math
import time

WIDTH, HEIGHT = 7, 6
BOTTOM_MASK = sum(1 << (c * (HEIGHT + 1)) for c in range(WIDTH))


def col_mask(c):
    """第 c 列的列掩码（含哨兵位）。"""
    return ((1 << (HEIGHT + 1)) - 1) << (c * (HEIGHT + 1))


def top_of_col(c):
    """第 c 列最高可放位置的位。"""
    base = c * (HEIGHT + 1)
    for r in range(HEIGHT):
        bit = 1 << (base + r)
        # 空位检查由调用方处理
        pass
    return base


class BitBoard:
    """用两个 64 位整数表示红方与黄方的棋盘。"""

    def __init__(self):
        self.red = 0        # 红方棋子的位掩码
        self.yellow = 0     # 黄方棋子的位掩码
        self.heights = [0] * WIDTH   # 每列已有几个棋子

    def can_play(self, col):
        return self.heights[col] < HEIGHT

    def play(self, col, player):
        """player: 0=红, 1=黄。返回是否成功。"""
        if not self.can_play(col):
            return False
        bit = 1 << (col * (HEIGHT + 1) + self.heights[col])
        if player == 0:
            self.red |= bit
        else:
            self.yellow |= bit
        self.heights[col] += 1
        return True

    def undo(self, col, player):
        """撤销：减高度并清位。"""
        self.heights[col] -= 1
        bit = ~(1 << (col * (HEIGHT + 1) + self.heights[col]))
        if player == 0:
            self.red &= bit
        else:
            self.yellow &= bit

    def check_win(self, player):
        """检查 4 连：用位运算检查 4 个方向。"""
        b = self.red if player == 0 else self.yellow
        # 水平: 位移 1 列
        m = b & (b >> (HEIGHT + 1))
        if m & (m >> (2 * (HEIGHT + 1))):
            return True
        # 垂直: 位移 1 行
        m = b & (b >> 1)
        if m & (m >> 2):
            return True
        # 对角 /
        m = b & (b >> HEIGHT)
        if m & (m >> (2 * HEIGHT)):
            return True
        # 对角 \
        m = b & (b >> (HEIGHT + 2))
        if m & (m >> (2 * (HEIGHT + 2))):
            return True
        return False

    def is_full(self):
        return all(h >= HEIGHT for h in self.heights)

    def render(self):
        lines = []
        for r in range(HEIGHT - 1, -1, -1):
            row = []
            for c in range(WIDTH):
                bit = 1 << (c * (HEIGHT + 1) + r)
                if self.red & bit:
                    row.append("●")
                elif self.yellow & bit:
                    row.append("○")
                else:
                    row.append("·")
            lines.append(" ".join(row))
        return "\n".join(lines) + "\n  " + " ".join(str(c) for c in range(WIDTH))


def evaluation(bb, player):
    """简单评估：统计 3 连/2 连的数量并加权。"""
    opp = 1 - player
    b_me = bb.red if player == 0 else bb.yellow
    b_opp = bb.red if opp == 0 else bb.yellow
    score = 0
    # 检查 4 个方向的连子数
    shifts = [(HEIGHT+1, "水平"), (1, "垂直"), (HEIGHT, "斜/"), (HEIGHT+2, "斜\\")]
    for shift, name in shifts:
        m2 = b_me & (b_me >> shift)
        m3 = m2 & (b_me >> 2*shift)
        score += bin(m2).count("1") * 3 + bin(m3).count("1") * 30
        o2 = b_opp & (b_opp >> shift)
        o3 = o2 & (b_opp >> 2*shift)
        score -= bin(o3).count("1") * 25
    # 中心列加分
    center = col_mask(3)
    center_me = b_me & center
    score += bin(center_me).count("1") * 6
    return score


nodes = [0]


def alphabeta_cf(bb, player, depth, alpha, beta):
    nodes[0] += 1
    if bb.check_win(0): return 1000 - depth
    if bb.check_win(1): return -1000 + depth
    if bb.is_full() or depth <= 0:
        return evaluation(bb, player)

    is_max = (player == 0)
    val = -math.inf if is_max else math.inf
    # 中心列优先
    cols = [3, 2, 4, 1, 5, 0, 6]
    for c in cols:
        if not bb.can_play(c):
            continue
        bb.play(c, player)
        v = alphabeta_cf(bb, 1-player, depth-1, alpha, beta)
        bb.undo(c, player)
        if is_max:
            val = max(val, v); alpha = max(alpha, val)
        else:
            val = min(val, v); beta = min(beta, val)
        if alpha >= beta:
            break
    return val


def best_move_cf(bb, player, depth=6):
    best, best_col = -math.inf, None
    alpha, beta = -math.inf, math.inf
    for c in [3, 2, 4, 1, 5, 0, 6]:
        if not bb.can_play(c):
            continue
        bb.play(c, player)
        v = alphabeta_cf(bb, 1-player, depth-1, alpha, beta)
        bb.undo(c, player)
        if (player == 0 and v > best) or (player == 1 and v < best):
            if player == 0: best = v
            else: best = v
            best_col = c
        if player == 0:
            alpha = max(alpha, best)
        else:
            beta = min(beta, best)
    return best_col, best


print("== Connect Four 位棋盘 ==")
bb = BitBoard()
bb.play(3, 0); bb.play(3, 1); bb.play(3, 0)
bb.play(4, 1); bb.play(4, 0)
print(bb.render())
print(f"  红方(●)位掩码 = {bb.red:048b}")
print(f"  4 连检测: 红方={bb.check_win(0)} 黄方={bb.check_win(1)}")

print("\n== 位运算检测 4 连（水平方向）==")
# 构造水平 4 连
h = BitBoard()
for c in range(4):
    h.play(c, 0)
print(h.render())
print(f"  红方位掩码 = {h.red:#b}")
print(f"  检查水平 4 连 = {h.check_win(0)}")
m = h.red & (h.red >> (HEIGHT + 1))
m2 = m & (m >> (2 * (HEIGHT + 1)))
print(f"  第一步 AND: {m:#b}（连续 2 对）")
print(f"  第二步 AND: {m2:#b}（连续 4 对的非零位）")

print("\n== Alpha-Beta 求解 ==")
b2 = BitBoard()
for c in (3, 4, 3, 4, 3):
    b2.play(c, (0 if c == 3 else 1))
print(b2.render())
t0 = time.perf_counter()
nodes[0] = 0
col, val = best_move_cf(b2, 1, depth=7)
t1 = time.perf_counter()
print(f"  黄方最优列 = {col} 评分={val} 节点={nodes[0]:,} 耗时={t1-t0:.3f}s")

print("\n== 深度对搜索时间的影响 ==")
for d in (4, 5, 6, 7, 8):
    b3 = BitBoard()
    nodes[0] = 0
    t0 = time.perf_counter()
    best_move_cf(b3, 0, depth=d)
    dt = time.perf_counter() - t0
    print(f"  depth={d}: 节点={nodes[0]:>8,} 耗时={dt:.3f}s")
print("  位棋盘 + alpha-beta 的效率：depth=8 在标准 Python 内仍可接受")

print("\n== 位棋盘 vs 对象棋盘 ==")
for line in (
    "  位棋盘: 走法 = 位或，胜负 = 位掩码 AND，极快（每步纳秒级）",
    "  对象棋盘: 二维数组，可读性好，但慢 10~100×",
    "  Connect Four 的位棋盘只需要 2×49 = 98 bit，两个 Python int 就够",
    "  国际象棋引擎用 Magic Bitboards 做滑动子攻击检测（更复杂的位技巧）",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  列编码留 1 个哨兵位（每列 HEIGHT+1 位）避免相邻列位溢出",
    "  check_win 的 4 次位移+AND 是 O(1) 的——这就是位棋盘的威力",
    "  Java/Python 的 long/int 虽然大，但 C/C++ 用 uint64_t 更快",
    "  Connect Four 已被完全求解（7x6 先手必赢，首手放中心列）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「立即赢/立即输」检测（跳过搜索直接判断）。
# 2. 实现迭代加深 + 时间限制（超时返回当前最优）。
# 3. 用 Zobrist 哈希 + 转置表缓存局面，减少重复搜索。
# 4. 思考：为什么每列留一个「哨兵位」可以防止位运算跨列溢出？
