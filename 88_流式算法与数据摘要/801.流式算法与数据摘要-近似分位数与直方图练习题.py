# ===== 第801课：流式算法与数据摘要-近似分位数与直方图 =====
# 知识点：
#   - 分位数查询：Q(0.5)=P50、Q(0.99)=P99；监控延迟的关键指标
#   - 精确方案需保存全部数据并排序，流式场景不可行
#   - 近似方案保证：返回的分位数估计 q̂ 与真值 q 满足 rank 差 ≤ εn
#   - 等宽直方图：实现最简单，但对重尾分布尾部精度差
#   - 对数桶直方图：桶边界按等比排列，改善重尾精度（Prometheus 常用）
#   - t-digest：自适应聚类，中心粗略、尾部精细，是 Elasticsearch 的方案
# 依赖：无（标准库）
import math
import random
import statistics


class HistogramSketch:
    """等宽直方图：把值域切成 buckets 个等宽桶。"""

    def __init__(self, lo, hi, buckets=20):
        self.lo, self.hi, self.n_buckets = lo, hi, buckets
        self.width = (hi - lo) / buckets
        self.counts = [0] * buckets
        self.total = 0

    def add(self, x):
        idx = int((x - self.lo) / self.width)
        idx = max(0, min(self.n_buckets - 1, idx))
        self.counts[idx] += 1
        self.total += 1

    def quantile(self, q):
        target = q * self.total
        acc = 0.0
        for i, c in enumerate(self.counts):
            if acc + c >= target:
                frac = (target - acc) / c if c else 0.5
                return self.lo + (i + frac) * self.width
            acc += c
        return self.hi

    def merge(self, other):
        for i, c in enumerate(other.counts):
            self.counts[i] += c
        self.total += other.total


class LogHistogram:
    """对数桶直方图：桶边界按等比数列排列，重尾分布精度大幅提升。"""

    def __init__(self, base=2.0, start_val=0.1):
        self.base, self.start_val = base, start_val
        self.counts = [0] * 40
        self.total = 0

    def _bucket(self, x):
        x = max(x, self.start_val)
        return min(39, int(math.log(x / self.start_val, self.base)))

    def add(self, x):
        self.counts[self._bucket(x)] += 1
        self.total += 1

    def quantile(self, q):
        target = q * self.total
        acc = 0.0
        for i, c in enumerate(self.counts):
            if acc + c >= target:
                frac = (target - acc) / c if c else 0.5
                lo = self.start_val * self.base ** i
                hi = lo * self.base
                return lo + (hi - lo) * frac
            acc += c
        return self.start_val * self.base ** 39

    def merge(self, other):
        for i, c in enumerate(other.counts):
            self.counts[i] += c
        self.total += other.total


def true_quantile(values, q):
    s = sorted(values)
    pos = (len(s)-1) * q
    lo, hi = int(pos), min(int(pos)+1, len(s)-1)
    return s[lo] + (s[hi]-s[lo]) * (pos-lo)


print("== 构造重尾分布（真实系统延迟特征）==")
rng = random.Random(7)
latencies = []
for _ in range(50000):
    u = rng.random()
    if u < 0.7:
        latencies.append(rng.uniform(5, 20))
    elif u < 0.95:
        latencies.append(rng.uniform(20, 80))
    else:
        latencies.append(max(0.1, rng.gauss(200, 80)))
print(f"  {len(latencies):,} 个延迟样本")

print("\n== 精确分位数 ==")
for q in (0.5, 0.9, 0.95, 0.99, 0.999):
    print(f"  P{int(q*1000):>03} = {true_quantile(latencies, q):>7.2f} ms")

print("\n== 等宽直方图近似 ==")
hist = HistogramSketch(0.1, 500, buckets=50)
for v in latencies: hist.add(v)
for q in (0.5, 0.9, 0.99, 0.999):
    est = hist.quantile(q)
    truth = true_quantile(latencies, q)
    print(f"  P{int(q*1000):>03}: 直方图={est:>7.2f} 精确={truth:>7.2f} "
          f"误差={est-truth:>+7.2f} ms")
print(f"  内存 = {50} 个计数器")
print("  P99 以上误差大：重尾集中在一两个桶里，线性插值失真")

print("\n== 对数桶直方图近似 ==")
lg = LogHistogram(base=2.0, start_val=0.1)
for v in latencies: lg.add(v)
for q in (0.5, 0.9, 0.99, 0.999):
    est = lg.quantile(q)
    truth = true_quantile(latencies, q)
    print(f"  P{int(q*1000):>03}: 对数桶={est:>7.2f} 精确={truth:>7.2f} "
          f"误差={est-truth:>+7.2f} ms")
print("  对数桶把高值域拆得更细，尾部精度显著优于等宽桶")

print("\n== 两种直方图的精度对比 ==")
print(f"  {'分位数':<10}{'等宽桶误差':>14}{'对数桶误差':>14}")
for q in (0.5, 0.9, 0.99, 0.999):
    truth = true_quantile(latencies, q)
    e1 = hist.quantile(q) - truth
    e2 = lg.quantile(q) - truth
    print(f"  P{int(q*1000):>03}{e1:>+14.2f}{e2:>+14.2f}")

print("\n== Q-Digest / t-digest（概念）==")
for line in (
    "  Q-Digest：树形聚合，可证明 ε 界，但实现复杂",
    "  t-digest：自适应聚类，中心粗略尾部精细，Elasticsearch 方案",
    "  HDR Histogram：对数桶 + 记录正确性保证",
    "  等宽桶最简单，对数桶改善重尾，t-digest 追求极致",
):
    print(" ", line)

print("\n== 应用 ==")
for line in [
    "  Prometheus 直方图：预设桶边界 + histogram_quantile()",
    "  Elasticsearch：t-digest 聚合",
    "  数据库：EXPLAIN ANALYZE 的延迟分位数",
    "  与第55章时间序列、第800课 EWMA 组合成完整监控方案",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 t-digest 简化版：按质心距离合并聚类，对比对数桶精度。
# 2. 给直方图加对数桶边界（1/2/4/8/...ms），验证重尾精度改善。
# 3. 对比 50 个等宽桶与 20 个对数桶在 P99.9 上的误差。
# 4. 思考：为什么 P99 比平均值更重要？
