# ===== 第902课：量子计算入门与电路模拟-纠缠与贝尔不等式 =====
# 知识点：
#   - 贝尔不等式：任何「局域隐变量」理论的关联强度 S ≤ 2
#   - 量子纠缠的关联 S 可达 2√2 ≈ 2.828（Tsirelson 界）—— 实验已证实
#   - 这不是近似误差，而是「世界比经典理论更怪」的数学证明
#   - 模拟验证：|Φ+⟩ 贝尔态 + 四组测量角度 -> 精确计算与蒙特卡洛对照
#   - CHSH 博弈：S = E(A,B) + E(A,B') + E(A',B) − E(A',B')
# 依赖：无（标准库）
import math
import random

H = [[1 / math.sqrt(2), 1 / math.sqrt(2)],
     [1 / math.sqrt(2), -1 / math.sqrt(2)]]


class PairState:
    """两比特纯态：直接存 4 个复振幅（|00⟩,|01⟩,|10⟩,|11⟩）。"""

    def __init__(self, amps):
        norm = math.sqrt(sum(abs(a) ** 2 for a in amps))
        self.amp = [a / norm for a in amps]

    def apply_single(self, gate, qubit):
        """把 2×2 门作用在 qubit（0 = 第一个比特）。"""
        out = [0j] * 4
        for i in range(4):
            bit = (i >> (1 - qubit)) & 1        # qubit 0 是高位
            j = i ^ (1 << (1 - qubit))
            if bit == 0:
                out[i] += gate[0][0] * self.amp[i] + gate[0][1] * self.amp[j]
            else:
                out[i] += gate[1][0] * self.amp[j] + gate[1][1] * self.amp[i]
        return PairState([a for a in out])

    def outcome_probs(self):
        """测量两个比特：返回 {(o0, o1): 概率}。"""
        probs = {}
        for i, a in enumerate(self.amp):
            if abs(a) > 1e-12:
                o0 = (i >> 1) & 1
                o1 = i & 1
                probs[(o0, o1)] = probs.get((o0, o1), 0) + abs(a) ** 2
        return probs

    def measure(self, rng):
        probs = self.outcome_probs()
        r = rng.random()
        acc = 0.0
        for key, p in sorted(probs.items()):
            acc += p
            if r < acc:
                return key
        return (1, 1)


def rot(angle):
    """实旋转矩阵（把测量基转到角度 angle 方向）。"""
    c, s = math.cos(angle), math.sin(angle)
    return [[c, s], [-s, c]]


def correlation(state, gate_a, gate_b, shots=None, rng=None):
    """E = P(同) − P(异)：测量结果 ±1 的乘积期望。"""
    applied = state.apply_single(gate_b, 1).apply_single(gate_a, 0)
    probs = applied.outcome_probs()
    if shots is None:
        same = sum(p for (o0, o1), p in probs.items() if o0 == o1)
        diff = sum(p for (o0, o1), p in probs.items() if o0 != o1)
        return same - diff
    win_same = 0
    for _ in range(shots):
        s2 = PairState(state.amp)
        s2 = s2.apply_single(gate_b, 1).apply_single(gate_a, 0)
        o = s2.measure(rng)
        win_same += 1 if o[0] == o[1] else -1
    return win_same / shots


print("== 贝尔态 |Φ+⟩ = (|00⟩ + |11⟩)/√2 ==")
bell = PairState([1, 0, 0, 1])
print(f"  概率分布: {bell.outcome_probs()}")
print("  两比特测量结果完全相同（00 或 11，各 50%）")

print("\n== 同基测量：完美相关 ==")
E_z = correlation(bell, [[1, 0], [0, -1]], [[1, 0], [0, -1]])
print(f"  E(Z,Z) = {E_z:.4f}（同向基总是 +1 —— 纠缠的『心灵感应』）")

