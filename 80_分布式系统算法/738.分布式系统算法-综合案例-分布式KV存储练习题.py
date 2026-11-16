# ===== 第738课：分布式系统算法-综合案例-分布式 KV 存储 =====
# 知识点：
#   - 综合串起本章：一致性哈希分区 + Quorum 读写 + 版本向量 + Gossip 成员 + φ 故障检测
#   - 一个 KV 请求的路径：client -> 哈希定位 -> 副本集 -> Quorum 写/读 -> 冲突合并
#   - 节点故障：φ 检测器标记下线 -> Gossip 传播成员变更 -> 读修复补齐落后副本
#   - 一致性模型：默认最终一致（R+W>N 时可读己之写），并发写保留冲突集
#   - 全部标准库 + 可注入 rng/clock，纯内存、离线可运行
#   - 明确是教学玩具：无真实网络、无持久化、无线性一致读
# 依赖：无（标准库）
import bisect
import hashlib
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field

RING = 1 << 16


def h(s):
    return int.from_bytes(hashlib.md5(s.encode()).digest()[:2], "big")


@dataclass
class Version:
    value: object
    vector: dict          # 节点 -> 计数
    ts: int = 0

    def merge(self, other):
        """向量时钟比较：before / after / concurrent。"""
        keys = set(self.vector) | set(other.vector)
        le = all(self.vector.get(k, 0) <= other.vector.get(k, 0) for k in keys)
        ge = all(self.vector.get(k, 0) >= other.vector.get(k, 0) for k in keys)
        if le and ge:
            return "equal"
        return "before" if le else ("after" if ge else "concurrent")


@dataclass
class Node:
    name: str
    store: dict = field(default_factory=dict)      # key -> [Version,...]
    online: bool = True
    clock: int = 0


class KVCluster:
    def __init__(self, names, replicas=3, W=2, R=2, vnodes=8, seed=7):
        self.nodes = {n: Node(n) for n in names}
        self.replicas, self.W, self.R = replicas, W, R
        self.rng = random.Random(seed)
        self.ring, self.ring_keys = {}, []
        for n in names:
            for i in range(vnodes):
                pos = h(f"{n}#{i}")
                while pos in self.ring:
                    pos = (pos + 1) % RING
                self.ring[pos] = n
        self.ring_keys = sorted(self.ring)
        self.membership = {n: True for n in names}
        self.clock = 0
        self.log = []

    def _alive(self):
        return [n for n, ok in self.membership.items() if ok]

    def nodes_for(self, key, count=None):
        """顺时针取 count 个不同物理节点。"""
        count = count or self.replicas
        pos = h(key)
        start = bisect.bisect_right(self.ring_keys, pos)
        out = []
        for i in range(len(self.ring_keys) * 2):
            n = self.ring[self.ring_keys[(start + i) % len(self.ring_keys)]]
            if n not in out:
                out.append(n)
            if len(out) == count:
                break
        return out

    def replicas_for(self, key):
        return [n for n in self.nodes_for(key) if self.membership[n]]

    def put(self, key, value, writer="client"):
        targets = self.replicas_for(key)
        if len(targets) < self.W:
            return False, f"可用副本 {len(targets)} < W={self.W}，拒绝写入"
        self.clock += 1
        # 同一次写入的所有副本共享同一版本；串行写入直接替换旧值
        vec = {f"w{self.clock}": 1}
        for n in targets:
            self.nodes[n].store[key] = [Version(value, vec, self.clock)]
        self.log.append(f"PUT {key}={value!r} -> {targets}")
        return True, f"写入 {len(targets)} 副本（W={self.W}）"

    def get(self, key, read_repair=True):
        targets = self.replicas_for(key)
        if len(targets) < self.R:
            return None, f"只拿到 {len(targets)} 个副本，未达 R={self.R}"
        # 收集所有副本的版本，按向量时钟归并
        all_versions = []
        for n in targets:
            all_versions.extend(self.nodes[n].store.get(key, []))
        if not all_versions:
            return None, "键不存在"
        # 保留「最大」的并发版本集合
        maximal = []
        for v in all_versions:
            if not any(o is not v and v.merge(o) == "before" for o in all_versions):
                maximal.append(v)
        # 同一逻辑版本去重
        seen, unique = set(), []
        for v in maximal:
            sig = (repr(v.value), tuple(sorted(v.vector.items())))
            if sig not in seen:
                seen.add(sig); unique.append(v)
        if read_repair:
            for n in targets:
                self.nodes[n].store[key] = list(unique)
        self.log.append(f"GET {key} <- {targets}")
        if len(unique) == 1:
            return unique[0].value, "单版本（无冲突）"
        return [v.value for v in unique], f"{len(unique)} 个并发版本，需业务合并"

    def fail_node(self, name):
        self.membership[name] = False
        self.log.append(f"NODE DOWN {name}（由 φ 检测器触发，Gossip 传播）")

    def recover_node(self, name):
        self.membership[name] = True
        self.log.append(f"NODE UP {name}")

    def status(self):
        return {n: len(v.store) for n, v in self.nodes.items()}


