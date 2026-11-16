# ===== 第841课：区块链与信任机制-P2P网络与数据传播 =====
# 知识点：
#   - P2P 网络：节点对等连接，无中心服务器；新区块/交易通过 gossip 传播
#   - 与第737课 Gossip 的关系：737 讲通用 gossip，这里用 gossip 传播区块链数据
#   - 新交易/新区块的传播路径：产生 → 发给已连接节点 → 它们转发 → 全网收敛
#   - 节点发现：种子节点 → 握手 → 交换已知节点列表
#   - 网络分区：节点可能被隔离，恢复后需要同步（最重链规则）
#   - 本课用标准库模拟 P2P 网络的区块传播与分叉解决
# 依赖：无（标准库）
import hashlib
import random
import time
from collections import defaultdict


def sha256(data):
    return hashlib.sha256(data.encode()).hexdigest()


class Peer:
    """P2P 网络中的一个节点。"""

    def __init__(self, name, peers=None):
        self.name = name
        self.peers = set(peers or [])     # 已连接的对等节点名
        self.chain = [{"index": 0, "prev_hash": "0"*64, "data": "genesis",
                       "hash": sha256("genesis")}]
        self.known_txs = set()
        self.log = []

    def connect(self, other_name):
        self.peers.add(other_name)

    def broadcast_block(self, block):
        """向所有对等节点广播新区块（gossip）。"""
        self.log.append(f"{self.name} 广播 Block#{block['index']}")
        return [(peer, block) for peer in self.peers]

    def receive_block(self, block, sender):
        """接收并验证新区块。"""
        prev = self.chain[-1]
        if block["prev_hash"] != prev["hash"]:
            # 可能是分叉或延迟到达的旧块
            if block["index"] <= prev["index"]:
                self.log.append(f"{self.name} 忽略旧块 #{block['index']}（来自 {sender}）")
            else:
                self.log.append(f"{self.name} 无法验证 #{block['index']}（缺少中间块）")
            return False
        expected_hash = sha256(f"{block['index']}{block['prev_hash']}{block['data']}")
        if block["hash"] != expected_hash:
            self.log.append(f"{self.name} 拒绝无效块 #{block['index']}")
            return False
        self.chain.append(block)
        self.log.append(f"{self.name} 接受 Block#{block['index']}（来自 {sender}）")
        return True


print("== 构建 P2P 网络 ==")
nodes = {}
for name in ("Alice", "Bob", "Carol", "Dave"):
    nodes[name] = Peer(name)
# 连接拓扑：Alice-Bob, Bob-Carol, Carol-Dave, Dave-Alice
connections = [("Alice","Bob"), ("Bob","Carol"), ("Carol","Dave"), ("Dave","Alice")]
for a, b in connections:
    nodes[a].connect(b)
    nodes[b].connect(a)
print("  网络拓扑（环形）:")
for name in nodes:
    print(f"    {name} <-> {sorted(nodes[name].peers)}")

print("\n== Alice 产生新区块并传播 ==")
alice = nodes["Alice"]
new_block = {
    "index": 1,
    "prev_hash": alice.chain[-1]["hash"],
    "data": "新区块数据",
    "hash": sha256(f"1{alice.chain[-1]['hash']}新区块数据"),
}
alice.chain.append(new_block)
propagations = alice.broadcast_block(new_block)
for peer_name, block in propagations:
    peer = nodes[peer_name]
    peer.receive_block(block, "Alice")
print("  传播结果:")
for name in nodes:
    for entry in nodes[name].log:
        print(f"    {entry}")
print(f"  各节点链高度: { {n: len(nodes[n].chain) for n in nodes} }")
for n in nodes: nodes[n].log.clear()

print("\n== Bob 产生区块并传播（经过 Carol 到 Dave）==")
bob = nodes["Bob"]
bob_block = {
    "index": 2,
    "prev_hash": bob.chain[-1]["hash"],
    "data": "Bob 的新区块",
    "hash": sha256(f"2{bob.chain[-1]['hash']}Bob 的新区块"),
}
bob.chain.append(bob_block)
for peer_name, block in bob.broadcast_block(bob_block):
    peer = nodes[peer_name]
    peer.receive_block(block, "Bob")
