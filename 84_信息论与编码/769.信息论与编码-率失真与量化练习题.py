# ===== 第769课：信息论与编码-率失真与量化 =====
# 知识点：
#   - 有损压缩：允许一定失真 D，换取更低码率 R；率失真函数 R(D) 给下界
#   - 高斯信源（方差 σ²，平方误差失真）：R(D) = ½log2(σ²/D)，0<D<=σ²
#   - 二值信源（汉明失真）：R(D) = 1 - H(D)
#   - 标量量化：把连续值映射到有限个重建电平；均匀量化步长 Δ，失真 ≈ Δ²/12
#   - Lloyd-Max 量化器：交替「最近邻分配」与「质心更新」，最小化 MSE（k-means 1D）
#   - 与第763课熵、第765课信道容量构成信息论三大定理
# 依赖：无（标准库）
import math
import random
import statistics


def h2(p):
    if p <= 0 or p >= 1: return 0.0
    return -p*math.log2(p) - (1-p)*math.log2(1-p)


def binary_rd(D):
    """二值等概信源 + 汉明失真的率失真函数。"""
    if D <= 0: return 1.0
    if D >= 0.5: return 0.0
    return 1 - h2(D)


def gaussian_rd(sigma2, D):
    """高斯信源 + 平方误差失真的率失真函数（bit/样本）。"""
    if D <= 0: return float("inf")
    if D >= sigma2: return 0.0
    return 0.5 * math.log2(sigma2 / D)


print("== 二值信源率失真 R(D) ==")
print(f"  {'D(允许误码率)':<16}{'R(D)=1-H(D)':<14}")
for D in (0.0, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5):
    print(f"  {D:<16.2f}{binary_rd(D):<14.4f}")
print("  D=0 需 1 bit（无损）；D=0.5 允许全猜错，0 bit 足够")

print("\n== 高斯信源率失真 R(D) = ½log2(σ²/D) ==")
sigma2 = 4.0
print(f"  方差 σ²={sigma2}")
print(f"  {'D(MSE)':<12}{'R(D) bit/样本':<16}{'相对下降'}")
for D in (4.0, 2.0, 1.0, 0.5, 0.25, 0.1, 0.01):
    r = gaussian_rd(sigma2, D)
    print(f"  {D:<12.2f}{r:<16.3f}{1-r/2:.0%}")
print("  D 每减半（失真降 3dB），码率只增加 0.5 bit/样本")

print("\n== 均匀量化：步长 Δ 与失真的关系 ==")
rng = random.Random(7)
signal = [rng.gauss(0, 2) for _ in range(10000)]
for bits in (1, 2, 3, 4, 6, 8):
    levels = 1 << bits
    lo, hi = min(signal), max(signal)
    delta = (hi - lo) / levels
    # 量化到电平中心
    q = [lo + (int((x-lo)/delta) + 0.5)*delta for x in signal]
    mse = statistics.fmean((a-b)**2 for a,b in zip(signal, q))
    snr = 10*math.log10(statistics.pvariance(signal)/mse) if mse else float("inf")
    print(f"  {bits} bit -> {levels:>3} 电平 步长={delta:.3f} "
          f"MSE={mse:.4f} SNR={snr:.1f}dB  理论 Δ²/12={delta**2/12:.4f}")
print("  每多 1 bit，SNR 约提升 6dB（量化经典结论）")

print("\n== Lloyd-Max 量化器（1D k-means）==")
def lloyd_max(values, k, iterations=50):
    lo, hi = min(values), max(values)
    levels = [lo + (i+0.5)*(hi-lo)/k for i in range(k)]
    for _ in range(iterations):
        groups = [[] for _ in range(k)]
        for x in values:
            j = min(range(k), key=lambda i: abs(x-levels[i]))
            groups[j].append(x)
        new = [statistics.fmean(g) if g else levels[i] for i, g in enumerate(groups)]
        if new == levels:
            break
        levels = new
    q = [min(levels, key=lambda c: abs(x-c)) for x in values]
    mse = statistics.fmean((a-b)**2 for a,b in zip(values,q))
    return levels, mse

for k in (2, 4, 8, 16):
    levels, mse = lloyd_max(signal, k)
    print(f"  k={k:>2}: 电平={[round(v,2) for v in levels]} MSE={mse:.4f}")
print("  非均匀电平会向高密度区聚集，MSE 低于同电平数的均匀量化")

print("\n== 熵编码量化索引（率失真联合） ==")
def quantize_indices(values, levels):
    return [min(range(len(levels)), key=lambda i: abs(x-levels[i])) for x in values]
def empirical_entropy(indices):
    from collections import Counter
    n = len(indices)
    return -sum((c/n)*math.log2(c/n) for c in Counter(indices).values())

for k in (2, 4, 8, 16):
    levels, mse = lloyd_max(signal, k)
    idx = quantize_indices(signal, levels)
    ent = empirical_entropy(idx)
    print(f"  k={k:>2}: MSE={mse:.4f} 索引熵={ent:.3f} bit/样本 "
          f"定长={math.log2(k):.1f} bit  熵编码可再省 {1-ent/math.log2(k):.0%}")
print("  量化决定失真，熵编码决定码率：两步分别优化再联合")

print("\n== 率失真 vs 信道容量（对偶）==")
for line in (
    "  信源编码：给定最大失真 D，求最小码率 R(D)",
    "  信道编码：给定信道容量 C，求可靠传输的最大速率 R<C",
    "  分离定理：先信源编码到 R(D)，再信道编码，只要 R(D)<C 即可端到端可靠",
    "  实际系统（视频通话）会联合考虑：网络差时主动增大 D 降码率",
):
    print(" ", line)

print("\n== 应用 ==")
for line in [
    "  JPEG：DCT + 量化表 + 哈夫曼，量化步长就是质量旋钮",
    "  MP3/AAC：心理声学模型决定各频带允许的失真",
    "  向量量化 / VQ-VAE：用码本索引表示高维向量",
    "  与第764课熵编码、第766课 LZ 组合成完整有损/无损管线",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 画出高斯信源 R(D) 曲线，标出 D 减半时 R 增加 0.5 bit。
# 2. 实现向量量化（2D k-means），对比标量量化的 MSE。
# 3. 给量化索引做哈夫曼编码，实测总 bit 数 vs 熵下界。
# 4. 思考：为什么视频编码在网络拥塞时优先调量化参数而不是换编码算法？
