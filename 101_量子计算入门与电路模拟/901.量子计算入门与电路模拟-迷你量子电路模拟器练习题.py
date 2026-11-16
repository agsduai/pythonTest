# ===== 第901课：量子计算入门与电路模拟-迷你量子电路模拟器 =====
# 知识点：
#   - 电路 = 按时间顺序施加的门序列；模拟 = 依次把门作用到态向量
#   - 引擎封装：add_gate / run / sample（多次测量出直方图）
#   - 与 899/900 的区别：不再手写逐步操作，用「电路描述」驱动
#   - 状态向量模拟器内存 O(2^n)：20 比特 = 100 万复数 —— 模拟器的现实边界
#   - 真实量子计算机是「硬件执行同样的电路」—— 模拟器用于验证与教学
# 依赖：无（标准库）
import math
import random


H = [[1 / math.sqrt(2), 1 / math.sqrt(2)],
     [1 / math.sqrt(2), -1 / math.sqrt(2)]]
X = [[0, 1], [1, 0]]
Z = [[1, 0], [0, -1]]
S = [[1, 0], [0, 1j]]
I2 = [[1, 0], [0, 1]]


def ry(theta):
    c, s = math.cos(theta / 2), math.sin(theta / 2)
    return [[c, -s], [s, c]]


class Circuit:
    def __init__(self, nqubits):
        self.n = nqubits
        self.gates = []                        # (类型, 参数)

    def h(self, q):
        self.gates.append(("H", q))
        return self

    def x(self, q):
        self.gates.append(("X", q))
        return self

    def ry(self, q, theta):
        self.gates.append(("RY", q, theta))
        return self

    def cnot(self, control, target):
        self.gates.append(("CNOT", control, target))
        return self

    def run(self, init=None):
        """返回运行后的 Register 态向量。"""
        reg = _Reg(self.n)
        if init is not None:
            reg.amp = [complex(a) for a in init]
        for g in self.gates:
            if g[0] == "CNOT":
                reg.apply_cnot(g[1], g[2])
            elif g[0] == "RY":
                reg.apply_single(ry(g[2]), g[1])
            else:
                reg.apply_single({"H": H, "X": X, "Z": Z, "S": S}[g[0]], g[1])
        return reg

    def sample(self, shots, rng):
        """跑 shots 次：每次重置电路 + 测量（模拟真实硬件的重复执行）。"""
        hist = {}
        for _ in range(shots):
            reg = self.run()
            outcome = reg.measure(rng)
            key = format(outcome, f"0{self.n}b")
            hist[key] = hist.get(key, 0) + 1
        return hist

    def draw(self):
        """文本电路图（按时序列）。"""
        depth = {}
        lines = {}
        for g in self.gates:
            if g[0] == "CNOT":
                qs = [g[1], g[2]]
            else:
                qs = [g[1]]
            d = max(depth.get(q, -1) for q in qs) + 1
            for q in qs:
                depth[q] = d
            label = "●" if g[0] == "CNOT" else g[0]
            target = g[2] if g[0] == "CNOT" else None
            for q in range(self.n):
                if q in qs:
                    ch = label if q != target else "⊕"
                    lines.setdefault(q, []).append((d, ch))
        width = max(depth.values()) + 1
        grid = {q: ["─"] * width for q in range(self.n)}
        for q, cells in lines.items():
            for d, ch in cells:
                grid[q][d] = ch
        for q in range(self.n - 1, -1, -1):
            print(f"  q{q}: " + "".join(grid[q]))
        return self


