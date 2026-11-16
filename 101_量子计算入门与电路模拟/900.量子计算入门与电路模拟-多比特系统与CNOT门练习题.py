# ===== 第900课：量子计算入门与电路模拟-多比特系统与CNOT门 =====
# 知识点：
#   - n 比特寄存器 = 2^n 维状态向量，振幅下标即基态二进制编号
#   - 单比特门作用在第 k 位：按「第 k 位是否为 1」把振幅两两配对做 2×2 变换
#   - CNOT = 可逆计算的灵魂：控制位不变、目标位条件翻转 —— 产生纠缠
#   - 纠缠态无法写成单比特态的张量积 —— 量子计算超越经典的关键资源
#   - 纠缠验证：对子系统求约化密度矩阵（对角 = 经典混合，非对角 = 有纠缠）
# 依赖：无（标准库）
import math
import random

H = [[1 / math.sqrt(2), 1 / math.sqrt(2)],
     [1 / math.sqrt(2), -1 / math.sqrt(2)]]
X = [[0, 1], [1, 0]]


class Register:
    """n 比特寄存器：amp[i] 是基态 |i⟩ 的复振幅（i 的二进制 = 各比特取值）。"""

    def __init__(self, n):
        self.n = n
        self.amp = [0.0 + 0j] * (2 ** n)
        self.amp[0] = 1.0 + 0j                     # 初始 |00...0⟩

    def apply_single(self, gate, target):
        """把 2×2 门作用在 target 位。"""
        step = 1 << target
        for i in range(2 ** self.n):
            if i & step:                           # 只处理 target=0 的配对
                continue
            j = i | step
            a0, a1 = self.amp[i], self.amp[j]
            self.amp[i] = gate[0][0] * a0 + gate[0][1] * a1
            self.amp[j] = gate[1][0] * a0 + gate[1][1] * a1
        return self

    def apply_cnot(self, control, target):
        """CNOT：控制位为 1 时翻转目标位。"""
        step_c, step_t = 1 << control, 1 << target
        for i in range(2 ** self.n):
            if (i & step_c) and not (i & step_t):
                j = i | step_t
                self.amp[i], self.amp[j] = self.amp[j], self.amp[i]
        return self

    def probabilities(self):
        return [abs(a) ** 2 for a in self.amp]

    def measure(self, rng):
        probs = self.probabilities()
        r = rng.random()
        acc = 0.0
        for i, p in enumerate(probs):
            acc += p
            if r < acc:
                # 投影坍缩
                for j in range(2 ** self.n):
                    if j != i:
                        self.amp[j] = 0.0
                self.amp[i] = self.amp[i] / abs(self.amp[i])
                return i
        return 2 ** self.n - 1

    def norm(self):
        return math.sqrt(sum(abs(a) ** 2 for a in self.amp))

    def show_top(self, top=8):
        probs = self.probabilities()
        order = sorted(range(len(probs)), key=lambda i: -probs[i])[:top]
        out = []
        for i in order:
            if probs[i] > 1e-12:
                bits = format(i, f"0{self.n}b")
                out.append(f"|{bits}⟩:{probs[i]:.3f}")
        return "  ".join(out)


def reduced_diag(reg, qubit):
    """第 qubit 位单独看的边缘概率 P(0), P(1)（把其余位求和掉）。"""
    p0 = p1 = 0.0
    for i, a in enumerate(reg.amp):
        if (i >> qubit) & 1:
            p1 += abs(a) ** 2
        else:
            p0 += abs(a) ** 2
    return p0, p1


rng = random.Random(82)

print("== 两比特寄存器 ==")
reg = Register(2)
print(f"  初始: {reg.show_top()}")
reg.apply_single(H, 0)
print(f"  H 于第 0 位: {reg.show_top()}")
print("  H 作用在 1 位上，第 1 位仍是 0 -> 只有 |00⟩ 和 |01⟩ 获得振幅（不均匀）")

