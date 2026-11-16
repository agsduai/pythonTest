# ===== 第735课：分布式系统算法-分布式事务与两阶段提交 =====
# 知识点：
#   - 2PC：协调者先 Prepare（各参与者投票），再 Commit/Abort（全局决定）
#   - 参与者 Prepare 成功后进入「不确定期」，必须等协调者最终决定，不能自行提交
#   - 阻塞缺陷：协调者宕机时参与者只能干等（需要超时 + 终止协议 / 3PC 缓解）
#   - 数据不一致窗口：Commit 消息部分到达时，有的节点已提交有的还在等
#   - 2PC 是「原子提交」协议，不是「并发控制」；隔离性由各节点本地锁保证
#   - 现代替代：Saga（第672课）、TCC、基于共识的提交（Spanner/Percolator）
#   - 本课用可注入的「消息丢失/节点崩溃」模拟各种故障路径
# 依赖：无（标准库）
from dataclasses import dataclass, field
from enum import Enum

PREPARE, COMMIT, ABORT, VOTE_YES, VOTE_NO = "PREPARE", "COMMIT", "ABORT", "YES", "NO"


class State(Enum):
    INIT = "初始"
    PREPARED = "已准备(不确定期)"
    COMMITTED = "已提交"
    ABORTED = "已中止"


@dataclass
class Participant:
    name: str
    state: State = State.INIT
    data: dict = field(default_factory=dict)
    prepared_data: dict = None
    fail_vote: bool = False
    log: list = field(default_factory=list)

    def prepare(self, txn, changes):
        self.log.append(f"{self.name}: 收到 PREPARE")
        if self.fail_vote:
            self.log.append(f"{self.name}: 本地校验失败 -> 投 NO")
            self.state = State.ABORTED
            return VOTE_NO
        self.prepared_data = dict(changes)
        self.state = State.PREPARED       # 持锁、写 redo、进入不确定期
        self.log.append(f"{self.name}: 写 WAL 并锁定 -> 投 YES（进入不确定期）")
        return VOTE_YES

    def decide(self, decision):
        self.log.append(f"{self.name}: 收到 {decision}")
        if decision == COMMIT:
            self.data.update(self.prepared_data or {})
            self.state = State.COMMITTED
        else:
            self.state = State.ABORTED
        self.prepared_data = None


class Coordinator:
    def __init__(self, participants):
        self.parts = participants
        self.log = []
        self.crash_after_prepare = False
        self.lost_commits = set()

    def run(self, txn, changes):
        print(f"  [协调者] 开始 2PC，事务 {txn}")
        votes = {}
        for p in self.parts:
            votes[p.name] = p.prepare(txn, changes)
            self.log.append(f"收到 {p.name} 投票: {votes[p.name]}")
        if any(v == VOTE_NO for v in votes.values()):
            decision = ABORT
            print("  [协调者] 有 NO 票 -> 全局 ABORT")
        else:
            decision = COMMIT
            print("  [协调者] 全票 YES -> 全局 COMMIT")
        self.log.append(f"写入全局决定日志: {decision}")
        if self.crash_after_prepare:
            print("  [协调者] !! 写完决定就宕机，COMMIT 未发出")
            return decision
        for p in self.parts:
            if p.name in self.lost_commits:
                self.log.append(f"发往 {p.name} 的 {decision} 消息丢失")
                continue
            p.decide(decision)
        return decision


def show(tag, parts):
    print(f"  {tag}: " + ", ".join(f"{p.name}={p.state.value}" for p in parts))


print("== 场景 1：全部成功 ==")
parts = [Participant("DB1"), Participant("DB2"), Participant("DB3")]
c = Coordinator(parts)
d = c.run("T1", {"balance": 100})
show("最终状态", parts)
print("  数据:", {p.name: p.data for p in parts})

print("\n== 场景 2：一个参与者投 NO -> 全局回滚 ==")
parts = [Participant("DB1"), Participant("DB2", fail_vote=True), Participant("DB3")]
c = Coordinator(parts)
d = c.run("T2", {"balance": 200})
show("最终状态", parts)
print("  数据:", {p.name: p.data for p in parts}, "（都不应写入）")

print("\n== 场景 3：协调者在 PREPARE 后宕机（阻塞缺陷）==")
parts = [Participant("DB1"), Participant("DB2")]
c = Coordinator(parts); c.crash_after_prepare = True
c.run("T3", {"x": 1})
show("参与者状态", parts)
print("  DB1/DB2 都卡在「已准备」，持锁等待，无法自行提交或回滚")
print("  这就是 2PC 的阻塞问题；需要协调者恢复后读日志补发决定")

print("\n== 场景 4：COMMIT 消息部分丢失（不一致窗口）==")
parts = [Participant("DB1"), Participant("DB2"), Participant("DB3")]
c = Coordinator(parts); c.lost_commits = {"DB3"}
c.run("T4", {"x": 9})
show("最终状态", parts)
print("  DB3 仍在不确定期；协调者需重发/参与者主动查询才能收敛")

print("\n== 完整参与者日志（重跑一次干净事务）==")
p1, p2, p3 = [Participant(f"DB{i+1}") for i in range(3)]
Coordinator([p1, p2, p3]).run("T5", {"v": 1})
for p in (p1, p2, p3):
    print(f"  {p.name}: {' -> '.join(p.log)}")

print("\n== 2PC 时序 ==")
for line in (
    "  Coordinator          Participant",
    "      |--- PREPARE ------>|   写 WAL、加锁、投 YES/NO",
    "      |<-- VOTE ----------|",
    "      |  [写全局决定日志]  |",
    "      |--- COMMIT/ABORT ->|   落盘、释放锁、回 ACK",
    "      |<-- ACK -----------|",
):
    print(line)

print("\n== 2PC 的代价与替代方案 ==")
for line in [
    "  同步阻塞、协调者单点、至少两轮 RTT + 多次持久化",
    "  3PC 加 CanCommit 与超时自动提交，但网络分区下仍可能不一致",
    "  Saga：长事务拆成本地事务 + 补偿，最终一致、无全局锁",
    "  Percolator / Spanner：用共识 + 时间戳 + 2PC 混合，兼顾一致与可用",
]:
    print("  -", line)

print("\n== CAP 视角 ==")
for line in (
    "  2PC 偏向 CP：分区时宁可阻塞也不让两边各自提交",
    "  可用性与一致性的取舍由业务决定（支付要 CP，点赞可 AP）",
    "  PACELC：即使无分区，也要在延迟(L)与一致性(C)之间选",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 实现协调者恢复：重启后读全局决定日志，向仍在 PREPARED 的节点补发决定。
# 2. 实现参与者超时终止协议：PREPARED 超时后向其他参与者询问决定。
# 3. 对比 Saga 与 2PC 在「长事务 + 高并发」下的锁持有时间。
# 4. 思考：为什么参与者在 PREPARED 状态不能自行决定提交？