class _Reg:
    """内部寄存器（与 900 课相同的实现）。"""

    def __init__(self, n):
        self.n = n
        self.amp = [0.0 + 0j] * (2 ** n)
        self.amp[0] = 1.0 + 0j

    def apply_single(self, gate, target):
        step = 1 << target
        for i in range(2 ** self.n):
            if i & step:
                continue
            j = i | step
            a0, a1 = self.amp[i], self.amp[j]
            self.amp[i] = gate[0][0] * a0 + gate[0][1] * a1
            self.amp[j] = gate[1][0] * a0 + gate[1][1] * a1

    def apply_cnot(self, control, target):
        sc, st = 1 << control, 1 << target
        for i in range(2 ** self.n):
            if (i & sc) and not (i & st):
                j = i | st
                self.amp[i], self.amp[j] = self.amp[j], self.amp[i]

    def probabilities(self):
        return [abs(a) ** 2 for a in self.amp]

    def measure(self, rng):
        probs = self.probabilities()
        r, acc = rng.random(), 0.0
        for i, p in enumerate(probs):
            acc += p
            if r < acc:
                for j in range(2 ** self.n):
                    if j != i:
                        self.amp[j] = 0.0
                if abs(self.amp[i]) > 0:
                    self.amp[i] /= abs(self.amp[i])
                return i
        return 2 ** self.n - 1

    def show_top(self, top=6):
        probs = self.probabilities()
        order = sorted(range(len(probs)), key=lambda i: -probs[i])[:top]
        return "  ".join(f"|{format(i, f'0{self.n}b')}⟩:{probs[i]:.3f}"
                         for i in order if probs[i] > 1e-12)


rng = random.Random(91)

print("== 第一个电路：贝尔态 ==")
c1 = Circuit(2).h(0).cnot(0, 1)
c1.draw()
reg = c1.run()
print(f"  状态: {reg.show_top()}")

print("\n== 采样直方图（模拟硬件重复执行 2000 次）==")
hist = c1.sample(2000, rng)
for key in sorted(hist):
    print(f"  |{key}⟩: {'#' * int(hist[key] / max(hist.values()) * 40)} {hist[key]}")
print(f"  合计 = {sum(hist.values())}，只有 00/11 出现 —— 与理论一致")

print("\n== 参数化电路：RY 旋转 ==")
c2 = Circuit(1).ry(0, math.pi / 3)
reg2 = c2.run()
p0 = abs(reg2.amp[0]) ** 2
print(f"  RY(π/3)|0⟩: P(0) = {p0:.4f}（理论 cos²(π/6) = {math.cos(math.pi / 6) ** 2:.4f}）")
hist2 = c2.sample(2000, rng)
print(f"  采样: 0 出现 {hist2.get('0', 0) / 2000:.1%}（约 {p0:.1%}）")

print("\n== 经典条件电路：隐形传态预备 ==")
c3 = Circuit(2).h(0).cnot(0, 1).x(1)
reg3 = c3.run()
print(f"  H·CNOT·X: {reg3.show_top()}   （X 改写目标位但保持纠缠结构）")

print("\n== 门序列与矩阵等价 ==")
print("  电路按从左到右执行 = 矩阵按反序相乘 U_n···U_1")
print("  模拟器逐门施加等价于逐步矩阵-向量乘法，复杂度 = 门数 × 2^n")
print(f"  3 比特电路单门成本 = {2 ** 3} 次复数运算；20 比特 = {2 ** 20} 次 —— 状态爆炸边界")

print("\n== 采样 vs 精确概率 ==")
exact_c = Circuit(2).h(0).ry(1, math.pi / 4).cnot(0, 1)
reg4 = exact_c.run()
probs = reg4.probabilities()
hist_exact = exact_c.sample(2000, rng)
print(f"  {'基态':<8}{'精确概率':>10}{'采样(2000)':>12}")
for i in range(4):
    key = format(i, "02b")
    print(f"  |{key}⟩  {probs[i]:>10.4f}{hist_exact.get(key, 0) / 2000:>12.1%}")
print("  采样是精确概率的蒙特卡洛估计 —— 2000 次的统计误差约 ±1%")

print("\n== 小结 ==")
for line in (
    "  电路 = 门的时间序列；模拟器 = 态向量上的逐门矩阵乘法",
    "  sample() 复刻真实硬件的工作方式：同一电路重复执行出统计分布",
    "  状态向量法 O(2^n) 内存：30 比特已是超算级别 —— 算法设计的目标是少比特",
    "  902 课：纠缠的第一个『杀手级应用』—— 贝尔不等式",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给 Circuit 加 CZ 门与 SWAP 门（CNOT 组合），并验证功能。
# 2. 实现电路的「逆电路」生成（门反序 + 每个门取逆），验证 run 后恢复 |0⟩。
# 3. 模拟 10 比特 GHZ 并统计内存与时间，画出规模-成本曲线（文本表格）。
# 4. 思考：为什么模拟器需要「每次采样重跑电路」而不是「测量后继续」？
#    测量的不可逆性如何体现在 API 设计上？