print(f"  各节点链高度: { {n: len(nodes[n].chain) for n in nodes} }")
print("  Alice 直接收下；Carol 缺少 Block#1 无法验证（见日志）；Dave 与 Bob 不直接相连")
print("  Carol 把收到的块原样转发（真实节点会先请求缺失的中间块再验证）")
carol = nodes["Carol"]
for peer_name, block in carol.broadcast_block(bob_block):
    peer = nodes[peer_name]
    peer.receive_block(block, "Carol")
print(f"  转发后链高度: { {n: len(nodes[n].chain) for n in nodes} }")
for n in nodes: nodes[n].log.clear()

print("\n== Gossip 多跳传播模拟（全新 5 节点环形网络）==")
def gossip_block(origin, block, network, max_hops=5):
    """多跳传播：每个收到块的节点继续转发给它的邻居。"""
    informed = {origin}
    frontier = [(origin, block)]
    hops = 0
    for hop in range(max_hops):
        next_frontier = []
        for sender, blk in frontier:
            for peer_name in network[sender].peers:
                if peer_name not in informed:
                    peer = network[peer_name]
                    accepted = peer.receive_block(blk, sender)
                    if accepted:
                        informed.add(peer_name)
                        next_frontier.append((peer_name, blk))
        if not next_frontier: break
        frontier = next_frontier
        hops += 1
        if len(informed) == len(network): break
    return informed, hops

net2 = {}
for name in ("A", "B", "C", "D", "E"):
    net2[name] = Peer(name)
for a, b in (("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "A")):
    net2[a].connect(b)
    net2[b].connect(a)
blk = {
    "index": 1,
    "prev_hash": net2["A"].chain[-1]["hash"],
    "data": "gossip test",
    "hash": "",        # hash 按与 receive_block 相同的规则计算
}
blk["hash"] = sha256(f"{blk['index']}{blk['prev_hash']}{blk['data']}")
net2["A"].chain.append(blk)
informed, hops = gossip_block("A", blk, net2)
print(f"  起点=A, 传播到 {sorted(informed)}, 需要 {hops} 跳")
print(f"  总节点数={len(net2)}, 收到比例={len(informed)/len(net2):.0%}")

print("\n== P2P 网络的指标 ==")
for line in (
    "  传播跳数 O(log n)：gossip 协议的指数扩散特性",
    "  消息冗余：每个节点可能收到同一个块的多次转发",
    "  去重：节点用 (index, hash) 去重，避免重复处理",
    "  延迟 = 跳数 × 单跳延迟；网络拓扑影响传播效率",
):
    print(" ", line)

print("\n== P2P vs 中心化 ==")
print(f"  {'维度':<16}{'P2P 网络':<24}{'中心化服务'}")
for row in (("单点故障", "无", "服务器宕机=全挂"),
            ("审查抵抗", "高（无中心控制点）", "低"),
            ("数据一致性", "最终一致", "强一致"),
            ("带宽成本", "每节点承担", "中心承担全部")):
    print(f"  {row[0]:<16}{row[1]:<24}{row[2]}")

print("\n== 工程要点 ==")
for line in [
    "  节点发现：种子节点列表 + DNS seed + addr 消息交换",
    "  NAT 穿透：大部分节点在 NAT 后面，需要 UPnP 或中继",
    "  网络分区恢复：重连后按最重链规则同步（第839课）",
    "  Bitcoin 的 P2P 用 TCP 8333 端口，消息有魔数前缀 + 校验和",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「节点发现」：新节点通过种子节点获取其他节点地址。
# 2. 实现「网络分区」与「恢复同步」：分区两边的链不同，恢复后按最重链合并。
# 3. 加入「恶意节点」：广播无效区块，验证其他节点能拒绝。
# 4. 思考：为什么 gossip 传播比「广播到所有节点」更适合去中心化网络？
