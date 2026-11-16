# ===== 第732课：分布式系统算法-共识算法Raft =====
# 知识点：
#   - Raft 把共识拆成：领导选举、日志复制、安全性（比 Paxos 更易理解）
#   - 节点三态：Follower / Candidate / Leader；任期 term 单调递增
#   - 选举：心跳超时 -> 自增 term -> 拉票；获多数票即成为 Leader
#   - 日志复制：Leader 追加条目，多数派确认后 commit，再应用到状态机
#   - 安全性：选举限制（候选日志必须至少和新的一样新），保证已提交不丢
#   - 脑裂防护：旧 Leader 收到更高 term 立即退位；分区里少数派无法提交
#   - 本课用可注入时钟/网络模拟选举与复制，不真实起进程
# 依赖：无（标准库）
import random
from dataclasses import dataclass, field

FOLLOWER, CANDIDATE, LEADER = "Follower", "Candidate", "Leader"


@dataclass
class LogEntry:
    term: int
    command: str
    index: int


@dataclass
class Node:
    name: str
    peers: list
    state: str = FOLLOWER
    term: int = 0
    voted_for: str = None
    log: list = field(default_factory=list)
    commit_index: int = -1
    voted: set = field(default_factory=set)
    election_timeout: float = 0.0


class Cluster:
    def __init__(self, names, seed=7):
        self.rng = random.Random(seed)
        self.nodes = {n: Node(n, [x for x in names if x != n]) for n in names}
        self.clock = 0.0
        self.partition = set()          # 被隔离、收不到消息的节点
        self.reset_timeouts()

    @property
    def majority(self):
        return len(self.nodes) // 2 + 1

    def reset_timeouts(self):
        for n in self.nodes.values():
            n.election_timeout = self.clock + self.rng.uniform(1.5, 3.0)

    def reachable(self, a, b):
        return a not in self.partition and b not in self.partition

    def start_election(self, name):
        n = self.nodes[name]
        n.state = CANDIDATE
        n.term += 1
        n.voted_for = name
        n.voted = {name}
        n.election_timeout = self.clock + self.rng.uniform(1.5, 3.0)
        last_idx, last_term = len(n.log) - 1, n.log[-1].term if n.log else 0
        for peer in n.peers:
            if not self.reachable(name, peer):
                continue
            p = self.nodes[peer]
            # 选举限制：候选日志至少和投票者一样新
            p_last_idx, p_last_term = len(p.log) - 1, p.log[-1].term if p.log else 0
            up_to_date = (last_term, last_idx) >= (p_last_term, p_last_idx)
            if n.term > p.term or (n.term == p.term and p.voted_for in (None, name)):
                if up_to_date:
                    p.term = max(p.term, n.term)
                    p.voted_for = name
                    p.state = FOLLOWER
                    n.voted.add(peer)
        if len(n.voted) >= self.majority:
            n.state = LEADER
            print(f"    t={self.clock:>4.1f} {name} 在第 {n.term} 任期当选 Leader "
                  f"（{len(n.voted)}/{len(self.nodes)} 票）")
            return True
        return False

    def replicate(self, leader_name, command):
        leader = self.nodes[leader_name]
        if leader.state != LEADER:
            return False, "不是 Leader"
        entry = LogEntry(leader.term, command, len(leader.log))
        leader.log.append(entry)
        acks = 1
        for peer in leader.peers:
            if self.reachable(leader_name, peer):
                p = self.nodes[peer]
                p.term = max(p.term, leader.term)
                p.log.append(entry)
                p.state = FOLLOWER
                acks += 1
        if acks >= self.majority:
            leader.commit_index = entry.index
            for p in self.nodes.values():
                if p.log and len(p.log) > p.commit_index:
                    p.commit_index = min(leader.commit_index, len(p.log) - 1)
            return True, f"{acks} 副本确认，已提交 index={entry.index}"
        return False, f"仅 {acks} 副本，未达多数派，不提交"

    def tick(self, dt=0.5):
        self.clock += dt
        for n in self.nodes.values():
            if n.state == LEADER:
                continue
            if self.clock >= n.election_timeout:
                self.start_election(n.name)

    def status(self):
        return {name: (n.state, n.term, len(n.log), n.commit_index)
                for name, n in self.nodes.items()}


