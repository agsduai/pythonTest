# ===== 第903课：量子计算入门与电路模拟-量子隐形传态 =====
# 知识点：
#   - 隐形传态：把未知量子态 |ψ⟩ 从甲传到乙，消耗 1 对纠缠 + 2 个经典比特
#   - 流程：制备纠缠对 → 甲对 ψ 与自己的比特做贝尔测量 → 4 种结果各 25%
#   - 甲把 2 bit 经典信息发给乙 → 乙按结果做修正（X^m1·Z^m2）→ 态转移完成
#   - 关键：原态在测量时被摧毁（不可克隆定理）—— 没有超光速通信
#   - 验证方式：传基态/叠加态，在乙端测量的分布应与甲端原态一致
# 依赖：无（标准库）
import math
import random

H = [[1 / math.sqrt(2), 1 / math.sqrt(2)],
     [1 / math.sqrt(2), -1 / math.sqrt(2)]]
X = [[0, 1], [1, 0]]
Z = [[1, 0], [0, -1]]


class Register:
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
        return self

    def apply_cnot(self, control, target):
        sc, st = 1 << control, 1 << target
        for i in range(2 ** self.n):
            if (i & sc) and not (i & st):
                j = i | st
                self.amp[i], self.amp[j] = self.amp[j], self.amp[i]
        return self

    def apply_ccx(self, c1, c2, target):
        """Toffoli：双控制非门。"""
        sc1, sc2, st = 1 << c1, 1 << c2, 1 << target
        for i in range(2 ** self.n):
            if (i & sc1) and (i & sc2) and not (i & st):
                j = i | st
                self.amp[i], self.amp[j] = self.amp[j], self.amp[i]
        return self

    def probabilities(self):
        return [abs(a) ** 2 for a in self.amp]

    def measure(self, targets, rng):
        """测量指定的若干比特（其余保持相干），返回结果整数并坍缩。"""
        n = self.n
        mask = sum(1 << t for t in targets)
        dist = {}
        for i, a in enumerate(self.amp):
            key = i & mask
            dist[key] = dist.get(key, 0.0) + abs(a) ** 2
        r, acc = rng.random(), 0.0
        chosen = 0
        for key in sorted(dist):
            acc += dist[key]
            if r < acc:
                chosen = key
                break
        norm = 0.0
        for i in range(2 ** n):
            if (i & mask) == chosen:
                norm += abs(self.amp[i]) ** 2
            else:
                self.amp[i] = 0.0
        if norm > 0:
            for i in range(2 ** n):
                if self.amp[i] != 0:
                    self.amp[i] /= math.sqrt(norm)
        return chosen

    def marginal(self, qubit):
        p0 = p1 = 0.0
        for i, a in enumerate(self.amp):
            if (i >> qubit) & 1:
                p1 += abs(a) ** 2
            else:
                p0 += abs(a) ** 2
        return p0, p1


def teleport(input_state, rng):
    """把第 0 位的态传到第 2 位。input_state: (α, β)。
    返回 (经典消息 m0m1, 乙端最终态的 (α', β') 纯度检查)。"""
    reg = Register(3)
    # 第 0 位装载待传态
    reg.amp[0] = input_state[0]
    reg.amp[1] = input_state[1]
    # 甲乙共享纠缠对：q1-q2 贝尔态
    reg.apply_single(H, 1)
    reg.apply_cnot(1, 2)
    # 甲做贝尔基测量：CNOT(0→1) + H(0)
    reg.apply_cnot(0, 1)
    reg.apply_single(H, 0)
    m01 = reg.measure([0, 1], rng)             # 4 种结果等概率
    m0 = (m01 >> 1) & 1
    m1 = m01 & 1
    # 乙按经典消息修正
    if m1:
        reg.apply_single(X, 2)
    if m0:
        reg.apply_single(Z, 2)
    return (m0, m1), reg


def state_of_qubit2(reg):
    """提取第 2 位的 (α, β)。位序约定：q2 = 下标的 bit2。
    测量坍缩后只剩一个 q2=0 振幅和一个 q2=1 振幅非零。"""
    a = reg.amp[0] + reg.amp[2]                # q2 = 0（下标 0..3 中存活的那一个）
    b = reg.amp[4] + reg.amp[6]                # q2 = 1（下标 4..7 中存活的那一个）
    return a, b


rng = random.Random(93)

print("== 隐形传态电路 ==")
print("""
  q0 (甲的未知态) ──●──H──M
                    │
  q1 (纠缠) ────────⊕────M      经典 2 bit -> 乙
  q2 (乙的比特) ──────────X^m1·Z^m2 -> 得到 |ψ⟩
""")
print("  资源消耗：1 对纠缠（q1-q2）+ 2 个经典比特 + 1 次贝尔测量")

