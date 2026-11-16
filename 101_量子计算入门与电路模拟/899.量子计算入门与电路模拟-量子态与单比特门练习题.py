# ===== 第899课：量子计算入门与电路模拟-量子态与单比特门 =====
# 知识点：
#   - 量子态 = 复数向量：|ψ⟩ = α|0⟩ + β|1⟩，|α|² + |β|² = 1（归一化）
#   - 测量的玻恩规则：测得 |0⟩ 的概率 = |α|² —— 概率来自振幅的模方
#   - 单比特门 = 2×2 幺正矩阵：X(翻转)、Z(相位翻转)、H(叠加)、S/T(相位)
#   - 幺正性保证总概率守恒 —— 量子计算是可逆的（除了测量）
#   - 本课用纯 Python 复数列表模拟：n 个量子比特 = 2^n 维状态向量
# 依赖：无（标准库）
import cmath
import math
import random


class Qubit:
    """单比特量子态。"""

    def __init__(self, alpha=1.0 + 0j, beta=0.0 + 0j):
        norm = math.sqrt(abs(alpha) ** 2 + abs(beta) ** 2)
        self.alpha = alpha / norm
        self.beta = beta / norm

    def apply(self, gate):
        """gate = [[a, b], [c, d]]：新 α = a·α + b·β。"""
        a, b = gate[0]
        c, d = gate[1]
        return Qubit(a * self.alpha + b * self.beta,
                     c * self.alpha + d * self.beta)

    def probabilities(self):
        return abs(self.alpha) ** 2, abs(self.beta) ** 2

    def measure(self, rng):
        p0, p1 = self.probabilities()
        return 0 if rng.random() < p0 else 1

    def show(self):
        def fmt(z):
            re, im = z.real, z.imag
            return f"{re:+.3f}{im:+.3f}i"
        return f"{fmt(self.alpha)}·|0⟩ + {fmt(self.beta)}·|1⟩"


X = [[0, 1], [1, 0]]
Z = [[1, 0], [0, -1]]
H = [[1 / math.sqrt(2), 1 / math.sqrt(2)],
     [1 / math.sqrt(2), -1 / math.sqrt(2)]]
S = [[1, 0], [0, 1j]]
T = [[1, 0], [0, cmath.exp(1j * math.pi / 4)]]

print("== 量子态的叠加与测量 ==")
q0 = Qubit()                                    # |0⟩
print(f"  |0⟩ = {q0.show()}   测量概率 P(0)={q0.probabilities()[0]:.3f}")
qx = q0.apply(X)
print(f"  X|0⟩ = {qx.show()}   （X 是经典非门）")
qh = q0.apply(H)
print(f"  H|0⟩ = {qh.show()}   （均匀叠加：两边振幅各 1/√2）")
rng = random.Random(81)
counts = [0, 0]
for _ in range(1000):
    counts[qh.measure(rng)] += 1
print(f"  测量 1000 次: |0⟩ {counts[0]} 次 / |1⟩ {counts[1]} 次（各 ~50%）")

print("\n== 幺正性：概率守恒 ==")
for name, gate in (("X", X), ("Z", Z), ("H", H), ("S", S)):
    p0, p1 = q0.apply(gate).probabilities()
    print(f"  {name}|0⟩: P(0)+P(1) = {p0 + p1:.6f}")
print("  无论怎么变，总概率恒为 1 —— 这是幺正矩阵的几何意义（旋转/反射）")

print("\n== 相位不可直接观测，但干涉可观测 ==")
q1 = Qubit(0.0 + 0j, 1.0 + 0j)                   # |1⟩
qh1 = q1.apply(H)
print(f"  H|1⟩ = {qh1.show()}   （注意 β 前的负号：|−⟩ 态）")
print("  H|0⟩ 与 H|1⟩ 振幅符号不同 —— 测量概率相同，但后续干涉行为不同")
inter = Qubit(1 / math.sqrt(2), -1 / math.sqrt(2)).apply(H)
print(f"  H|−⟩ = {inter.show()}   （|−⟩ 再过 H 回到 |1⟩：负号干涉相消）")
inter2 = Qubit(1 / math.sqrt(2), 1 / math.sqrt(2)).apply(H)
print(f"  H|+⟩ = {inter2.show()}   （|+⟩ 再过 H 回到 |0⟩：正号相长）")

print("\n== T 门与相位旋转 ==")
q = q0.apply(H).apply(T)
print(f"  H|0⟩ 再加 T: {q.show()}")
print("  T 给 |1⟩ 分量加 45° 相位 —— 单独看不变化，测量概率不变；")
print("  但多个 T 与 H 交替就能合成任意旋转（通用门集 {H,T,CNOT}）")

print("\n== 单比特电路 = 矩阵连乘 ==")
qz = q0.apply(H).apply(Z).apply(H)
print(f"  H→Z→H 作用在 |0⟩: {qz.show()}   （等价于 X|0⟩ = |1⟩，Z 夹在 H 间当非门）")
qseq = q0.apply(H).apply(H)
print(f"  H→H 作用在 |0⟩:   {qseq.show()}   （H·H = I，门自逆）")

print("\n== 小结 ==")
for line in (
    "  态向量 + 幺正门 + 玻恩测量 = 量子计算的全部数学地基",
    "  叠加不是『同时是 0 和 1』，而是复振幅的线性组合（可干涉）",
    "  相位不可直接测，却决定干涉结果 —— 量子算法全靠它做文章",
    "  900 课：把单比特门扩展到多比特寄存器（张量积 + CNOT）",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 RY(θ) 门 [[cosθ/2, −sinθ/2], [sinθ/2, cosθ/2]]，扫描 θ∈[0,π] 的测量概率。
# 2. 验证幺正性：对每个门检查 U·U† = I（数值误差 < 1e-12）。
# 3. 实现「布洛赫球」可视化：把 (α,β) 映射为 (x,y,z) 坐标打印文本散点。
# 4. 思考：为什么测量不可逆？从「幺正 vs 投影」的数学差异解释。
