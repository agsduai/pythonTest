# ===== 第905课：量子计算入门与电路模拟-Grover搜索 =====
# 知识点：
#   - 经典无序搜索 N 项需要 O(N) 次；Grover 用量子：O(√N) 次调用
#   - 核心循环：oracle（目标相位翻转）+ 扩散算子（绕均值翻转）
#   - 每轮把目标态振幅向均值方向「旋转」θ≈2/√N → 累积放大
#   - 最优轮数 ≈ π/4·√N：轮数过了振幅会再衰减（不是越多越好）
#   - Grover 是「二次加速」，可叠加于任何可编码为判定的问题
# 依赖：无（标准库）
import math
import random

H = [[1 / math.sqrt(2), 1 / math.sqrt(2)],
     [1 / math.sqrt(2), -1 / math.sqrt(2)]]


class GroverRegister:
    def __init__(self, n):
        self.n = n
        self.N = 2 ** n
        self.amp = [1.0 / math.sqrt(self.N) + 0j] * self.N   # 均匀叠加

    def oracle(self, targets):
        for t in targets:
            self.amp[t] *= -1
        return self

    def diffuse(self):
        """绕均值翻转：amp = 2·mean − amp。"""
        mean = sum(self.amp) / self.N
        for i in range(self.N):
            self.amp[i] = 2 * mean - self.amp[i]
        return self

    def success_prob(self, targets):
        return sum(abs(self.amp[t]) ** 2 for t in targets)

    def measure(self, rng):
        r, acc = rng.random(), 0.0
        probs = [abs(a) ** 2 for a in self.amp]
        for i, p in enumerate(probs):
            acc += p
            if r < acc:
                return i
        return self.N - 1


def grover_iterations(n, targets):
    return max(1, int(round(math.pi / 4 * math.sqrt(2 ** n / len(targets)))))


def run_grover(n, targets, iterations, rng=None):
    reg = GroverRegister(n)
    prob_hist = [reg.success_prob(targets)]
    for _ in range(iterations):
        reg.oracle(targets)
        reg.diffuse()
        prob_hist.append(reg.success_prob(targets))
    if rng is None:
        return reg, prob_hist
    outcome = reg.measure(rng)
    return outcome, prob_hist


rng = random.Random(95)

print("== 场景：在 16 个盒子里找 1 个正确的（n=4）==")
n, target = 4, 5
optimal = grover_iterations(n, [target])
print(f"  目标 = 编号 {target}，理论最优轮数 ≈ π/4·√16 = {math.pi / 4 * 4:.3f} -> {optimal} 轮")

print("\n== 振幅放大曲线 ==")
reg_full, prob_hist = run_grover(n, [target], 8)
print(f"  {'迭代':>4}{'目标态概率':>12}  可视化")
for it, p in enumerate(prob_hist):
    print(f"  {it:>4}{p:>12.4f}  {'#' * int(p * 50)}")
print("  概率先升后降：θ = 2·arcsin(1/√N) 每轮转动，过冲后再转过头")
print(f"  经典均匀猜测成功率 = 1/16 = {1 / 16:.4f}；Grover 在 {optimal} 轮达到峰值")

print("\n== 峰值时刻测量 ==")
reg_peak, _ = run_grover(n, [target], optimal)
print(f"  {optimal} 轮后目标态概率 = {reg_peak.success_prob([target]):.4f}")
hits = 0
shots = 1000
for _ in range(shots):
    outcome, _ = run_grover(n, [target], optimal, rng)
    hits += (outcome == target)
print(f"  1000 次完整 Grover 测量: 命中 {hits} 次（{hits / shots:.1%}）")
print(f"  经典 1000 次均匀猜测: 命中约 {shots / 16:.0f} 次")

print("\n== 未达到最优轮数 ==")
for it in (1, 2, 3, 4, 5, 6):
    hit = 0
    for _ in range(500):
        outcome, _ = run_grover(n, [target], it, rng)
        hit += (outcome == target)
    print(f"  {it} 轮: 实测命中率 {hit / 500:.1%}（理论 {prob_hist[it]:.1%}）")

print("\n== 多目标情况 ==")
for k in (1, 2, 4, 8):
    targets = list(range(k))
    it_opt = max(1, int(round(math.pi / 4 * math.sqrt(2 ** n / k))))
    reg_k, ph = run_grover(n, targets, it_opt)
    print(f"  目标数 {k}: 最优轮数 {it_opt}, 峰值概率 {ph[-1]:.4f}")
print("  目标越多，√(N/k) 越小 —— 轮数越少（也更容易过冲，需精确控制）")

print("\n== oracle 的真实成本 ==")
print("  Grover 的 O(√N) 只数 oracle 调用次数；oracle 本身的代价取决于问题")
print("  例：SAT 编码成可逆电路时，oracle 可能远贵于搜索本身")
print("  所以 Grover 的实战收益 = √加速 × oracle 成本的权衡")
print("  对 128 位密钥穷举：√128bit ≈ 2^64 次 —— 安全强度减半但仍可行（理论）")

print("\n== 模拟器成本 ==")
print(f"  {'n':>3}{'N=2^n':>8}{'每轮成本':>10}{'最优轮数':>10}")
for n2 in (4, 8, 12, 16):
    it2 = max(1, int(round(math.pi / 4 * math.sqrt(2 ** n2))))
    print(f"  {n2:>3}{2 ** n2:>8}{2 ** n2:>10}{it2:>10}")
print("  模拟器每轮 O(2^n)：n=16 已是百万级复数 —— 与真实硬件互补")

print("\n== 小结 ==")
for line in (
    "  Grover = oracle 相位翻转 + 均值扩散的振幅放大，几何直觉极清晰",
    "  最优轮数 π/4·√N 是精确公式；盲目多轮会过冲",
    "  二次加速 + oracle 开销 = 实际收益，要按问题具体分析",
    "  906 课：把本章组件拼成完整的迷你量子引擎",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「带相位误差」的 oracle（翻转幅度 0.9 而非 1），观察峰值概率下降。
# 2. 实现「部分扩散」：扩散角减半，推导新的最优轮数并验证。
# 3. 用 Grover 解一个 3 比特 SAT 问题（oracle = 满足子句的赋值相位翻转）。
# 4. 思考：为什么 Grover 最优轮数是整数舍入的 π/4·√N？连续时间版本
#    （模拟 Grover / 绝热量子计算）如何避免过冲？
