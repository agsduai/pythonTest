# ===== 第733课：分布式系统算法-一致性哈希与分区 =====
# 知识点：
#   - 普通取模 hash(key) % N 在节点增减时几乎全部键要重映射（灾难性）
#   - 一致性哈希：把节点和键都映射到 [0, 2^m) 环上，键顺时针找第一个节点
#   - 增删节点只影响环上相邻一小段键，迁移量 ≈ K/N
#   - 虚拟节点 vnode：每个物理节点映射多个点，缓解数据倾斜与热点
#   - 副本：顺时针找后续 R 个不同物理节点，跨机架/可用区放置
#   - 与第624课空间索引/第72章工作流无关；本课聚焦「键 -> 节点」映射
# 依赖：无（标准库）
import bisect
import hashlib
from collections import Counter

RING_BITS = 32
RING_SIZE = 1 << RING_BITS


def h(s):
    return int.from_bytes(hashlib.md5(s.encode()).digest()[:4], "big")


def mod_shard(key, n):
    return h(key) % n


print("== 取模分区：加一个节点几乎全量迁移 ==")
keys = [f"user:{i}" for i in range(10000)]
for old_n, new_n in ((4, 5), (9, 10)):
    moved = sum(mod_shard(k, old_n) != mod_shard(k, new_n) for k in keys)
    print(f"  {old_n} -> {new_n} 节点: {moved}/{len(keys)} = {moved/len(keys):.1%} 的键要迁移")
print("  理论迁移比例 = N/(N+1)，加 1 台要搬走 80%+ 数据")


class ConsistentHash:
    def __init__(self, replicas=1):
        self.replicas = replicas
        self.ring = {}          # ring 位置 -> 物理节点
        self.sorted_keys = []

    def _add_points(self, node):
        for i in range(self.replicas):
            pos = h(f"{node}#{i}") % RING_SIZE
            while pos in self.ring:
                pos = (pos + 1) % RING_SIZE
            self.ring[pos] = node
        self.sorted_keys = sorted(self.ring)

    def add(self, node):
        self._add_points(node)

    def remove(self, node):
        for pos, n in list(self.ring.items()):
            if n == node:
                del self.ring[pos]
        self.sorted_keys = sorted(self.ring)

    def node_for(self, key):
        if not self.ring:
            return None
        pos = h(key) % RING_SIZE
        idx = bisect.bisect_right(self.sorted_keys, pos) % len(self.sorted_keys)
        return self.ring[self.sorted_keys[idx]]

    def replicas_for(self, key, count=3):
        """顺时针找 count 个不同物理节点（跳过虚拟节点重复）。"""
        if not self.ring:
            return []
        pos = h(key) % RING_SIZE
        start = bisect.bisect_right(self.sorted_keys, pos)
        out = []
        for i in range(len(self.sorted_keys) * 2):
            node = self.ring[self.sorted_keys[(start + i) % len(self.sorted_keys)]]
            if node not in out:
                out.append(node)
            if len(out) == count:
                break
        return out


print("\n== 一致性哈希：迁移量 ≈ K/N ==")
for vnodes in (1, 16, 128):
    ring = ConsistentHash(vnodes)
    for n in ("N1", "N2", "N3", "N4"):
        ring.add(n)
    before = {k: ring.node_for(k) for k in keys}
    ring.add("N5")
    moved = sum(before[k] != ring.node_for(k) for k in keys)
    print(f"  4->5 节点, vnode={vnodes:>3}: 迁移 {moved/len(keys):.1%} "
          f"（理论 1/5=20%）")

print("\n== 虚拟节点改善数据倾斜 ==")
for vnodes in (1, 8, 64, 256):
    ring = ConsistentHash(vnodes)
    for n in ("N1", "N2", "N3", "N4", "N5"):
        ring.add(n)
    cnt = Counter(ring.node_for(k) for k in keys)
    vals = list(cnt.values())
    print(f"  vnode={vnodes:>3}: 分布={dict(sorted(cnt.items()))} "
          f"最多/最少={max(vals)/min(vals):.2f}×")
print("  vnode 越多越均匀，但内存与成员变更广播成本上升")

print("\n== 副本放置 ==")
ring = ConsistentHash(64)
for n in ("AZ1-N1", "AZ1-N2", "AZ2-N1", "AZ2-N2", "AZ3-N1"):
    ring.add(n)
for k in ("order:1001", "user:42", "session:xyz"):
    print(f"  {k:<14} -> 主 {ring.node_for(k)}, 3 副本 {ring.replicas_for(k, 3)}")
print("  生产还要保证副本落在不同机架/AZ，本例仅按物理节点去重")

print("\n== 环上位置分布（前 5 个物理节点，vnode=8）==")
r2 = ConsistentHash(8)
for n in ("N1", "N2", "N3"):
    r2.add(n)
print("  环点数:", len(r2.ring))
print("  前 10 个位置:", [(p, r2.ring[p]) for p in r2.sorted_keys[:10]])

print("\n== 一致哈希 vs 范围分区 ==")
for line in (
    "  哈希分区: 分布均匀、点查快；范围查询要散到所有节点",
    "  范围分区: 范围扫描高效、易分裂合并；可能有热点（如按时间递增键）",
    "  一致性哈希解决的是「节点变化时少搬数据」，不是「负载均衡」的全部",
    "  Highest Random Weight / Jump Hash / Maglev 是更均匀的无环方案",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  成员变更要所有客户端/代理看到同一张环（用配置中心/共识维护）",
    "  扩容时新节点要「预热」数据，期间读可能回源，需灰度切流",
    "  热点键（大 V、秒杀商品）一致性哈希也救不了，要单独拆分/本地缓存",
    "  Dynamo/Cassandra/Riak/memcached 客户端都用这套思路",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现加权一致性哈希：按节点容量分配不同数量的虚拟节点。
# 2. 对比 Jump Consistent Hash 的迁移量与分布均匀度。
# 3. 模拟「节点宕机 + 副本接管」，验证读仍能命中其余副本。
# 4. 思考：为什么「一致性哈希」不等于「自动负载均衡」？
