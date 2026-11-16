# ===== 第681课：随机模拟与蒙特卡洛-A/B测试与假设检验模拟 =====
# 知识点：
#   - 假设检验：H0（无差异） vs H1（有差异）；p 值 = P(观察到这么极端 | H0 真)
#   - 置换检验 permutation test：打乱标签重算统计量，不依赖分布假设
#   - 第 I 类错误 α（误报）、第 II 类错误 β（漏报）、功效 power = 1-β
#   - 功效分析：给定效应量、α、期望 power，反推所需样本量
#   - 多重比较：检验次数越多，至少一次误报的概率 1-(1-α)^m 越高
#   - 用蒙特卡洛模拟验证解析公式，并展示「peeking（提前看结果）」的危害
# 依赖：无（标准库）
import math
import random
import statistics

print("== 置换检验：两组均值差是否显著 ==")
A = [12.1, 11.8, 12.3, 12.0, 11.9, 12.2, 12.4, 11.7]
B = [12.6, 12.5, 12.8, 12.4, 12.9, 12.7, 12.55, 12.65]
obs = statistics.fmean(B) - statistics.fmean(A)
pooled = A + B
n = len(A)

def perm_test(pooled, n, B=20000, seed=0):
    r = random.Random(seed)
    count = 0
    diffs = []
    for _ in range(B):
        r.shuffle(pooled)
        d = statistics.fmean(pooled[n:]) - statistics.fmean(pooled[:n])
        diffs.append(d)
        if abs(d) >= abs(obs) - 1e-12:
            count += 1
    return (count + 1) / (B + 1), diffs

p, diffs = perm_test(list(pooled), n, B=10000, seed=5)
print(f"  A 均值={statistics.fmean(A):.4f}  B 均值={statistics.fmean(B):.4f}")
print(f"  观测差={obs:.4f}  置换检验 p={p:.5f}")
print(f"  置换分布: 均值={statistics.fmean(diffs):.4f} 标准差={statistics.pstdev(diffs):.4f}")
print(f"  α=0.05 结论: {'拒绝 H0（有显著差异）' if p < 0.05 else '不拒绝 H0'}")

print("\n== 解析 t 检验近似（对照） ==")
def welch_t(a, b):
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    va, vb = statistics.variance(a), statistics.variance(b)
    na, nb = len(a), len(b)
    se = math.sqrt(va / na + vb / nb)
    return (mb - ma) / se

t = welch_t(A, B)
print(f"  Welch t ≈ {t:.3f}（|t|>2 通常对应 p<0.05）")

print("\n== 第 I 类错误：H0 为真时误报率应 ≈ α ==")
def simulate_null(alpha=0.05, n=50, trials=3000, seed=1):
    r = random.Random(seed)
    false_positives = 0
    for _ in range(trials):
        x = [r.gauss(0, 1) for _ in range(n)]
        y = [r.gauss(0, 1) for _ in range(n)]
        # 用 z 近似检验
        d = statistics.fmean(y) - statistics.fmean(x)
        se = math.sqrt(statistics.variance(x)/n + statistics.variance(y)/n)
        if abs(d / se) > 1.96:
            false_positives += 1
    return false_positives / trials

print(f"  3000 次 H0 为真实验的误报率 = {simulate_null():.4f}（理论 0.05）")

print("\n== 功效：真实效应量越大 / 样本越大，检出率越高 ==")
def simulate_power(effect, n, alpha=0.05, trials=2000, seed=2):
    r = random.Random(seed)
    hits = 0
    for _ in range(trials):
        x = [r.gauss(0, 1) for _ in range(n)]
        y = [r.gauss(effect, 1) for _ in range(n)]
        d = statistics.fmean(y) - statistics.fmean(x)
        se = math.sqrt(statistics.variance(x)/n + statistics.variance(y)/n)
        if abs(d / se) > 1.96:
            hits += 1
    return hits / trials

print(f"  {'效应量':<10}{'n=20':<12}{'n=50':<12}{'n=100':<12}")
for eff in (0.0, 0.3, 0.5, 0.8):
    print(f"  {eff:<10}" + "".join(f"{simulate_power(eff, n):<12.3f}"
                                   for n in (20, 50, 100)))

print("\n== 样本量反推（模拟版）==")
def required_n(effect, target_power=0.8, alpha=0.05):
    for n in range(10, 501, 10):
        if simulate_power(effect, n, alpha, trials=500, seed=9) >= target_power:
            return n
    return None
for eff in (0.3, 0.5, 0.8):
    print(f"  effect={eff} 达到 power=0.8 约需每组 n≈{required_n(eff)}")
print("  效应量减半，所需样本约变 4 倍（n ∝ 1/effect²）")

print("\n== 多重比较：检验越多，误报越多 ==")
for m in (1, 5, 10, 20, 50):
    fam = 1 - (1 - 0.05) ** m
    print(f"  检验 {m:>2} 次, 至少一次误报概率={fam:.3f}")
print("  校正：Bonferroni 用 α/m，或控制 FDR（Benjamini-Hochberg）")

print("\n== 提前窥探（peeking）的危害 ==")
def peeking(trials=2000, seed=4):
    r = random.Random(seed)
    fp = 0
    for _ in range(trials):
        seen_a, seen_b = [], []
        for step in range(1, 11):          # 每来 10 个样本看一次
            seen_a += [r.gauss(0, 1) for _ in range(10)]
            seen_b += [r.gauss(0, 1) for _ in range(10)]
            d = statistics.fmean(seen_b) - statistics.fmean(seen_a)
            se = math.sqrt(statistics.variance(seen_a)/len(seen_a) +
                           statistics.variance(seen_b)/len(seen_b))
            if abs(d / se) > 1.96:        # 一见显著就停
                fp += 1
                break
    return fp / trials

print(f"  H0 为真、最多窥探 10 次 -> 误报率 ≈ {peeking():.3f}（远超 0.05）")
print("  正确做法：预先固定样本量，或用序贯检验（alpha spending）")

print("\n== 实验设计清单 ==")
for line in [
    "  先定指标、效应量、α 与 power，再算样本量，别边跑边加量",
    "  随机分流要可复现（记录 seed），并做 SRM 样本比例校验",
    "  多重指标/多组别必须做多重比较校正",
    "  报告效应量与置信区间，不要只报 p 值",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Benjamini-Hochberg FDR 校正，作用于一组 p 值。
# 2. 用模拟比较「固定样本量」与「序贯检验」的误报率与平均样本量。
# 3. 对比例指标（转化率）做置换检验，而不是均值 t 检验。
# 4. 思考：为什么「跑到显著就停」会把误报率抬高到远超 α？
