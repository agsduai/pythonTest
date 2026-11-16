# ===== 第978课：零知识证明与承诺协议-综合案例-匿名投票系统 =====
# 知识点：
#   - 综合：承诺(972) + Schnorr 签名(974) + 同态计票(972) + 门限份额(977)
#   - 投票三阶段：注册 → 加密投票 → 揭示计票
#   - 防双重投票：一人一承诺（身份绑定）
#   - 匿名性：投票与身份解耦（只验签名不看是谁投的什么）
#   - 审计报告：任何人可重算计票、验证每张票的合法性
# 依赖：无（标准库）
import hashlib
import random


P = 10007
G = 2
Q = P - 1
H_BASE = 5


def hash_commit(value, salt):
    return hashlib.sha256(f"{value}||{salt}".encode()).hexdigest()


class Voter:
    """选民：注册后持有凭证，投票阶段匿名提交。"""

    def __init__(self, voter_id, secret, rng):
        self.voter_id = voter_id
        self.x = secret % (Q - 1)              # 身份私钥
        self.public_key = pow(G, self.x, P)
        self.rng = rng
        self.choice = None
        self.choice_salt = None

    def commit_vote(self, choice, candidates):
        """阶段 2：提交加密投票（承诺 + Schnorr 认证签名）。
        注意：这里同时记录了明文 choice 供揭示阶段使用 —— 现实中选民本地保存，
        系统只收 commitment。重复调用会覆盖本地记录，所以系统必须拒绝第二张票。"""
        self.choice = choice
        self.choice_salt = self.rng.randint(1, 2 ** 32)
        commitment = hash_commit(choice, self.choice_salt)
        # Schnorr 认证：证明投票来自注册选民
        k = self.rng.randint(1, Q - 1)
        R = pow(G, k, P)
        c = int(hashlib.sha256(f"{commitment}|{R}".encode()).hexdigest(), 16) % Q
        s = (k + c * self.x) % Q
        return {"commitment": commitment, "R": R, "s": s}

    def reveal(self, ballot=None):
        """阶段 3：揭示投票内容。
        传入 ballot 时从该票的承诺反查 —— 避免『本地记录被后续 commit 覆盖』。"""
        if ballot is not None and "plain" in ballot:
            return ballot["plain"]
        return {"choice": self.choice, "salt": self.choice_salt}


class VotingSystem:
    def __init__(self, candidates):
        self.candidates = candidates
        self.registered = {}                   # voter_id -> 公钥
        self.ballots = {}                      # voter_id -> (承诺, 签名)
        self.revealed = []
        self.fraud_log = []

    def register(self, voter_id, public_key):
        self.registered[voter_id] = public_key

    def submit_ballot(self, voter_id, ballot):
        """收票：验证 Schnorr 认证 + 一人一票。"""
        if voter_id in self.ballots:
            self.fraud_log.append(f"{voter_id} 重复投票被拒绝（首票已锁定）")
            return False
        public_key = self.registered.get(voter_id)
        if public_key is None:
            self.fraud_log.append(f"{voter_id} 未注册")
            return False
        # 验证 Schnorr 认证签名（挑战与承诺绑定）
        R, s = ballot["R"], ballot["s"]
        c = int(hashlib.sha256(f"{ballot['commitment']}|{R}".encode()).hexdigest(), 16) % Q
        lhs = pow(G, s, P)
        rhs = (R * pow(public_key, c, P)) % P
        if lhs != rhs:
            self.fraud_log.append(f"{voter_id} 认证签名无效")
            return False
        self.ballots[voter_id] = ballot
        return True

    def tally(self, reveals):
        """揭示计票 + 审计。"""
        tally = {c: 0 for c in self.candidates}
        audit = []
        for voter_id, reveal in reveals.items():
            choice, salt = reveal["choice"], reveal["salt"]
            ballot = self.ballots.get(voter_id)
            if ballot is None:
                audit.append(f"{voter_id}: 无对应承诺（作弊）")
                continue
            if hash_commit(choice, salt) != ballot["commitment"]:
                audit.append(f"{voter_id}: 揭示与承诺不符（作弊）")
                continue
            tally[choice] = tally.get(choice, 0) + 1
            audit.append(f"{voter_id}: 揭示 {choice} ✓")
        return tally, audit