print("\n== CHSH 四组角度 ==")
# 经典最优配置的量子角度：A=0, A'=π/4, B=π/8, B'=−π/8
angles = {
    "A": 0.0, "A'": math.pi / 4,
    "B": math.pi / 8, "B'": -math.pi / 8,
}
pairs = [("A", "B", +1), ("A", "B'", +1), ("A'", "B", +1), ("A'", "B'", -1)]
S = 0.0
print(f"  {'测量对':<12}{'E(关联)':>10}{'系数':>6}")
for a_name, b_name, sign in pairs:
    ga, gb = rot(angles[a_name]), rot(angles[b_name])
    e = correlation(bell, ga, gb)
    S += sign * e
    print(f"  E({a_name},{b_name}): {e:>10.4f}{sign:>+6}")
print(f"  CHSH S = {S:.4f}")
print(f"  经典局域理论上限 = 2.0000")
print(f"  量子可达上限 = 2√2 = {2 * math.sqrt(2):.4f}（Tsirelson 界）")
print(f"  本例 {'超过经典上限 ✓' if S > 2 + 1e-9 else '未超过'} —— 纠缠强于任何局域隐变量")

print("\n== 经典局域理论的极限（枚举全部 16 种确定性策略）==")
best, best_cfg = -9.0, None
for a0 in (1, -1):
    for a1 in (1, -1):
        for b0 in (1, -1):
            for b1 in (1, -1):
                S_c = a0 * b0 + a0 * b1 + a1 * b0 - a1 * b1
                if S_c > best:
                    best, best_cfg = S_c, (a0, a1, b0, b1)
print(f"  A 对两个问题的答案 {best_cfg[:2]}，B 的答案 {best_cfg[2:]}")
print(f"  确定性策略最大 S = {best:.4f}")
print("  随机混合策略只是确定性策略的加权平均 -> S ≤ 2 对一切经典局域理论成立")

print("\n== 蒙特卡洛对照（20000 shots）==")
rng = random.Random(92)
S_mc = 0.0
for a_name, b_name, sign in pairs:
    ga, gb = rot(angles[a_name]), rot(angles[b_name])
    e_mc = correlation(bell, ga, gb, shots=20000, rng=rng)
    S_mc += sign * e_mc
print(f"  采样 S = {S_mc:.4f}（精确 {S:.4f}，误差 {abs(S_mc - S):.4f}）")
print("  真实实验（Aspect 1982、2015 无漏洞实验）就是这个流程的物理版")

print("\n== CHSH 博弈的胜负率 ==")
print("  规则：裁判随机发测量基 A/A'、B/B'，双方不打商量回答 ±1，")
print("  目标 a⊕b = 判定函数（多数情形成立者胜）")
print(f"  经典策略胜率上限 = {0.5 + best / 8:.0%}（S=2 时 p = 1/2 + S/8 = 75%）")
print(f"  量子策略胜率     = {0.5 + S / 8:.1%}（S=2√2 时 ≈ 85.4%）")
print("  非局域关联被换算成可量化的信息优势 —— 量子密码学的根基")

print("\n== 小结 ==")
for line in (
    "  贝尔不等式把『哲学争论』变成『可测量的实验判据』",
    "  模拟器的价值：不用实验室就能复现 2√2 的非局域关联",
    "  纠缠是资源：CHSH 博弈、量子密钥分发、隐形传态都靠它",
    "  903 课：纠缠的应用之一 —— 量子隐形传态",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 |Ψ−⟩ = (|01⟩−|10⟩)/√2 的 CHSH，验证 S 同样为 2√2（符号差异）。
# 2. 扫描测量角度 b ∈ [0, π/2]，画出 E(b) 的余弦曲线（文本图）。
# 3. 实现「无漏洞实验」的模拟：加入探测器效率 <100%，观察 S 如何被稀释到 2 以下。
# 4. 思考：贝尔不等式的『不等』到底排除了哪些理论？「非局域」与「无隐变量」
#    是同一回事吗？
