# ===== 第799课：流式算法与数据摘要-MisraGries与频繁项 =====
# 知识点：
#   - Heavy hitters / 频繁项：找出出现次数超过 θ·N 的元素（θ 为阈值）
#   - Misra-Gries：只维护 k 个计数器；保证频率 > N/(k+1) 的元素一定在候选集里
#   - 算法：新元素有槽就用；没槽就全体计数器 -1，计数器为 0 的槽让给新元素
#   - 计数器之和 ≤ N：每次「全体减一」的代价 ≤ 1/θ 次，总体 O(1/θ)
#   - 与 CMS 的区别：MG 是确定性算法、有明确候选集保证；CMS 是概率的频次估计
#   - Space-Saving 是 MG 的变体，直接估计「出现次数」而非候选集
# 依赖：无（标准库）
from collections import Counter
import random


def misra_gries(stream, k):
    """k 个计数器的 MG 算法；返回候选计数器。"""
    counters = {}
    for item in stream:
        if item in counters:
            counters[item] += 1
        elif len(counters) < k:
            counters[item] = 1
        else:
            # 全体 -1，清零项删除，腾出槽位
            for key in list(counters):
                counters[key] -= 1
                if counters[key] == 0:
                    del counters[key]
    return counters


def space_saving(stream, k):
    """Space-Saving 变体：新元素替换计数最小的槽并继承计数+1。"""
    counters = {}
    for item in stream:
        if item in counters:
            counters[item] += 1
        elif len(counters) < k:
            counters[item] = 1
        else:
            min_key = min(counters, key=counters.get)
            counters[item] = counters.pop(min_key) + 1
    return counters


print("== MG 保证推导 ==")
# 频率超过 N/(k+1) 的元素最多 k 个（鸽巢）——所以 k 个计数器一定覆盖它们
for k, theta in ((k, 1/(k+1)) for k in (4, 9, 19)):
    print(f"  k={k:>2} 个计数器: 保证捕捉频率 > N/{k+1} = {theta:.1%} 的元素")

print("\n== 模拟：3 个真 Heavy Hitter + 长尾 ==")
rng = random.Random(11)
N = 100000
# 构造：3 个高频项 + 1000 个长尾项
heavy = [("api:search", 0.20), ("api:login", 0.10), ("api:pay", 0.06)]
tail = [f"api:user{i}" for i in range(1000)]
tail_probs = [0.00064] * len(tail)    # 长尾合计约 0.64，余 0.0 归化
s = sum(w for _, w in heavy)
tail_p = (1 - s) / len(tail)
stream = []
for _ in range(N):
    u = rng.random()
    if u < s:
        acc = 0
        for key, w in heavy:
            acc += w
            if u < acc: stream.append(key); break
    else:
        stream.append(rng.choice(tail))

from collections import Counter
truth = Counter(stream)
true_heavy = [k for k, v in truth.items() if v > N * 0.05]
print(f"  流长度={N} 真实频率 > 5% 的项: "
      f"{[(k, f'{truth[k]/N:.1%}') for k in true_heavy]}")

print("\n== Misra-Gries：k 个计数器 ==")
for k in (5, 10, 20, 50):
    counters = misra_gries(stream, k)
    caught = [x for x in true_heavy if x in counters]
    est = {x: counters[x] for x in caught}
    print(f"  k={k:>2}: 候选={len(counters)} 抓住真 Heavy={len(caught)}/{len(true_heavy)} "
          f"估计={est}")
print("  保证：频率 > N/(k+1) 的元素一定在候选里（不漏）；计数值有下界但偏大")

print("\n== Space-Saving：估计更准 ==")
ss = space_saving(stream, 20)
top_ss = sorted(ss.items(), key=lambda x: -x[1])[:5]
real_top = sorted(truth.items(), key=lambda x: -x[1])[:5]
print(f"  Space-Saving Top-5: {top_ss}")
print(f"  真实 Top-5        : {real_top}")
print("  Space-Saving 直接给出频次估计（继承被淘汰项的计数），比原始 MG 更准")

print("\n== 误差界 ==")
for k in (10, 20, 50, 100):
    ss = space_saving(stream, k)
    errs = []
    for x in true_heavy:
        est = ss.get(x, 0)
        errs.append((est - truth[x]) / N)
    print(f"  k={k:>3}: heavy 项估计偏高量（相对N）= "
          f"{[f'+{e:.4f}' for e in errs]}")
print("  理论上界：估计 ≤ 真实频率 + N/(k+1)；k 越大越准")

print("\n== 应用场景 ==")
for line in [
    "  网络监控：找出 DDoS 攻击源 IP（频率异常高的源）",
    "  搜索引擎：热门查询词实时榜",
    "  数据库：热点 key 检测（缓存击穿预警，第49课）",
    "  推荐：短窗口内的热门内容（时效性优先于全量统计）",
]:
    print("  -", line)

print("\n== 与 CMS 的配合 ==")
for line in (
    "  CMS：回答「给定这个 key，频率是多少」——点查询",
    "  MG/Space-Saving：回答「哪些 key 频率最高」——Top-K 查询",
    "  常见组合：MG 找候选，CMS 精估频次；或直接用 Space-Saving 一站式",
    "  都支持 merge，分布式分片聚合后结果一致",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  「全体减一」操作在实现时可用延迟标记（存一个全局减量），摊还 O(1)",
    "  Space-Saving 用堆+双向链表可 O(1) 更新（Agarwal 版本）",
    "  阈值 θ 应按业务定：5% 用于攻击检测，0.1% 用于热搜",
    "  Top-K 滑动窗口版要结合时间衰减（第772课指数衰减思想）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「带删除的 Space-Saving」：元素可被撤销。
# 2. 对比 MG、Space-Saving、CMS 三者回答 Top-K 时的准确性。
# 3. 用真实数据集（如日志文件）验证 Space-Saving 的误差界。
# 4. 思考：为什么 MG 的候选集保证「不漏」但计数「偏高」？