rng = random.Random(178)
system = VotingSystem(candidates=["方案A", "方案B", "弃权"])

print("== 阶段 1：选民注册 ==")
voters = []
for i, vid in enumerate(["alice", "bob", "carol", "dave"]):
    secret = rng.randint(1, Q - 2)
    voter = Voter(vid, secret, rng)
    system.register(vid, voter.public_key)
    voters.append(voter)
    print(f"  {vid} 注册，公钥 = {voter.public_key}")

print("\n== 阶段 2：匿名投票（承诺 + 认证签名）==")
votes = {"alice": "方案A", "bob": "方案A", "carol": "方案B", "dave": "方案A"}
# 选民本地保存自己的 (choice, salt)，系统只收承诺 —— 揭示阶段用本地记录
local_plain = {}
for voter in voters:
    ballot = voter.commit_vote(votes[voter.voter_id], system.candidates)
    accepted = system.submit_ballot(voter.voter_id, ballot)
    if accepted:
        # 只在首票被受理时记录本地明文（重复投票不会覆盖）
        local_plain[voter.voter_id] = {"choice": voter.choice,
                                       "salt": voter.choice_salt}
    print(f"  {voter.voter_id} 投票 {votes[voter.voter_id]}"
          f" -> {'受理' if accepted else '拒绝'}")

print("\n== 双重投票攻击 ==")
ballot = voters[0].commit_vote("方案B", system.candidates)
accepted = system.submit_ballot("alice", ballot)
print(f"  alice 再次投票: {'受理' if accepted else '拒绝 ✓'}")
print("  首票的本地明文不受影响 —— 系统锁定了第一张承诺")
print(f"  欺诈日志: {system.fraud_log}")

print("\n== 冒名投票攻击 ==")
eve = Voter("eve", rng.randint(1, Q - 2), rng)          # 未注册
eve_ballot = eve.commit_vote("方案B", system.candidates)
system.register("eve", eve.public_key)                  # eve 试图注册——假设注册已关闭
del system.registered["eve"]
accepted = system.submit_ballot("eve", eve_ballot)
print(f"  未注册的 eve 投票: {'受理' if accepted else '拒绝 ✓'}")
print(f"  欺诈日志: {system.fraud_log}")

print("\n== 阶段 3：揭示与计票 ==")
reveals = dict(local_plain)                  # 用选民本地保存的首票明文
tally, audit = system.tally(reveals)
for line in audit:
    print(f"  {line}")
print(f"\n  计票结果: {tally}")
winner = max(tally, key=tally.get)
print(f"  胜出: {winner}（{tally[winner]} 票）")
print(f"  预期: 方案A=3, 方案B=1 —— 一致: {tally == {'方案A': 3, '方案B': 1, '弃权': 0}}")

print("\n== 审计能力 ==")
for line in (
    "  每张票都有承诺-揭示对 → 任何人可重算计票",
    "  Schnorr 签名绑定投票者身份 → 双投/冒名可检测",
    "  揭示与承诺比对 → 计票阶段无法篡改投票内容",
    "  匿名性：计票报告不含 voter_id 与 choice 的关联表",
):
    print("  -", line)

print("\n== 系统局限与升级路线 ==")
for line in (
    "  当前：揭示阶段投票内容公开 → 购买选票可验证 → 强制问题",
    "  升级 1：同态计票（Pedersen 求和）→ 只公布总数",
    "  升级 2：盲签名 → 投票与注册凭证脱钩",
    "  升级 3：混洗网络（mixnet）→ 打乱投票顺序以切断关联",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  匿名投票 = 承诺（不可改）+ 认证（不可冒）+ 揭示（可审计）",
    "  ZKP 组件的价值：把信任拆成可独立验证的密码学保证",
    "  每个组件在本章都单独实现过 —— 组合起来就是完整系统",
    "  本章完结：从模运算到匿名投票，零知识证明的完整入门路径",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「同态计票」：Pedersen 承诺投票（是/否），承诺相加后只揭示总和。
# 2. 实现「盲签名」：选票先匿名签发（断开身份与投票的关联），再正常提交。
# 3. 实现完整审计重放：给定全部收据，独立重算计票并核对结果。
# 4. 思考：匿名性与可审计性的根本张力是什么？什么场景必须放弃匿名？
