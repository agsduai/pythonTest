# ===== 第795课：流式算法与数据摘要-流模型与单遍处理 =====
# 知识点：
#   - 数据流模型：数据只能「顺序扫一遍」、内存远小于数据量、答案允许近似
#   - 单遍 single pass：每个元素只看一次；两遍算法在大数据/流场景不可用
#   - 精确 vs 近似：流式算法的答案有概率保证 (ε, δ)；内存与精度可调
#   - 三类典型问题：频次（谁出现多）、基数（有多少不同的）、分位数（P50/P99）
#   - 数据流算法在监控、广告计数、网络流量、数据库查询优化里无处不在
#   - 本课先建立「流」的抽象：无限迭代器 + 有限的内存状态
# 依赖：无（标准库）
import random
import statistics


def make_stream(n, distinct, seed=0):
    """生成 n 个元素的流，值来自 distinct 个不同键。"""
    rng = random.Random(seed)
    keys = [f"key{i}" for i in range(distinct)]
    # Zipf 分布：少数键占多数流量（真实流量特征）
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


def exact_stats(stream):
    """精确统计（作为基线）：需要记住所有见过的键。"""
    counts = {}
    for x in stream:
        counts[x] = counts.get(x, 0) + 1
    return {
        "distinct": len(counts),
        "total": sum(counts.values()),
        "top": sorted(counts.items(), key=lambda x: -x[1])[:5],
        "memory_keys": len(counts),
    }


print("== 数据流模型 ==")
N, D = 100000, 5000
stream = make_stream(N, D, seed=7)
exact = exact_stats(stream)
print(f"  流长度={exact['total']:,}  不同键={exact['distinct']:,}")
print(f"  Top-5: {exact['top']}")
print(f"  精确统计需要记住 {exact['memory_keys']:,} 个键（全部内存）")
print(f"  如果有 10 亿不同用户，精确统计需要 GB 级内存 → 必须近似")

print("\n== 流的抽象：迭代器 + 有限状态 ==")
def counted_stream(stream, budget):
    """演示：只有 budget 个槽位时，用固定内存扫描。"""
    state = {"seen": 0, "samples": []}
    for x in stream:
        state["seen"] += 1
        if len(state["samples"]) < budget:
            state["samples"].append(x)
    return state
st = counted_stream(make_stream(N, D, seed=7), budget=3)
print(f"  处理 {st['seen']:,} 个元素，内存里只留 {len(st['samples'])} 个样本")

print("\n== 单遍 vs 多遍 ==")
for line in (
    "  多遍算法（外部排序、MapReduce 两阶段 job）可以来回扫",
    "  单遍算法：数据库聚合、Kafka 消费、网络探针——数据转瞬即逝",
    "  判定标准：数据能否再次获取？获取成本是否远大于计算成本？",
    "  许多「离线批处理」问题换个视角就是流问题",
):
    print(" ", line)

print("\n== 近似保证的语法 ==")
for line in (
    "  (ε, δ) 保证：错误超过 ε·N 的概率 ≤ δ",
    "  例如 Count-Min Sketch：估计值 ≥ 真值，且误差 ≤ ε·N 以概率 1-δ",
    "  空间 = O((1/ε)·log(1/δ))，与流长度无关！",
    "  这类保证让近似算法可以被放进 SLA/容量规划",
):
    print(" ", line)

print("\n== 流式算法全家桶（本章内容导览） ==")
print(f"  {'问题':<14}{'算法':<22}{'误差类型':<16}{'内存'}")
for row in (("频次估计", "Count-Min Sketch", "只高不低", "O(1/ε·log1/δ)"),
            ("基数估计", "HyperLogLog", "±1~2%", "O(log log n)"),
            ("频繁项 Top-K", "Misra-Gries", "确定性", "O(k)"),
            ("均匀抽样", "蓄水池抽样", "精确", "O(k)"),
            ("分位数", "Greenwald-Khanna", "ε-近似", "O(1/ε·log n)")):
    print(f"  {row[0]:<14}{row[1]:<22}{row[2]:<16}{row[3]}")

print("\n== 与精确算法的关系 ==")
for line in [
    "  流式算法不是「降低标准」，而是用可控误差换不可能的内存",
    "  小数据集（能全放内存）直接用精确算法，别过度设计",
    "  误差保证是「 worst case 上界」，实际表现通常更好",
    "  监控系统里常并行跑多个 sketch，各答各的问题",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 用 Zipf 分布生成 100 万元素流，测量精确统计的内存峰值（sys.getsizeof 累计）。
# 2. 实现「两遍算法」求 Top-K，与后续单遍算法对比。
# 3. 给流加「撤销」操作（元素被删除），讨论哪些 sketch 还能工作。
# 4. 思考：为什么流式算法都尽量避免「哈希碰撞后无法撤销」？
