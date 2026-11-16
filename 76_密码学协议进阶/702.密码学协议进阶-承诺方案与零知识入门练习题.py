# ===== 第702课：密码学协议进阶-承诺方案与零知识入门 =====
# 知识点：
#   - 承诺 commitment：先「锁定」一个值，之后公开，期间不能改、也不能被猜出
#   - 两个性质：hiding（承诺不泄露值）、binding（无法事后换成别的值）
#   - 哈希承诺 C = H(value || salt)；salt 防小值域暴力枚举（猜 0/1 很容易）
#   - 打开阶段公开 (value, salt)，验证方重算哈希比对
#   - 佩德森承诺思路：C = g^v · h^r mod p，具有加法同态（教学简化版）
#   - 零知识入门：Schnorr 协议的「三轮」结构（承诺->挑战->响应），本课只讲直觉
#   - 全部标准库 + 小素数教学参数，明确标注不可用于生产
# 依赖：无（标准库）
import hashlib
import hmac
import secrets

print("== 为什么需要 salt：小值域会被枚举 ==")
def weak_commit(v):
    return hashlib.sha256(str(v).encode()).hexdigest()

c = weak_commit("yes")
for guess in ("yes", "no", "maybe"):
    if weak_commit(guess) == c:
        print(f"  猜 {guess!r} 命中 -> 承诺泄露了值")
print("  值域小（是/否、0~100）时必须加随机 salt")

print("\n== 加盐承诺 ==")
def commit(value, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.sha256(salt + str(value).encode()).digest()
    return salt, digest

def open_commit(value, salt, digest):
    check = hashlib.sha256(salt + str(value).encode()).digest()
    return hmac.compare_digest(check, digest)

value, salt = "方案A", None
salt, digest = commit(value)
print(f"  承诺 = {digest.hex()[:32]}...（只公开这一串）")
print(f"  salt = {salt.hex()}（打开时才公开）")
print("  窃听者无法从承诺反推值；值域再小也没用，因为 salt 是随机的")
print("  验证打开:", open_commit("方案A", salt, digest))
print("  试图抵赖成 方案B:", open_commit("方案B", salt, digest))

print("\n== 同一值两次承诺应不同（hiding）==")
s1, d1 = commit("yes")
s2, d2 = commit("yes")
print(f"  d1={d1.hex()[:16]}... d2={d2.hex()[:16]}... 相同={d1 == d2}")
print("  若相同，观察者就能关联两次「同一个答案」")

print("\n== 抛硬币协议（双方都不信任对方）==")
# Alice 猜，Bob 抛。Bob 先承诺，Alice 再猜，最后 Bob 打开
def coin_flip_protocol(alice_guess, bob_actual=None):
    bob_actual = bob_actual if bob_actual is not None else secrets.choice(["正", "反"])
    salt, dig = commit(bob_actual)
    # Alice 此时只看到 dig，给出猜测
    # Bob 打开
    verified = open_commit(bob_actual, salt, dig)
    return {"bob": bob_actual, "alice": alice_guess, "verified": verified,
            "alice_wins": verified and alice_guess == bob_actual}

for g in ("正", "反", "正"):
    r = coin_flip_protocol(g)
    print(f"  Bob={r['bob']} Alice猜={r['alice']} 打开有效={r['verified']} "
          f"Alice赢={r['alice_wins']}")
print("  Bob 无法在看到 Alice 猜测后改结果（binding）")
print("  Alice 无法在猜之前知道结果（hiding）")

print("\n== 佩德森承诺（加法同态，教学参数）==")
p, g, h = 23, 5, 3          # 小素数，真实用大群
def pedersen(v, r=None, p=p, g=g, h=h):
    r = r if r is not None else secrets.randbelow(p - 1)
    return (pow(g, v, p) * pow(h, r, p)) % p, r

C1, r1 = pedersen(3)
C2, r2 = pedersen(4)
Csum = (C1 * C2) % p
C7, r7 = pedersen(7)
print(f"  C(3)={C1} C(4)={C2} C(3)·C(4)={Csum}")
print(f"  C(7)={C7}  相等: {Csum == C7}（加法同态，无需打开即可验和）")
print("  注意：这个同态性依赖 h 与 g 的离散对数关系未知；教学参数不安全")

print("\n== 零知识直觉：Schnorr 三轮 ==")
for line in (
    "  1) 证明者随机选 r，发承诺 R=g^r mod p",
    "  2) 验证者发随机挑战 c（证明者无法预知）",
    "  3) 证明者回应 z=r+c·x（x 是秘密），验证者查 g^z == R·y^c",
    "  关键: 不知道 x 的人无法同时对多个 c 作答；挑战随机 -> 可重复多轮降作弊概率",
    "  验证者全程只看到 R/c/z，学不到 x 的任何信息 -> 零知识",
):
    print(" ", line)

# 用教学参数演示一轮 Schnorr 的等式
x = 7                          # 秘密
y = pow(g, x, p)               # 公钥
r = secrets.randbelow(p - 1)
R = pow(g, r, p)
c = secrets.randbelow(p - 1)
z = r + c * x                  # 真实现在要 mod (p-1)，这里演示结构
lhs = pow(g, z, p)
rhs = (R * pow(y, c, p)) % p
print(f"\n  教学参数一轮: g={g} p={p} x={x} y={y}")
print(f"  g^z mod p={lhs}  R·y^c mod p={rhs}  相等={lhs == rhs}")
print("  （指数应对 p-1 取模；小参数仅用于展示等式结构）")

print("\n== 应用场景 ==")
for line in [
    "  密封投标 / 猜拳 / 抛硬币 / 彩票开奖前锁定结果",
    "  区块链：默克尔承诺、机密交易（Pedersen）、zk-SNARK",
    "  身份认证：Schnorr / Fiat-Shamir 变换成非交互式签名",
    "  生产实现用 cryptography / PyNaCl，别自己写群参数",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 修复 Schnorr 演示：把 z 对 (p-1) 取模，验证等式在任意 c 下成立。
# 2. 实现 Fiat-Shamir 变换：用 H(R) 当挑战，把三轮压成一轮非交互证明。
# 3. 用默克尔树把 100 个承诺聚合成一个根，验证单个值只需 O(log n) 路径。
# 4. 思考：为什么哈希承诺必须同时满足 hiding 与 binding，缺一会怎样？
