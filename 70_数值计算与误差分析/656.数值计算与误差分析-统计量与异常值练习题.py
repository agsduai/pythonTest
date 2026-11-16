# ===== 第656课：数值计算与误差分析-统计量与异常值 =====
# 知识点：
#   - 集中趋势：均值（受异常值影响）、中位数（稳健）、截尾均值（折中）
#   - 离散程度：方差/标准差、MAD（中位绝对偏差，更稳健）、IQR
#   - 稳健统计：breakdown point，中位数能容忍近 50% 异常值，均值 0%
#   - 异常值检测：3σ 法则（本身会被异常值污染）、IQR 箱线法、z-score vs 修正 z-score
#   - 方差计算用「两遍法」或 Welford 在线算法，避免 E[x²]-E[x]² 的抵消误差
#   - statistics 模块提供 mean/median/pstdev/quantiles；本例手写以展示原理
# 依赖：无（标准库）
import math
import statistics

data = [12.1, 11.8, 12.3, 12.0, 11.9, 12.2, 12.4, 11.7, 12.1, 11.95, 999.0]
clean = data[:-1]

print("== 均值 vs 中位数（一个异常值）==")
print(f"  数据: {data}")
print(f"  含异常值均值   = {statistics.mean(data):.3f}")
print(f"  去掉异常值均值 = {statistics.mean(clean):.3f}")
print(f"  含异常值中位数 = {statistics.median(data):.3f}")
print(f"  去掉异常值中位数 = {statistics.median(clean):.3f}")
print("  均值被拉高近 100 倍，中位数几乎不动 -> 稳健性差异")

print("\n== 截尾均值 ==")
def trimmed_mean(xs, ratio=0.1):
    s = sorted(xs)
    k = int(len(s) * ratio)
    return statistics.mean(s[k:len(s) - k]) if len(s) - 2 * k > 0 else statistics.mean(s)

for r in (0.0, 0.1, 0.2, 0.3):
    print(f"  截尾 {r:.0%}: {trimmed_mean(data, r):.3f}")

print("\n== 离散程度：标准差 vs MAD ==")
def mad(xs):
    med = statistics.median(xs)
    return statistics.median([abs(x - med) for x in xs])

print(f"  含异常值标准差 = {statistics.pstdev(data):.3f}")
print(f"  干净数据标准差 = {statistics.pstdev(clean):.3f}")
print(f"  含异常值 MAD   = {mad(data):.3f}")
print(f"  干净数据 MAD   = {mad(clean):.3f}")
print("  标准差被污染，MAD 保持稳定")

print("\n== 三种方差算法（数值稳定性）==")
def var_two_pass(xs):
    n = len(xs)
    m = sum(xs) / n
    return sum((x - m) ** 2 for x in xs) / n

def var_naive(xs):
    n = len(xs)
    return sum(x * x for x in xs) / n - (sum(xs) / n) ** 2

def welford(xs):
    n, mean, m2 = 0, 0.0, 0.0
    for x in xs:
        n += 1
        delta = x - mean
        mean += delta / n
        m2 += delta * (x - mean)
    return m2 / n, mean

shifted = [1e9 + x for x in clean]     # 大基数 + 小波动
print("  数据 = 1e9 + 小波动（考验抵消误差）")
print(f"  两遍法     : {var_two_pass(shifted):.9f}")
print(f"  Welford    : {welford(shifted)[0]:.9f}")
print(f"  E[x²]-E[x]²: {var_naive(shifted):.9f}  ← 大数相减，有效位丢失")
print(f"  参考(干净值): {var_two_pass(clean):.9f}")
print(f"  Welford 均值={welford(shifted)[1]:.6f}（在线算法，无需存全部数据）")

print("\n== IQR 与箱线法 ==")
def quantile(xs, q):
    s = sorted(xs)
    pos = (len(s) - 1) * q
    lo, hi = int(pos), min(int(pos) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)

q1, q3 = quantile(data, 0.25), quantile(data, 0.75)
iqr = q3 - q1
low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
print(f"  Q1={q1:.3f} Q3={q3:.3f} IQR={iqr:.3f}")
print(f"  正常范围 [{low:.3f}, {high:.3f}]")
print("  IQR 判为异常:", [x for x in data if x < low or x > high])

print("\n== 3σ 法则的悖论 ==")
mu, sd = statistics.mean(data), statistics.pstdev(data)
out_3s = [x for x in data if abs(x - mu) > 3 * sd]
print(f"  mean={mu:.2f} std={sd:.2f} -> 3σ 判为异常: {out_3s}")
print("  异常值把 std 撑大，反而把自己藏起来了（masking 效应）")

print("\n== 修正 z-score（基于 MAD）==")
def modified_z(xs):
    med = statistics.median(xs)
    m = mad(xs)
    if m == 0:
        return [0.0] * len(xs)
    return [0.6745 * (x - med) / m for x in xs]

zs = modified_z(data)
print("  各点修正 z 值:", [round(z, 2) for z in zs])
print("  |z| > 3.5 的异常:", [x for x, z in zip(data, zs) if abs(z) > 3.5])

print("\n== breakdown point ==")
for name, point in (("均值", "0%（一个无穷大就能带偏）"),
                    ("中位数", "约 50%"),
                    ("截尾均值", "约等于截尾比例")):
    print(f"  {name:<8}: {point}")

print("\n== 工程要点 ==")
for line in [
    "  报表先出中位数 + IQR，再出均值 + 标准差，避免单一指标误导",
    "  在线/流式数据用 Welford，内存 O(1) 且数值稳定",
    "  检测前先画分布；多峰数据别硬套 3σ",
    "  异常不等于错误：先判断是录入错误还是真实长尾，再决定剔除",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Welford 的合并版，支持把两批数据的统计量合并成全局方差。
# 2. 用 IQR 与修正 z-score 分别检测同一份含 3 个异常值的数据并对比。
# 3. 给截尾均值增加非对称截尾（只截上尾），用于长尾收入数据。
# 4. 思考：为什么「先剔除异常值再算标准差」容易造成 masking？
