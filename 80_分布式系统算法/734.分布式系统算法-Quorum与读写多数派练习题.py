# ===== 第734课：分布式系统算法-Quorum与读写多数派 =====
# 知识点：
#   - Quorum：N 副本，写需 W 个确认、读需 R 个副本，满足 R + W > N 保证读到最新值
#   - 常见配置：N=3, W=2, R=2；W=N 强一致但可用性差；W=1 写快但可能丢
#   - 读写交集定理：任意读集合与写集合必至少重叠一个节点
#   - 版本/时间戳解决「哪个副本更新」；无时钟时用 (version, node) 决胜
#   - 宽松 Quorum sloppy quorum + hinted handoff 提升可用性但弱化一致性
#   - 本课模拟副本集、写扩散、读修复（read repair）与冲突版本合并
# 依赖：无（标准库）
from dataclasses import dataclass, field


@dataclass
class Replica:
    name: str
    store: dict = field(default_factory=dict)      # key -> (value, version)
    online: bool = True


@dataclass
class Cluster:
    replicas: list
    N: int = 0
    W: int = 2
    R: int = 2
    version: int = 0

    def __post_init__(self):
        self.N = len(self.replicas)

    def _alive(self):
        return [r for r in self.replicas if r.online]

    def write(self, key, value):
        self.version += 1
        v = self.version
        acks = []
        for r in self._alive():
            r.store[key] = (value, v)
            acks.append(r.name)
            if len(acks) >= self.W:
                break
        ok = len(acks) >= self.W
        return ok, acks, v

    def read(self, key, read_repair=True):
        responses = []
        for r in self._alive():
            if key in r.store:
                responses.append((r, *r.store[key]))
            if len(responses) >= self.R:
                break
        if len(responses) < self.R:
            return None, f"只拿到 {len(responses)} 个响应，未达 R={self.R}"
        best = max(responses, key=lambda x: (x[2], x[0].name))
        value, ver = best[1], best[2]
        if read_repair:
            for r in self._alive():
                cur = r.store.get(key, (None, -1))
                if cur[1] < ver:
                    r.store[key] = (value, ver)
        return value, f"取 version={ver}, 读修复 {sum(1 for r in self.replicas if r.store.get(key, (None,-1))[1] == ver)}/{self.N} 副本"


def make_cluster(n=3, W=2, R=2):
    return Cluster([Replica(f"N{i+1}") for i in range(n)], W=W, R=R)


print("== 交集定理：R + W > N ==")
for N, W, R in ((3, 2, 2), (3, 3, 1), (3, 1, 3), (3, 2, 1), (5, 3, 3), (5, 1, 2)):
    safe = W + R > N
    print(f"  N={N} W={W} R={R}: R+W={R+W} {'>' if safe else '<='} {N} -> "
          f"{'保证读到最新' if safe else '可能读到旧值'}")
print("  反例 N=3,W=2,R=1：读集合可能与写集合完全不交")

print("\n== 正常写入 + 读修复 ==")
c = make_cluster()
print("  write(x, 'v1'):", c.write("x", "v1"))
print("  各副本:", {r.name: r.store.get("x") for r in c.replicas})
# 模拟一个副本落后
c.replicas[2].store["x"] = ("stale", 0)
print("  人为让 N3 落后为 ('stale',0)")
value, note = c.read("x")
print(f"  read(x) -> {value!r}, {note}")
print("  读修复后:", {r.name: r.store.get("x") for r in c.replicas})

print("\n== 可用性：节点宕机时能否读写 ==")
for W, R in ((2, 2), (3, 1), (1, 3)):
    c2 = make_cluster(W=W, R=R)
    c2.replicas[2].online = False       # 挂 1 台
    ok_w, acks, _ = c2.write("k", "val")
    v, note = c2.read("k")
    print(f"  W={W},R={R} 挂1台: 写成功={ok_w}(acks={len(acks)}) "
          f"读={v!r} {note}")

print("\n== 版本冲突与决胜 ==")
c3 = make_cluster(W=2, R=2)            # 读会拿到两个副本，能看到版本差异
c3.write("y", "from-N1")
# 模拟另一路并发写只落到 N2、且版本更高
c3.version += 5
c3.replicas[1].store["y"] = ("from-N2", c3.version)
print("  写入后两副本:", {r.name: r.store.get("y") for r in c3.replicas[:2]})
v, note = c3.read("y")
print(f"  并发写后读: {v!r}（按 (version,node) 取最大）")
print("  真实系统用向量时钟保留冲突，交给业务合并（如购物车并集）")

print("\n== Sloppy Quorum / Hinted Handoff（概念） ==")
for line in (
    "  目标节点不可达时，写先落到「替身」节点并记 hint",
    "  目标恢复后替身把数据回传（hinted handoff）",
    "  提升可用性，但读可能没覆盖真正该在的副本 -> 弱化一致性",
    "  Dynamo 用 N/R/W + sloppy quorum + 向量时钟 + Merkle 反熵",
):
    print(" ", line)

print("\n== 配置权衡 ==")
print(f"  {'配置':<14}{'一致性':<12}{'写延迟':<10}{'读延迟':<10}{'可用性'}")
for row in (("W=N,R=1", "强(同步全副本)", "高", "低", "差(任一挂则写不了)"),
            ("W=2,R=2", "强(交集)", "中", "中", "容忍1台"),
            ("W=1,R=N", "强(读全副本)", "低", "高", "读不容忍故障"),
            ("W=1,R=1", "最终一致", "最低", "最低", "最好")):
    print(f"  {row[0]:<14}{row[1]:<12}{row[2]:<10}{row[3]:<10}{row[4]}")

print("\n== 工程要点 ==")
for line in [
    "  仅 R+W>N 还不够：需要读修复/反熵处理落后副本",
    "  写并发冲突要靠版本向量，不能只靠最后写入者获胜（LWW 会丢数据）",
    "  线性一致读还要过 Leader 或读索引（read-index），Quorum 本身不等价",
    "  监控副本滞后（replica lag）是运维重点",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现读修复的异步版本，并统计反熵同步前后的副本差异数。
# 2. 用向量时钟保留并发写冲突，返回冲突集合而不是 LWW 覆盖。
# 3. 模拟网络分区下「两边都能写」的分裂脑，验证合并策略。
# 4. 思考：为什么 R+W>N 仍不足以保证线性一致性？
