# ===== 第904课：量子计算入门与电路模拟-Deutsch-Jozsa与量子并行 =====
# 知识点：
#   - DJ 问题：黑盒函数 f 要么常数要么平衡（半数 0 半数 1），判断是哪种
#   - 经典确定式：最坏要 2^(n-1)+1 次查询；量子：只需 1 次
#   - 相位技巧：|x⟩ → (-1)^f(x)|x⟩，把函数值编码进相位
#   - 干涉读出：全部叠加 → 相位编码 → H 门干涉 → 常数时 |0..0⟩ 概率=1
#   - 这是「量子并行 + 干涉」范式的最小示例（Grover/Shor 同根同源）
# 依赖：无（标准库）
import math

H = [[1 / math.sqrt(2), 1 / math.sqrt(2)],
     [1 / math.sqrt(2), -1 / math.sqrt(2)]]


class DJRegister:
    def __init__(self, n):
        self.n = n
        self.amp = [0.0 + 0j] * (2 ** n)
        self.amp[0] = 1.0 + 0j

    def apply_single_all(self, gate):
        for q in range(self.n):
            step = 1 << q
            for i in range(2 ** self.n):
                if i & step:
                    continue
                j = i | step
                a0, a1 = self.amp[i], self.amp[j]
                self.amp[i] = gate[0][0] * a0 + gate[0][1] * a1
                self.amp[j] = gate[1][0] * a0 + gate[1][1] * a1
        return self

    def apply_oracle(self, f):
        """相位 oracle：amp[i] *= (-1)^f(i)。"""
        for i in range(2 ** self.n):
            if f(i):
                self.amp[i] *= -1
        return self

    def probabilities(self):
        return [abs(a) ** 2 for a in self.amp]


def dj_classical(f, n):
    """经典确定式：见两个不同值→平衡；查满 2^(n-1)+1 个仍同值→常数（鸽笼）。"""
    seen_vals = set()
    for i in range(2 ** n):
        seen_vals.add(f(i))
        if len(seen_vals) == 2:
            return "balanced", i + 1
        if i + 1 > 2 ** (n - 1):
            return "constant", i + 1
    return ("constant" if len(seen_vals) == 1 else "balanced"), 2 ** n


def dj_quantum(f, n):
    reg = DJRegister(n)
    reg.apply_single_all(H)                 # 全体叠加
    reg.apply_oracle(f)                     # 相位编码（1 次调用）
    reg.apply_single_all(H)                 # 干涉
    p_zero = abs(reg.amp[0]) ** 2
    return ("constant" if p_zero > 0.5 else "balanced"), p_zero



print("== DJ 问题设定（n=3，8 个输入）==")
constant_f = lambda x: 1                                  # 常数：全 1
balanced_f = lambda x: (x.bit_count() % 2)                # 平衡：奇偶
balanced2 = lambda x: 1 if x < 4 else 0                   # 平衡：前半 0 后半 1
print("  常数函数: f(x)=1")
print("  平衡函数1: f(x)=x 的比特奇偶")
print("  平衡函数2: f(x)=1 if x<4 else 0")

print("\n== 经典确定式 vs 量子（1 次查询）==")
print(f"  {'函数':<12}{'经典查询数':>12}{'经典结论':>10}{'量子查询':>10}{'量子结论':>10}")
for label, f, kind in (("常数 f=1", constant_f, "constant"),
                       ("平衡 parity", balanced_f, "balanced"),
                       ("平衡 half", balanced2, "balanced")):
    _, qc = dj_classical(f, 3)
    kind_q, p0 = dj_quantum(f, 3)
    print(f"  {label:<12}{qc:>12}{kind:>10}{1:>10}{kind_q:>10}"
          f"  P(|000⟩)={p0:.3f}")
print("  经典最坏 2^(n-1)+1 = 5 次；量子 1 次查询 + 干涉直接读出")

print("\n== 量子电路逐步展开（平衡函数 parity, n=3）==")
reg = DJRegister(3)
reg.apply_single_all(H)
probs = reg.probabilities()
print(f"  ① 全体叠加: 均匀分布 1/8 = {probs[0]:.3f}")
reg.apply_oracle(balanced_f)
amps_after = reg.amp
signs = "".join("−" if a.real < 0 else "+" for a in amps_after)
print(f"  ② 相位编码: 振幅符号 = {signs}（一半负 —— f(x)=1 的分量翻转）")
reg.apply_single_all(H)
print(f"  ③ 干涉后: P(|000⟩) = {abs(reg.amp[0]) ** 2:.4f}, "
      f"其他分量振幅 ≈ 0")
print("  常数函数：无相位差 → 干涉相长回 |000⟩；平衡函数：相消归零")

print("\n== 常数函数的干涉 ==")
reg_c = DJRegister(3)
reg_c.apply_single_all(H)
reg_c.apply_oracle(constant_f)
reg_c.apply_single_all(H)
print(f"  f(x)=1: P(|000⟩) = {abs(reg_c.amp[0]) ** 2:.4f}")
reg_c0 = DJRegister(3)
reg_c0.apply_single_all(H)
reg_c0.apply_single_all(H)                       # f(x)=0：oracle 不翻转
print(f"  f(x)=0: P(|000⟩) = {abs(reg_c0.amp[0]) ** 2:.4f}")
print("  两种常数都 → P=1；平衡 → P=0 —— 一次查询区分，无统计误差")

print("\n== 量子并行性的正确理解 ==")
for line in (
    "  叠加确实『同时算所有 x』—— 但测量只能拿到一个随机结果",
    "  DJ 的关键是：f 的全局性质（常数/平衡）被编码成『一个可测量的全局量』",
    "  单看一个 f(x) 没有用；设计算法 = 设计『让性质干涉可见』的电路",
    "  Grover 把目标态振幅放大（905 课）、Shor 用周期性干涉 —— 同一范式",
):
    print("  -", line)

print("\n== n 扩展时的成本 ==")
print(f"  {'n':>4}{'经典最坏查询':>14}{'量子查询':>10}{'模拟器门成本':>14}")
for n in (1, 3, 5, 10):
    print(f"  {n:>4}{2 ** (n - 1) + 1:>14}{1:>10}{2 * 2 ** n:>14}")
print("  查询次数指数级优势；模拟器成本指数级增长 —— 量子硬件才是主角")

print("\n== 小结 ==")
for line in (
    "  相位 oracle + 全局干涉 = 量子算法的标准开头",
    "  DJ 展示『一次查询判定全局性质』—— 经典信息论下不可能",
    "  量子并行 ≠ 免费的指数加速；加速来自把答案编码进干涉模式",
    "  905 课：Grover 搜索 —— 干涉的第二次亮相",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Bernstein-Vazirani 算法：找隐藏串 s（f(x)=s·x mod 2），一次查询读出 s。
# 2. 让 oracle 支持「非均匀相位」（如 (-1)^f · 0.5 缩放），观察 DJ 何时失效。
# 3. 实现 n=10 的 DJ，统计模拟器运行时间，与经典 513 次查询对比。
# 4. 思考：DJ 在真实硬件上为何需要「理想 oracle」？噪声如何破坏干涉？
