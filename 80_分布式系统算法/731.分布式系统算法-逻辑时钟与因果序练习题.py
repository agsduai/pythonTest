# ===== 第731课：分布式系统算法-逻辑时钟与因果序 =====
# 知识点：
#   - 物理时钟不可靠（时钟漂移、NTP 回拨），分布式系统用逻辑时钟刻画「先后」
#   - Lamport 时钟：本地事件 +1；发消息带时间戳；收件时 t=max(local,msg)+1
#   - Lamport 性质：a -> b（happens-before）则 L(a) < L(b)，反之不成立
#   - 向量时钟：每节点一个分量，可判定因果 / 并发（a||b 时互不可比）
#   - 全序广播：用 (Lamport 时间戳, 节点 ID) 打破平局，得到全局一致顺序
#   - 本课用可注入的事件序列模拟多节点消息传递，不依赖真实时钟
# 依赖：无（标准库）
from dataclasses import dataclass, field


@dataclass
class Event:
    node: str
    kind: str        # local / send / recv
    label: str
    lamport: int = 0
    vector: dict = field(default_factory=dict)


class LamportNode:
    def __init__(self, name):
        self.name, self.time, self.log = name, 0, []

    def tick(self, label, kind="local"):
        self.time += 1
        e = Event(self.name, kind, label, self.time)
        self.log.append(e)
        return e

    def send(self, label):
        return self.tick(label, "send")

    def recv(self, label, msg_time):
        self.time = max(self.time, msg_time) + 1
        e = Event(self.name, "recv", label, self.time)
        self.log.append(e)
        return e


print("== Lamport 时钟：三节点消息链 ==")
A, B, C = LamportNode("A"), LamportNode("B"), LamportNode("C")
a1 = A.send("A1->B")
b1 = B.recv("B recv A1", a1.lamport)
b2 = B.send("B2->C")
b3 = B.tick("B local")
c1 = C.recv("C recv B2", b2.lamport)
a2 = A.tick("A local2")
c2 = C.tick("C local")
for n in (A, B, C):
    print(f"  {n.name}: {[(e.label, e.lamport) for e in n.log]}")
print(f"  a1 -> b1 因果成立且 L(a1)={a1.lamport} < L(b1)={b1.lamport}")
print(f"  但 L(a2)={a2.lamport} < L(c2)={c2.lamport} 不代表 a2 发生在 c2 之前（可并发）")

print("\n== 向量时钟 ==")
class VectorNode:
    def __init__(self, name, peers):
        self.name = name
        self.v = {p: 0 for p in peers}
        self.log = []

    def tick(self, label, kind="local"):
        self.v[self.name] += 1
        e = Event(self.name, kind, label, vector=dict(self.v))
        self.log.append(e)
        return e

    def send(self, label):
        return self.tick(label, "send")

    def recv(self, label, msg_v):
        for k in self.v:
            self.v[k] = max(self.v[k], msg_v.get(k, 0))
        self.v[self.name] += 1
        e = Event(self.name, "recv", label, vector=dict(self.v))
        self.log.append(e)
        return e


def compare(v1, v2):
    """返回 'before' / 'after' / 'equal' / 'concurrent'。"""
    le = all(v1.get(k, 0) <= v2.get(k, 0) for k in set(v1) | set(v2))
    ge = all(v1.get(k, 0) >= v2.get(k, 0) for k in set(v1) | set(v2))
    if le and ge:
        return "equal"
    if le:
        return "before"
    if ge:
        return "after"
    return "concurrent"

PEERS = ["A", "B", "C"]
va, vb, vc = VectorNode("A", PEERS), VectorNode("B", PEERS), VectorNode("C", PEERS)
ea1 = va.send("A1")
eb1 = vb.recv("B recv A1", ea1.vector)
ea2 = va.tick("A2")
ec1 = vc.tick("C1 (与 A/B 并发)")
eb2 = vb.send("B2->C")
ec2 = vc.recv("C recv B2", eb2.vector)
for n in (va, vb, vc):
    print(f"  {n.name}: {[(e.label, list(e.vector.values())) for e in n.log]}")
print(f"  A1 {compare(ea1.vector, eb1.vector)} B-recv-A1（因果）")
print(f"  A2 {compare(ea2.vector, ec1.vector)} C1（应为并发）")
print(f"  B2 {compare(eb2.vector, ec2.vector)} C-recv-B2（因果）")

print("\n== 因果 vs 并发 判定表 ==")
pairs = [
    ({"A":1,"B":0,"C":0}, {"A":1,"B":1,"C":0}, "before"),
    ({"A":2,"B":0,"C":0}, {"A":1,"B":3,"C":0}, "concurrent"),
    ({"A":1,"B":1,"C":0}, {"A":1,"B":1,"C":0}, "equal"),
    ({"A":2,"B":2,"C":1}, {"A":1,"B":1,"C":1}, "after"),
]
for v1, v2, expect in pairs:
    got = compare(v1, v2)
    print(f"  {list(v1.values())} vs {list(v2.values())} -> {got:<11} 期望={expect}")

print("\n== 全序广播（total order broadcast）==")
events = [(3, "A", "write x=1"), (3, "B", "write x=2"), (1, "C", "read"),
          (3, "C", "write x=3"), (2, "A", "read")]
ordered = sorted(events)      # (Lamport, node_id) 元组天然全序
print("  按 (Lamport时间, 节点ID) 排序:")
for t, node, desc in ordered:
    print(f"    t={t} {node} {desc}")
print("  所有节点用同样规则排序 -> 得到一致的状态机顺序（状态机复制 SMR）")

print("\n== 混合逻辑时钟 HLC（概念）==")
for line in (
    "  HLC = 物理时间 + 逻辑计数，既接近墙上时钟又保持因果",
    "  l = max(physical, last.l); 同物理时刻内用 c 递增",
    "  CockroachDB / MongoDB 用 HLC 做分布式事务时间戳",
):
    print(" ", line)

print("\n== 应用 ==")
for line in [
    "  冲突检测：向量时钟判断两个写是否并发（购物车/协同编辑）",
    "  版本向量 / Dotted Version Vector 是向量时钟的工程变体",
    "  全序广播是 Paxos/Raft 之上实现复制状态机的接口",
    "  因果一致性比强一致弱，但比最终一致强，适合很多业务",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 HLC（物理+逻辑混合时钟），验证因果不丢且接近墙上时间。
# 2. 用向量时钟检测「并发写冲突」，输出需要人工合并的键集合。
# 3. 实现版本向量的压缩（只保留每个节点最后一次计数器）。
# 4. 思考：为什么 Lamport 时钟无法判断两个事件是否并发？