print("\n== 贝尔态制备：H + CNOT ==")
bell = Register(2)
bell.apply_single(H, 0)                # 第 0 位叠加
bell.apply_cnot(0, 1)                  # 复制到第 1 位（条件翻转）
print(f"  H(0) + CNOT(0→1): {bell.show_top()}")
print("  振幅只在 |00⟩ 和 |11⟩ 上 —— 两个比特永远同步")
p0, p1 = reduced_diag(bell, 0)
print(f"  第 0 位单独看: P(0)={p0:.3f}, P(1)={p1:.3f}（各自 50%，完全随机）")
print("  但联合测量永远相同 —— 单比特视图丢失了关联 = 纠缠的本质")

print("\n== 纠缠 vs 经典相关（张量积判据）==")


def is_product_state(reg):
    """检验 2 比特态是否可写成 (a|0⟩+b|1⟩)⊗(c|0⟩+d|1⟩)：
    可分离 ⇔ a00·a11 == a01·a10。"""
    a00, a01 = reg.amp[0], reg.amp[1]
    a10, a11 = reg.amp[2], reg.amp[3]
    return abs(a00 * a11 - a01 * a10) < 1e-9


reg2 = Register(2)
reg2.apply_single(H, 0)
print(f"  H 后 (无 CNOT): 可分离态 = {is_product_state(reg2)}")
print(f"  贝尔态 (H+CNOT): 可分离态 = {is_product_state(bell)}")
print("  a00·a11 ≠ a01·a10 <=> 振幅矩阵秩 > 1 <=> 纠缠 —— 一行判据看清纠缠")

print("\n== CNOT 的可逆性 ==")
reg3 = Register(2)
reg3.amp[2] = 1.0 + 0j                            # |10⟩
reg3.apply_cnot(0, 1)
print(f"  CNOT(0→1)|10⟩ = {reg3.show_top()}（控制位 0 → 目标不变）")
reg3.apply_cnot(0, 1)
print(f"  再来一次 CNOT(0→1) = {reg3.show_top()}（自逆：跑两次回到原态）")

print("\n== 测量坍缩 ==")
reg4 = Register(2)
reg4.apply_single(H, 0)
reg4.apply_cnot(0, 1)
outcome = reg4.measure(rng)
print(f"  测量贝尔态 -> 结果 {format(outcome, '04b')}（只可能是 00 或 11）")
print(f"  坍缩后归一化: {reg4.show_top()}（纯态）")

print("\n== 3 比特：GHZ 态（纠缠的推广）==")
ghz = Register(3)
ghz.apply_single(H, 0)
ghz.apply_cnot(0, 1)
ghz.apply_cnot(1, 2)
print(f"  GHZ = {ghz.show_top()}   （|000⟩ 与 |111⟩ 的叠加，三体纠缠）")
shots = [0, 0]
for _ in range(1000):
    g = Register(3)
    g.apply_single(H, 0)
    g.apply_cnot(0, 1)
    g.apply_cnot(1, 2)
    shots[g.measure(rng) in (0, 7)] += 1
print(f"  1000 次测量: 合法结果(000/111) {shots[0]} 次 + 非法 {shots[1]}（应为 0）")

print("\n== 小结 ==")
for line in (
    "  多比特 = 2^n 维向量；单比特门按位配对作用，代价 O(2^n)",
    "  CNOT 不可少：仅靠单比特门永远造不出纠缠（可分离态封闭）",
    "  纠缠判据一行可写：a00·a11 ≠ a01·a10（秩判据的 2×2 特例）",
    "  901 课：把这些原语封装成电路模拟器",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 SWAP 门（三个 CNOT 组成）并验证交换两个比特的态。
# 2. 实现 CZ 门（控制-Z）：对角门 diag(1,1,1,-1)，验证 CZ = (H⊗H)·CNOT·(H⊗H)。
# 3. 制备 4 比特 GHZ 并统计测量直方图。
# 4. 思考：为什么 CNOT 用「交换振幅」实现而不用 2×2 矩阵？控制位是叠加态时
#    发生了什么？
