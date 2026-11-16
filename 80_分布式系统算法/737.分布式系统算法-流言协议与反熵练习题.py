# ===== 第737课：分布式系统算法-流言协议与反熵 =====
# 知识点：
#   - Gossip / 流言协议：每轮每个节点随机挑几个对等节点交换状态，最终全集群收敛
#   - 传播模型类似传染病：感染节点数呈 S 型曲线，轮数 O(log n)
#   - 反熵 anti-entropy：两个副本比对并补齐差异；Merkle 树把比对降到 O(log n)
#   - 流言类型：dissemination（传播新值）、anti-entropy（修复差异）、聚合（求平均/求和）
#   - 参数 fanout（每轮联系几个）、轮间隔；fanout 大收敛快但网络流量大
#   - 与第732课 Raft 对比：Gossip 是最终一致、去中心、可扩展；Raft 是强一致
# 依赖：无（标准库）
import hashlib
import random
from collections import defaultdict


def h(s):
    return hashlib.md5(s.encode()).hexdigest()[:8]


def gossip_rounds(n=50, fanout=2, seed=7, max_rounds=30):
    """模拟一条更新从 1 个节点扩散到全部节点。"""
    rng = random.Random(seed)
    infected = {0}
    history = [1]
    for r in range(1, max_rounds + 1):
        new = set()
        for node in list(infected):
            targets = rng.sample(range(n), min(fanout, n - 1))
            new.update(t for t in targets if t != node)
        before = len(infected)
        infected |= new
        history.append(len(infected))
        if len(infected) == n:
            return r, history
    return max_rounds, history


print("== 流言扩散：感染曲线 ==")
for fanout in (1, 2, 3, 5):
    rounds, hist = gossip_rounds(n=64, fanout=fanout, seed=5)
    print(f"  fanout={fanout}: {rounds} 轮收敛, 曲线={hist[:min(len(hist), 9)]}"
          f"{'...' if len(hist) > 9 else ''}")
print("  S 型曲线：初期慢、中期指数、后期扫尾慢（最后几个最难碰到）")

print("\n== 节点规模 vs 收敛轮数 ==")
for n in (16, 64, 256, 1024):
    rounds, _ = gossip_rounds(n=n, fanout=2, seed=5, max_rounds=40)
    print(f"  n={n:>5}: {rounds} 轮（≈ log2(n)={n.bit_length()-1} 量级）")

print("\n== 反熵：两副本比对并补齐差异 ==")
def anti_entropy(a, b):
    """返回 (a 缺的键, b 缺的键)，然后双向补齐。"""
    only_a = set(a) - set(b)
    only_b = set(b) - set(a)
    for k in only_b:
        a[k] = b[k]
    for k in only_a:
        b[k] = a[k]
    return only_a, only_b

r1 = {"u1": "v3", "u2": "v1", "u3": "v2"}
r2 = {"u2": "v1", "u3": "v9", "u4": "v1"}
print("  修复前 A:", r1)
print("  修复前 B:", r2)
only_a, only_b = anti_entropy(r1, r2)
print(f"  A 缺 {sorted(only_b)}, B 缺 {sorted(only_a)}")
print("  修复后 A:", r1)
print("  修复后 B:", r2)
print("  注意：同键不同值（u3）需要版本/时间戳决胜，反熵本身不解决冲突")

print("\n== Merkle 树把差异定位从 O(n) 降到 O(log n) ==")
class Merkle:
    def __init__(self, data):
        self.data = dict(sorted(data.items()))
        self.leaves = {k: h(f"{k}={v}") for k, v in self.data.items()}
        self.root = self._build(list(self.leaves.items()))

    def _build(self, items):
        if not items:
            return h("empty")
        if len(items) == 1:
            return items[0][1]
        mid = len(items) // 2
        return h(self._build(items[:mid]) + self._build(items[mid:]))

    def diff(self, other):
        """按键排序后二分比对：子树根相同则整段跳过，否则继续下探。"""
        keys = sorted(set(self.leaves) | set(other.leaves))
        def rec(ks):
            if not ks:
                return []
            left = [self._build([(k, self.leaves.get(k, "")) for k in ks]),
                    other._build([(k, other.leaves.get(k, "")) for k in ks])]
            if left[0] == left[1]:
                return []                       # 整段一致，无需再比
            if len(ks) == 1:
                return ks
            mid = len(ks) // 2
            return rec(ks[:mid]) + rec(ks[mid:])
        return rec(keys)

A = {f"k{i}": f"v{i}" for i in range(8)}
B = dict(A)
B["k5"] = "CHANGED"          # 只改一个键
ma, mb = Merkle(A), Merkle(B)
print(f"  A.root={ma.root}  B.root={mb.root}  相同={ma.root == mb.root}")
print(f"  朴素比对需传 {len(A)} 个键的哈希；Merkle 只需沿路径比 O(log n) 个节点")
print("  本例简化 diff 定位的差异键:", sorted(set(ma.diff(mb))))

print("\n== 流言聚合：求全集群平均值 ==")
def gossip_average(values, rounds=20, seed=3):
    rng = random.Random(seed)
    est = list(values)          # 每个节点持有的估计值
    for _ in range(rounds):
        for i in range(len(est)):
            j = rng.randrange(len(est))
            if j != i:
                avg = (est[i] + est[j]) / 2
                est[i] = est[j] = avg
    return est

vals = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
true_avg = sum(vals) / len(vals)
for r in (1, 3, 10, 30):
    est = gossip_average(vals, rounds=r, seed=3)
    print(f"  {r:>2} 轮后各节点估计: {[round(v,2) for v in est]} "
          f"真实均值={true_avg:.1f}")
print("  成对平均最终收敛到全局均值，去中心、无单点")

print("\n== Gossip vs 共识 ==")
print(f"  {'维度':<12}{'Gossip':<22}{'Raft/Paxos'}")
for row in (("一致性", "最终一致", "强一致/线性一致"),
            ("中心节点", "无", "有 Leader"),
            ("扩展性", "O(log n) 轮，节点多也稳", "通常 3~7 节点"),
            ("典型用途", "成员/元数据/监控/反熵", "配置/元数据/复制状态机")):
    print(f"  {row[0]:<12}{row[1]:<22}{row[2]}")

print("\n== 工程要点 ==")
for line in [
    "  消息要带版本号/时间戳/墓碑，否则删除会被旧值『复活』",
    "  fanout 与轮间隔需要按集群规模与带宽调优",
    "  Merkle 树分片粒度太粗会传多余数据，太细则树本身太大",
    "  Cassandra/Dynamo 用 gossip 做成员与故障检测 + Merkle 反熵修数据",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现带版本向量的反熵，正确处理「同键并发写」而不是简单覆盖。
# 2. 测量 fanout=1..8 的「收敛轮数 × 每轮消息数」总开销，找最优点。
# 3. 给 Merkle.diff 真正实现按层比较，统计实际传输的哈希个数。
# 4. 思考：为什么流言协议天然容忍节点频繁上下线？
