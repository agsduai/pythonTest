# ===== 第839课：区块链与信任机制-分叉与共识博弈 =====
# 知识点：
#   - 分叉 fork：两个节点几乎同时出块，链分叉
#   - 最长链规则：始终选择最长（或最重）的链作为主链
#   - 孤儿块 orphan：不在主链上的区块被丢弃
#   - 51% 攻击：算力 > 50% 的攻击者可以制造更长的私有链覆盖公共链
#   - 最终性 finality：通常等 6 个确认后认为交易不可逆
#   - 与第80章 Raft 的对比：Raft 需要共识但只支持少数节点；PoW 允许开放加入
#   - 本课模拟分叉产生、最长链竞争与最终确认
# 依赖：无（标准库）
import hashlib
import random
import time
from dataclasses import dataclass, field


def sha256(data):
    return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class Block:
    index: int
    prev_hash: str
    data: str
    miner: str
    nonce: int = 0
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            content = f"{self.index}{self.prev_hash}{self.data}{self.miner}{self.nonce}"
            self.hash = sha256(content)


class ForkSimulator:
    """模拟区块链分叉与最长链竞争。"""

    def __init__(self, difficulty=3, seed=0):
        self.difficulty = difficulty
        self.rng = random.Random(seed)
        genesis = self._mine_block(0, "0"*64, "Genesis", "network")
        self.branches = {"main": [genesis]}   # 分支名 -> 块列表

    def _mine_block(self, index, prev_hash, data, miner):
        """模拟挖矿：随机找 nonce。"""
        target = "0" * self.difficulty
        nonce = 0
        while True:
            content = f"{index}{prev_hash}{data}{miner}{nonce}"
            h = sha256(content)
            if h.startswith(target):
                return Block(index, prev_hash, data, miner, nonce, h)
            nonce += 1
            if nonce > 100000:     # 安全上限
                return Block(index, prev_hash, data, miner, nonce, sha256(content))

    def add_block(self, branch, data, miner):
        """在指定分支上挖一个新区块。"""
        chain = self.branches[branch]
        prev = chain[-1]
        block = self._mine_block(prev.index + 1, prev.hash, data, miner)
        chain.append(block)
        return block

    def resolve_fork(self):
        """最长链规则：选择最长的分支作为主链，其他变为孤儿。"""
        best_branch = max(self.branches, key=lambda b: len(self.branches[b]))
        orphans = {name: chain for name, chain in self.branches.items()
                   if name != best_branch and len(chain) < len(self.branches[best_branch])}
        self.branches = {best_branch: self.branches[best_branch]}
        return best_branch, orphans

    def status(self):
        return {name: len(chain) for name, chain in self.branches.items()}


print("== 正常情况：无分叉 ==")
sim = ForkSimulator(difficulty=3, seed=1)
for data in ("Tx1", "Tx2", "Tx3"):
    b = sim.add_block("main", data, "miner1")
print(f"  链高度={sim.status()['main']}")

print("\n== 分叉产生：两个节点同时出块 ==")
sim2 = ForkSimulator(difficulty=3, seed=2)
genesis_h = sim2.branches["main"][-1].hash
# 两个节点从同一高度挖矿
for miner in ("minerA", "minerB"):
    b = sim2._mine_block(1, sim2.branches["main"][-1].hash, f"block by {miner}", miner)
    branch_name = f"fork_{miner}"
    sim2.branches[branch_name] = sim2.branches["main"][:] + [b]
print(f"  分叉后状态: {sim2.status()}")

print("\n== 继续在两条分支上挖矿 ==")
sim2.add_block("fork_minerA", "Tx by A", "minerA")
sim2.add_block("fork_minerB", "Tx by B", "minerB")
print(f"  各分支高度: {sim2.status()}")

print("\n== 最长链规则：选择胜者 ==")
winner, orphans = sim2.resolve_fork()
print(f"  胜出分支: {winner}（高度={sim2.status()[winner]}）")
print(f"  孤儿分支: {list(orphans.keys())}")
print("  孤儿块上的交易被丢弃，需重新打包进新区块")

print("\n== 51% 攻击模拟 ==")
def simulate_attack(attack_power=0.3, rounds=20, seed=0):
    """模拟诚实节点与攻击者的链竞争。
    attack_power = 攻击者的算力比例（0~1）。
    返回 (诚实链高度, 攻击链高度)。"""
    rng = random.Random(seed)
    honest_len, attack_len = 1, 1
    for _ in range(rounds):
        if rng.random() < attack_power:
            attack_len += 1
        else:
            honest_len += 1
    return honest_len, attack_len

for power in (0.2, 0.3, 0.4, 0.5, 0.51, 0.6):
    results = [simulate_attack(power, seed=s) for s in range(50)]
    attack_wins = sum(1 for h, a in results if a > h)
    print(f"  算力={power:.0%}: 攻击者追上诚实链的比例 = {attack_wins/50:.0%}")
print("  算力 < 50% 时几乎不可能追上；> 50% 时概率随时间趋近 100%")

print("\n== 最终性：6 个确认 ==")
print("  Bitcoin 约定：交易被 6 个后续区块确认后视为最终")
print(f"  攻击者需要重挖 6 个区块且超过诚实链 -> 6 深度时概率极低")
for depth in (1, 2, 3, 6):
    # 简化计算：攻击者算力 30% 时追上 d 深度的概率
    p_attack = 0.3
    p_honest = 0.7
    # Gambler's ruin: P(追上) = (p_attack/p_honest)^depth
    prob = (p_attack/p_honest) ** depth
    print(f"  深度={depth}: 攻击者追上概率={prob:.4f}")

print("\n== 分叉类型 ==")
for line in (
    "  自然分叉: 网络延迟导致两个节点几乎同时出块（自动解决）",
    "  软分叉 soft fork: 协议升级后旧节点认为新块无效（向后兼容）",
    "  硬分叉 hard fork: 协议规则不兼容（如 Bitcoin → Bitcoin Cash）",
    "  51% 攻击分叉: 恶意算力重写历史（第836课）",
):
    print(" ", line)

print("\n== PoW vs PoS vs Raft ==")
print(f"  {'维度':<14}{'PoW':<20}{'PoS':<18}{'Raft'}")
for row in (("加入门槛", "算力", "质押代币", "预配置节点"),
            ("共识速度", "~10min/块", "~秒级", "~毫秒级"),
            ("最终性", "概率性(6确认)", "概率性/确定", "确定性"),
            ("去中心化", "高", "中", "低(3~7节点)")):
    print(f"  {row[0]:<14}{row[1]:<20}{row[2]:<18}{row[3]}")

print("\n== 工程要点 ==")
for line in [
    "  分叉是正常现象，不是错误；关键是解决分叉的规则",
    "  最长链规则简单但可能被利用；GHOST 协议考虑了孤儿块的贡献",
    "  最终性的权衡：越快的最终性越容易分叉，越慢越安全",
    "  与第80章 Raft 的共识比较：Raft 适合小规模强一致场景",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现连续挖矿模拟（100 块），统计分叉发生的频率。
# 2. 实现 GHOST 协议：把孤儿块的算力也算入主链的「权重」。
# 3. 用第837课的 UTXO 模型模拟「双花攻击」在分叉场景下的结果。
# 4. 思考：为什么 Bitcoin 选择 6 个确认而不是 1 个或 100 个？
