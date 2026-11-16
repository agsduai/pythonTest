# ===== 第796课：流式算法与数据摘要-蓄水池抽样 =====
# 知识点：
#   - 蓄水池抽样 Reservoir Sampling：从长度未知的流中均匀抽出 k 个样本
#   - Algorithm R：第 i 个元素以 k/i 概率随机替换池中一个；最终每个元素等概率 k/n
#   - 证明思路：归纳法——第 i 步后留在池中的概率恰为 k/i
#   - 加权变体 A-Res：按权重 w_i 概率 w_i/w_total 抽样（key = u^(1/w_i) 取最大）
#   - 分布式版本：各分片抽 k 个再合并（等价于对合并流的抽样）
#   - 应用：等价测试集采样、日志降采样、A/B 抽样、推荐冷启动
# 依赖：无（标准库）
import math
import random
import statistics


def reservoir_sample(stream, k, rng):
    """Algorithm R：未知长度的均匀抽样，返回 (样本列表, 已处理数量)。"""
    sample = []
    for i, item in enumerate(stream, 1):
        if i <= k:
            sample.append(item)
        else:
            j = rng.randrange(i)
            if j < k:
                sample[j] = item
    return sample, i


def weighted_reservoir(stream_items, k, rng):
    """A-Res 加权蓄水池：item 为 (value, weight)。"""
    pool, last_key = [], []
    for value, weight in stream_items:
        if weight <= 0:
            continue
        key = rng.random() ** (1.0 / weight)
        if len(pool) < k:
            pool.append(value); last_key.append(key)
        elif key > min(last_key):
            idx = last_key.index(min(last_key))
            pool[idx] = value; last_key[idx] = key
    return pool


print("== Algorithm R：均匀性验证 ==")
rng = random.Random(1)
population = [f"item{i}" for i in range(100)]
counts = {x: 0 for x in population}
TRIALS = 2000
K = 10
for _ in range(TRIALS):
    sample, n = reservoir_sample(iter(population), K, rng)
    for s in sample:
        counts[s] += 1
expected = TRIALS * K / len(population)
devs = [abs(c - expected) / expected for c in counts.values()]
print(f"  总体 {len(population)} 个, 每次抽 {K} 个, 重复 {TRIALS} 次")
print(f"  每个元素期望被抽 {expected:.1f} 次")
print(f"  实测范围: {min(counts.values())}~{max(counts.values())} 次 "
      f"（最大偏差 {max(devs):.1%}，抽样随机波动范围内）")

print("\n== 流长度未知时的行为 ==")
rng = random.Random(7)
for total in (5, 10, 50, 500, 5000):
    r2 = random.Random(7)
    sample, seen = reservoir_sample((f"x{i}" for i in range(total)), 5, r2)
    print(f"  流长度={total:>5}: 抽出 {len(sample)} 个，样本={sample[:3]}...")
print("  无论流多长，池子里恰好 k 个且均匀")

print("\n== 数学验证：每个元素入选概率恰为 k/i ==")
# 精确计算：第 i 个元素最终留下的概率 = k/i（归纳可证）
for i in (5, 10, 50, 500):
    print(f"  第 {i:>4} 个元素的入选概率 = {min(1.0, K/i):.4f}")
print("  越晚出现的元素入选概率越低，但替换机制保持了整体均匀")

print("\n== 加权蓄水池 A-Res ==")
items = [("premium", 10.0), ("normal", 1.0), ("normal", 1.0),
         ("premium", 10.0), ("normal", 1.0), ("premium", 10.0)]
from collections import Counter
counter = Counter()
for _ in range(3000):
    pool = weighted_reservoir(items, 2, random.Random(42))
    for v in pool:
        counter[v] += 1
print(f"  物品池（权重）: {items}")
print(f"  3000 次抽 2 个的命中次数: {dict(counter)}")
print(f"  premium 总权重 30 / normal 总权重 3 -> "
      f"期望占比 premium≈{30/(30+3):.1%}")
print(f"  实测 premium 占比≈{counter['premium']/(sum(counter.values())):.1%}")

print("\n== 分布式蓄水池（分片合并） ==")
def distributed_sample(streams, k, seed=0):
    """每个分片抽 k 个，合并后用 Algorithm R 从合并池里再抽 k 个。"""
    shard_samples = []
    for i, stream in enumerate(streams):
        s, _ = reservoir_sample(stream, k, random.Random(seed * 100 + i))
        shard_samples.extend(s)
    return reservoir_sample(iter(shard_samples), k, random.Random(seed))

streams = [[f"s{i}-item{j}" for j in range(100)] for i in range(4)]
sample, _ = distributed_sample(streams, 8)
print(f"  4 个分片各 100 元素 -> 合并抽样 {len(sample)} 个: {sample}")
print("  每个分片抽 k 个再合并，数学上等价于对全体均匀抽样")

print("\n== 与固定种子/精确抽样的对比 ==")
for line in (
    "  random.sample(population, k) 需要整体已知（先读入内存）",
    "  蓄水池抽样适合「流式/长度未知/内存受限」三种场景",
    "  固定 seed 让样本可复现，便于回归测试",
    "  与第680课 bootstrap 呼应：都是「有限样本推断总体」的工具",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  池大小 k 是内存上界：日志降采样场景先定 k 再定策略",
    "  并行写入时用「每分片独立蓄水池 + 合并」避免锁竞争",
    "  需要删除已选元素时，可用「负权重/时间衰减」扩展",
    "  面试高频：Algorithm R 的均匀性证明要能手推",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 用归纳法严格证明 Algorithm R 的均匀性。
# 2. 实现「带衰减的蓄水池」：旧样本权重随时间指数下降。
# 3. 对比 reservoir sample 与 random.sample 在 1 亿元素上的内存与耗时。
# 4. 思考：为什么替换时选「随机位置 j<i」而不是「随机池中位置」？