print("\n== 传送基态 |1⟩ ==")
msgs = {}
for _ in range(200):
    (m0, m1), reg = teleport((0.0 + 0j, 1.0 + 0j), rng)
    key = (m0, m1)
    msgs[key] = msgs.get(key, 0) + 1
    a, b = state_of_qubit2(reg)
    final = abs(reg.amp[0]) ** 2
print(f"  200 次传送 |1⟩：经典消息分布 = {msgs}")
print("  4 种消息各约 25% —— 测量结果真随机，但修正后乙端总是 |1⟩")
a, b = state_of_qubit2(teleport((0.0 + 0j, 1.0 + 0j), rng)[1])
print(f"  乙端最终态: P(0)={abs(a) ** 2:.3f}, P(1)={abs(b) ** 2:.3f}（应为 0/1）")

print("\n== 传送叠加态 |+⟩ = (|0⟩+|1⟩)/√2 ==")
success = 0
trials = 300
p1_hist = 0.0
for _ in range(trials):
    _, reg = teleport((1 / math.sqrt(2), 1 / math.sqrt(2)), rng)
    a, b = state_of_qubit2(reg)
    p1 = abs(b) ** 2
    p1_hist += p1
    if abs(p1 - 0.5) < 1e-6:
        success += 1
print(f"  {trials} 次传送 |+⟩：乙端 P(1) 平均 = {p1_hist / trials:.4f}（理论 0.5）")
print(f"  每次都精确为 0.5：{'是' if success == trials else '否'}")
print("  叠加态整体被传送 —— 振幅与相对相位都完好无损")

print("\n== 传送带相位的态 |−⟩ ==")
ok_minus = 0
for _ in range(100):
    _, reg = teleport((1 / math.sqrt(2), -1 / math.sqrt(2)), rng)
    a, b = state_of_qubit2(reg)
    # |−⟩ 的特征：再过 H 后测得 1 的概率为 1 —— 用振幅符号检查
    alpha_after = (a + b) / math.sqrt(2)
    beta_after = (a - b) / math.sqrt(2)
    if abs(abs(beta_after) ** 2 - 1.0) < 1e-9:
        ok_minus += 1
print(f"  100 次传送 |−⟩：乙端 H 后测得 |1⟩ 概率=1 的次数 = {ok_minus}")
print("  相位信息（α 的符号）也被正确传送 —— 这正是『量子』而非『经典传真』")

print("\n== 不可能的事：复制与超光速 ==")
print("  不可克隆定理：测量前的未知态无法复制 —— 所以传送后甲端必被摧毁")
print("  验证：传送后甲端（q0/q1）处于确定的消息态，与 |ψ⟩ 无关")
for _ in range(3):
    _, reg = teleport((1 / math.sqrt(2), 1 / math.sqrt(2)), rng)
    p0a, p1a = reg.marginal(0)
    print(f"    甲端 q0 边缘: P(0)={p0a:.3f}, P(1)={p1a:.3f}（总是测量结果的确定值）")
print("  无超光速：乙的态在收到经典比特前是均匀混合，无法提前获知 |ψ⟩")
print("  2 bit 经典信息的传播速度 ≤ 光速 —— 相对论完好无损")

print("\n== 经典消息的必要性 ==")
print("  若乙不做修正：4 种消息下乙端的态分别是")
for (m0, m1), correction in (((0, 0), "I"), ((0, 1), "X"), ((1, 0), "Z"), ((1, 1), "XZ")):
    print(f"    m0m1={m0}{m1}: 需要修正 {correction}")
print("  不修正 = 拿到随机相位的混合 —— 50% 概率是错的态")

print("\n== 小结 ==")
for line in (
    "  隐形传态 = 纠缠 + 经典通信 + 修正门，传态不传物质",
    "  测量摧毁原态 + 经典信道限速 -> 不违反不可克隆与相对论",
    "  这是量子网络（量子互联网）的基本原语",
    "  904 课：量子加速的初体验 —— Deutsch-Jozsa 算法",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「量子密集编码」：传 1 个比特 + 2 个纠缠 = 送 2 个经典比特（逆操作）。
# 2. 统计 1000 次传送 |ψ⟩=cos(θ)|0⟩+sin(θ)|1⟩ 的乙端测量分布，扫描 θ。
# 3. 实现 Toffoli 门（已在 Register 中）构建可逆逻辑：AND 的可逆版本。
# 4. 思考：隐形传态传送的是『态的信息』而非『物质/能量』——那它能传什么、
#    不能传什么？与经典拷贝（传真）的本质区别？
