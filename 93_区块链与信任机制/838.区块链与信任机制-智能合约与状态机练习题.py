# ===== 第838课：区块链与信任机制-智能合约与状态机 =====
# 知识点：
#   - 智能合约：部署在区块链上的程序，状态由区块链保证不可篡改
#   - 合约 = 状态存储 + 函数（改变状态的入口）+ 事件（状态变更的通知）
#   - 与第72章 FSM 的关系：合约的状态转移由交易触发，每笔交易是「一步」
#   - Gas：每次操作消耗 Gas，防止无限循环和资源滥用
#   - 本课用标准库实现一个简单的「投票合约」和「众筹合约」
#   - 明确标注：教学用最小实现，真实合约用 Solidity + EVM
# 依赖：无（标准库）
import hashlib
import time
from collections import defaultdict


class VoteContract:
    """投票合约：候选人列表 + 投票者注册 + 计票。"""

    def __init__(self, candidates, owner):
        self.candidates = list(candidates)
        self.votes = {c: 0 for c in candidates}
        self.registered_voters = set()
        self.has_voted = {}
        self.owner = owner
        self.closed = False
        self.events = []

    def register_voter(self, voter, caller):
        if caller != self.owner:
            self.events.append(("REJECT", f"只有部署者 {self.owner} 可以注册选民"))
            return False
        if self.closed:
            self.events.append(("REJECT", "投票已关闭"))
            return False
        self.registered_voters.add(voter)
        self.events.append(("REGISTER", voter))
        return True

    def vote(self, voter, candidate):
        if self.closed:
            self.events.append(("REJECT", "投票已关闭")); return False
        if voter not in self.registered_voters:
            self.events.append(("REJECT", f"{voter} 未注册")); return False
        if voter in self.has_voted:
            self.events.append(("REJECT", f"{voter} 已投过票")); return False
        if candidate not in self.votes:
            self.events.append(("REJECT", f"候选人 {candidate} 不存在")); return False
        self.votes[candidate] += 1
        self.has_voted[voter] = candidate
        self.events.append(("VOTE", voter, candidate))
        return True

    def close(self, caller):
        if caller != self.owner:
            self.events.append(("REJECT", "只有部署者可以关闭")); return False
        self.closed = True
        self.events.append(("CLOSE", "投票结束"))
        return True

    def results(self):
        return dict(sorted(self.votes.items(), key=lambda x: -x[1]))


class CrowdfundContract:
    """众筹合约：目标金额 + 截止时间 + 退款。"""

    def __init__(self, goal, deadline_block, owner):
        self.goal = goal
        self.deadline = deadline_block
        self.owner = owner
        self.pledges = defaultdict(float)    # backer -> 金额
        self.total_raised = 0.0
        self.finalized = False
        self.success = None
        self.events = []

    def pledge(self, backer, amount, current_block):
        if self.finalized:
            self.events.append(("REJECT", "众筹已结束")); return False
        if current_block >= self.deadline:
            self.events.append(("REJECT", "已过截止时间")); return False
        if amount <= 0:
            self.events.append(("REJECT", "金额必须为正")); return False
        self.pledges[backer] += amount
        self.total_raised += amount
        self.events.append(("PLEDGE", backer, amount))
        return True

    def finalize(self, current_block, caller):
        if caller != self.owner:
            self.events.append(("REJECT", "只有所有者可以 finalize")); return False
        if self.finalized:
            self.events.append(("REJECT", "已经 finalize")); return False
        if current_block < self.deadline:
            self.events.append(("REJECT", "尚未到截止时间")); return False
        self.finalized = True
        self.success = self.total_raised >= self.goal
        self.events.append(("FINALIZE", f"raised={self.total_raised}, goal={self.goal}, success={self.success}"))
        return self.success

    def refund(self, backer, caller):
        if not self.finalized: return False
        if self.success: return False       # 成功则不退款
        amount = self.pledges.get(backer, 0)
        if amount <= 0: return False
        self.pledges[backer] = 0
        self.events.append(("REFUND", backer, amount))
        return True


print("== 投票合约 ==")
vote = VoteContract(["Alice", "Bob"], owner="admin")
vote.register_voter("user1", "admin")
vote.register_voter("user2", "admin")
vote.register_voter("user3", "admin")
vote.vote("user1", "Alice")
vote.vote("user2", "Bob")
vote.vote("user3", "Alice")
vote.vote("user3", "Bob")           # 重复投票
vote.close("admin")
print("  事件日志:")
for e in vote.events:
    print("   ", e)
print(f"  结果: {vote.results()}")

print("\n== 众筹合约 ==")
crowd = CrowdfundContract(goal=100, deadline_block=10, owner="creator")
for backer, amount in (("backer1", 40), ("backer2", 35), ("backer3", 30)):
    crowd.pledge(backer, amount, current_block=5)
print(f"  已筹金额={crowd.total_raised} 目标={crowd.goal}")
crowd.finalize(current_block=12, caller="creator")
print(f"  众筹成功={crowd.success}")
if not crowd.success:
    for b in list(crowd.pledges):
        crowd.refund(b, "creator")
print("  退款后 pledges:", dict(crowd.pledges))

print("\n== Gas 概念 ==")
for line in (
    "  每个操作消耗 Gas：存储写入最贵（SSTORE = 20000 Gas）",
    "  Gas Limit 限制单笔交易的总消耗，防止无限循环",
    "  Gas Price 由市场决定（EIP-1559：base fee + tip）",
    "  教学意义：合约设计要最小化存储写入和循环",
):
    print(" ", line)

print("\n== 合约安全要点 ==")
for line in [
    "  重入攻击 Reentrancy: 外部调用可能再次调用合约 → 检查-效果-交互模式",
    "  整数溢出: Solidity 0.8+ 内置检查，旧版需要 SafeMath",
    "  访问控制: 只有 owner 可以执行管理操作",
    "  前置交易 Front-running: 看到别人的交易后抢先提交",
    "  教学要点：合约代码不可修改 → bug 永久存在 → 上线前必须审计",
]:
    print("  -", line)

print("\n== 智能合约 vs 传统程序 ==")
print(f"  {'维度':<16}{'传统程序':<26}{'智能合约'}")
for row in (("部署", "可随时更新", "不可修改（永久）"),
            ("信任", "需要信任运营方", "代码即法律"),
            ("状态", "数据库", "合约存储（链上）"),
            ("执行", "服务器", "所有节点重复执行")):
    print(f"  {row[0]:<16}{row[1]:<26}{row[2]}")

# ===== 练习题 =====
# 1. 给投票合约加「委托投票」：A 可以委托 B 代投。
# 2. 实现众筹合约的「安全提取」：贡献者在失败后自行提取退款。
# 3. 实现「Gas 估算」：统计每个合约操作的虚拟 Gas 消耗。
# 4. 思考：为什么智能合约的 bug 比传统程序更危险？
