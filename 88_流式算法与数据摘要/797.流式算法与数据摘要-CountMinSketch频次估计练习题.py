# ===== 第797课：流式算法与数据摘要-Count-Min Sketch频次估计 =====
# 知识点：
#   - Count-Min Sketch (CMS)：d 行 × w 列的二维计数器数组 + d 个独立哈希
#   - 插入：每行把对应计数器 +1；查询：取 d 个计数器的最小值
#   - 保证：估计值 ≥ 真频率（只高不低）；误差 ≤ ε·N 以概率 1-δ
#   - 参数：w = ⌈e/ε⌉ 列，d = ⌈ln(1/δ)⌉ 行；N 为流长度
#   - 天然支持「可合并」：两个 sketch 逐格相加即合并，适合分布式聚合
#   - 局限：不能删除（需 Count-Min with decay / conservative update 变体）
# 依赖：无（标准库）
import hashlib
import math
import random


def _hash(s, seed):
    return int.from_bytes(hashlib.md5(f"{seed}:{s}".encode()).digest()[:8], "big")


class CountMinSketch:
    def __init__(self, epsilon=0.001, delta=0.01):
        self.w = math.ceil(math.e / epsilon)          # 列数
        self.d = math.ceil(math.log(1/delta))         # 行数
        self.table = [[0]*self.w for _ in range(self.d)]
        self.seeds = [i+1 for i in range(self.d)]
        self.total = 0
        self._name_to_row_cache = None

    def _cols(self, item):
        return [_hash(item, s) % self.w for s in self.seeds]

    def add(self, item, count=1):
        self.total += count
        for row, col in zip(self.table, self._cols(item)):
            row[col] += count

    def estimate(self, item):
        return min(row[c] for row, c in zip(self.table, self._cols(item)))

    def merge(self, other):
        """sketch 可合并：分布式聚合时逐格相加。"""
        if (self.w, self.d) != (other.w, other.d):
            raise ValueError("参数不同无法合并")
        self.total += other.total
        for r1, r2 in zip(self.table, other.table):
            for i in range(self.w):
                r1[i] += r2[i]

    def heavy_hitters(self, candidates, k=5):
        return sorted(((c, self.estimate(c)) for c in candidates),
                      key=lambda x: -x[1])[:k]


def make_stream(n, distinct, seed=0):
    rng = random.Random(seed)
    keys = [f"ip{i}" for i in range(distinct)]
    weights = [1/(i+1) for i in range(distinct)]
    s = sum(weights)
    probs = [w/s for w in weights]
    for _ in range(n):
        u, acc, chosen = rng.random(), 0.0, keys[0]
        for k, p in zip(keys, probs):
            acc += p
            if u < acc:
                chosen = k; break
        yield chosen


print("== CMS 参数与内存 ==")
N, D = 200000, 3000
cms = CountMinSketch(epsilon=0.001, delta=0.01)
print(f"  宽 w={cms.w} 列 × 深 d={cms.d} 行 = {cms.w*cms.d} 个计数器")
print(f"  每个 8 字节计数器 ≈ {cms.w*cms.d*8/1024:.0f} KB（固定，与流长度无关）")
print(f"  误差界: 估计超出真值 ≤ ε·N = {0.001*N:,.0f}，概率 ≥ 99%")

print("\n== 全流插入与查询 ==")
true_counts = {}
for x in make_stream(N, D, seed=7):
    cms.add(x)
    true_counts[x] = true_counts.get(x, 0) + 1

print(f"  处理 {N:,} 个元素")
for key in ("ip0", "ip1", "ip2", "ip50", "ip500"):
    truth = true_counts.get(key, 0)
    est = cms.estimate(key)
    err = est - truth
    bound = 0.001 * N
    print(f"  {key:<8}: 真值={truth:>6} 估计={est:>6} 误差=+{err:>5} "
          f"界内={err <= bound}")

print("\n== 只高不低（单向误差）的性质 ==")
violations = sum(1 for k in true_counts if cms.estimate(k) < true_counts[k])
print(f"  检查全部 {len(true_counts)} 个键: 低估次数={violations}（理论应为 0）")
print("  CMS 的保证是「单向」的：估计值永远 ≥ 真值")

print("\n== ε 对精度的影响 ==")
for eps in (0.01, 0.005, 0.002, 0.001, 0.0005):
    s = CountMinSketch(epsilon=eps, delta=0.01)
    for x in make_stream(N, D, seed=7):
        s.add(x)
    errs = [s.estimate(k) - true_counts[k] for k in true_counts]
    avg_err = sum(errs) / len(errs)
    print(f"  ε={eps:<7}: 宽={s.w:>4} 列, 平均误差=+{avg_err:>8.1f} "
          f"(界 {eps*N:>8.0f})")
print("  ε 减半，列数翻倍，误差约减半——空间换精度的线性权衡")

print("\n== 可合并性：分布式聚合 ==")
c1, c2 = CountMinSketch(0.001, 0.01), CountMinSketch(0.001, 0.01)
half1 = list(make_stream(N//2, D, seed=7))
half2 = list(make_stream(N//2, D, seed=8))
for x in half1: c1.add(x)
for x in half2: c2.add(x)
c1.merge(c2)
truth_merged = {}
for x in half1 + half2: truth_merged[x] = truth_merged.get(x, 0) + 1
errs = [c1.estimate(k) - truth_merged[k] for k in truth_merged]
print(f"  两台机器各处理一半，merge 后估计误差平均=+{sum(errs)/len(errs):.1f}")
print("  这就是分布式监控（如 Prometheus 分片）的聚合原理")

print("\n== Top-K 应用 ==")
top = cms.heavy_hitters(list(true_counts), k=5)
real_top = sorted(true_counts.items(), key=lambda x: -x[1])[:5]
print("  CMS 估计 Top-5:", [(k, v) for k, v in top])
print("  真实 Top-5     :", real_top)
print("  CMS 只能估计「给定候选集」的频次；无候选集时用 Misra-Gries（第799课）")

print("\n== 工程要点 ==")
for line in [
    "  计数器用 uint32/uint64 会溢出，大流量要考虑饱和或用更多位",
    "  conservative update：只把「比当前最小值小」的行 +1，误差更小",
    "  删除流需要「减法 sketch」或按时间分片再过期",
    "  生产实现：Redis 的 CMS 模块、Alibaba 的 CMS 库、Flink 的 sketch 算子",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 conservative update 变体，量化同等内存下误差改善多少。
# 2. 实现「减法 sketch」支持撤销操作，并讨论误差如何变化。
# 3. 对比 CMS 与精确 Counter 在 1000 万元素下的内存与耗时。
# 4. 思考：为什么 CMS 的估计永远只高不低？哈希冲突的方向决定了什么？