print("== 初始状态 ==")
c = Cluster(["A", "B", "C", "D", "E"], seed=3)
print(" ", c.status())
print(f"  多数派 = {c.majority}/5")

print("\n== 触发选举（推进虚拟时钟）==")
for _ in range(12):
    c.tick(0.5)
    leaders = [n for n, v in c.nodes.items() if v.state == LEADER]
    if leaders:
        break
print("  选举后:", c.status())

leader = next((n for n, v in c.nodes.items() if v.state == LEADER), None)
print("\n== 日志复制 ==")
for cmd in ("SET x=1", "SET y=2", "SET z=3"):
    ok, msg = c.replicate(leader, cmd)
    print(f"  {cmd:<10} -> {ok}, {msg}")
print("  各节点日志长度:", {n: len(v.log) for n, v in c.nodes.items()})

print("\n== 网络分区：Leader 被单独隔离到少数派 ==")
# partition 里的节点收不到任何消息；其余 4 个节点仍互通（4 >= 多数派 3）
c.partition = {leader}
survivors = [n for n in c.nodes if n not in c.partition]
print(f"  被隔离={sorted(c.partition)}，仍互通的多数派={survivors} "
      f"({len(survivors)} >= {c.majority})")
# 只让一个节点先超时发起选举，避免同一 tick 里人人拉票（真实 Raft 靠随机超时错开）
first = survivors[0]
c.nodes[first].election_timeout = c.clock
for n in survivors[1:]:
    c.nodes[n].election_timeout = c.clock + 10
for _ in range(15):
    c.tick(0.5)
    new_leader = next((n for n in survivors if c.nodes[n].state == LEADER), None)
    if new_leader:
        break
print(f"  新 Leader={new_leader}, term={c.nodes[new_leader].term if new_leader else '-'}")
ok, msg = c.replicate(leader, "SET x=OLD")
print(f"  旧 Leader 尝试写入: {ok}, {msg}（少数派，无法提交 -> 防脑裂）")
if new_leader:
    ok, msg = c.replicate(new_leader, "SET x=NEW")
    print(f"  新 Leader 写入    : {ok}, {msg}")

print("\n== 分区恢复：旧 Leader 发现更高 term 后退位 ==")
c.partition = set()
# 模拟旧 Leader 收到新 Leader 的心跳（带更高 term）
old = c.nodes[leader]
new_term = max(v.term for v in c.nodes.values())
if new_term > old.term:
    old.term = new_term
    old.state = FOLLOWER
    print(f"  旧 {leader} 收到 term={new_term} 的消息 -> 退位为 Follower")
print("  恢复后状态:", c.status())

print("\n== Raft 安全性要点 ==")
for line in (
    "  Election Safety  : 一个任期最多一个 Leader",
    "  Leader Append-Only: Leader 从不覆盖/删除自己的日志",
    "  Log Matching      : 相同 (index,term) 的条目内容相同，且前缀一致",
    "  Leader Completeness: 已提交条目必定出现在后续所有 Leader 的日志里",
    "  State Machine Safety: 不会有两个节点在同一 index 应用不同命令",
):
    print(" ", line)

print("\n== 与 Paxos / 工程实现 ==")
for line in [
    "  Paxos 更通用但难懂难实现；Raft 强 Leader + 可理解性优先",
    "  etcd(raft)/Consul/TiKV 都基于 Raft 或其变体",
    "  生产还要处理：成员变更、日志压缩快照、只读线性一致、PreVote",
    "  本课省略了 AppendEntries 的完整一致性检查与 nextIndex 回退",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 AppendEntries 的 prevLogIndex/prevLogTerm 匹配与冲突回退。
# 2. 增加 PreVote，减少分区节点反复抬 term 干扰集群。
# 3. 实现日志快照压缩：丢弃已应用且被多数派确认的前缀。
# 4. 思考：为什么「少数派分区不能提交」是防止脑裂的关键？