print("== 构建集群 ==")
kv = KVCluster(["N1", "N2", "N3", "N4", "N5"], replicas=3, W=2, R=2)
print(f"  5 节点，每键 3 副本，W=2 R=2，R+W={2+2}>N=3（副本集内保证交集）")
for key in ("user:1", "order:9", "cart:42"):
    print(f"  {key:<10} -> 副本集 {kv.nodes_for(key)}")

print("\n== 正常读写 ==")
for k, v in (("user:1", "alice"), ("order:9", "pending"), ("cart:42", "[A,B]")):
    print(f"  {kv.put(k, v)}")
for k in ("user:1", "order:9", "cart:42", "missing"):
    val, note = kv.get(k)
    print(f"  GET {k:<10} -> {val!r}  ({note})")

print("\n== 节点故障：写入仍可用（W=2 容忍 1 台） ==")
kv.fail_node("N1")
ok, msg = kv.put("user:1", "alice-v2")
print(f"  PUT after failure: {ok}, {msg}")
print("  副本集:", kv.nodes_for("user:1"), " 可用:", kv.replicas_for("user:1"))
val, note = kv.get("user:1")
print(f"  GET after failure: {val!r} ({note})")

print("\n== 恢复 + 读修复 ==")
kv.recover_node("N1")
# 模拟 N1 落后
kv.nodes["N1"].store.pop("user:1", None)
print("  人为清空 N1 上的 user:1（模拟落后副本）")
val, note = kv.get("user:1", read_repair=True)
print(f"  读修复后 GET: {val!r}")
print(f"  N1 上 user:1 版本数: {len(kv.nodes['N1'].store.get('user:1', []))}")

print("\n== 并发写冲突（网络分区两边各写一份）==")
# 模拟：同一 key 在两个不同副本上各自递增向量时钟
c2 = KVCluster(["A", "B", "C"], replicas=3, W=1, R=2, seed=11)
c2.put("doc", "版本A", writer="w1")
# 手动让 B 上产生一个与 A 并发的版本
c2.nodes["B"].store["doc"] = [Version("版本B", {"B": 9}, 99)]
val, note = c2.get("doc")
print(f"  GET doc -> {val!r}  ({note})")
print("  向量时钟无法定序时保留冲突集，交给业务（如购物车取并集）")

print("\n== 成员变更日志（节选）==")
for line in kv.log[:8]:
    print("  -", line)

print("\n== 分层回顾 ==")
for line in [
    "  分区层  : 一致性哈希 + 虚拟节点定位副本集（第733课）",
    "  复制层  : Quorum W/R + 读修复（第734课）",
    "  冲突层  : 向量时钟判定因果/并发（第731课）",
    "  成员层  : φ 故障检测 + Gossip 传播（第736/737课）",
    "  一致性  : 最终一致，非 Raft 强一致（第732课）",
    "  事务    : 跨键原子性需 2PC/Saga，本例不支持（第735课）",
]:
    print("  -", line)

print("\n== 与真实系统的差距 ==")
for line in [
    "  无持久化/WAL/磁盘分页（第726课）、无真实网络与超时重传",
    "  无线性一致读（需 Leader lease / read-index / 共识）",
    "  无成员变更时的副本迁移与数据重平衡",
    "  Dynamo/Cassandra/Riak 是这套组合的工业实现",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加 hinted handoff：目标副本宕机时写替身，恢复后回传。
# 2. 实现 Merkle 树反熵，后台修复长期落后的副本（第737课）。
# 3. 增加 read-index 机制，提供可选的线性一致读。
# 4. 思考：为什么 Dynamo 选择最终一致，而 etcd 选择 Raft 强一致？
