# ===== 第840课：区块链与信任机制-数字签名与所有权验证 =====
# 知识点：
#   - 数字签名 = 私钥签名 + 公钥验证，证明「我有这把私钥」且「消息未被篡改」
#   - 与哈希/HMAC 的区别：签名是非对称的（公私钥对），HMAC 是对称的
#   - 与第76章玩具 RSA 的区别：真实签名用 ECDSA/Ed25519，本课用玩具 RSA 教学
#   - 签名流程：hash(message) -> sign(hash, private_key) -> verify(hash, sig, public_key)
#   - Bitcoin 用 ECDSA secp256k1；本课用简化的 RSA 签名教学
# 依赖：无（标准库）
import hashlib
import secrets
import math


def egcd(a, b):
    if b == 0: return (a, 1, 0)
    g, x1, y1 = egcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)


def mod_inv(a, m):
    g, x, _ = egcd(a % m, m)
    if g != 1: raise ValueError(f"{a} 与 {m} 不互素")
    return x % m


def is_prime(n, rounds=20):
    if n < 2: return False
    for p in (2,3,5,7,11,13,17,19,23,29,31,37):
        if n % p == 0: return n == p
    d, r = n - 1, 0
    while d % 2 == 0: d //= 2; r += 1
    for _ in range(rounds):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x in (1, n-1): continue
        for _ in range(r-1):
            x = x*x % n
            if x == n-1: break
        else: return False
    return True


def generate_keys(bits=32):
    """生成教学用 RSA 密钥对。"""
    while True:
        p = secrets.randbits(bits // 2) | (1 << (bits // 2 - 1)) | 1
        if is_prime(p): break
    while True:
        q = secrets.randbits(bits // 2) | (1 << (bits // 2 - 1)) | 1
        if is_prime(q) and p != q: break
    n = p * q
    phi = (p - 1) * (q - 1)
    e = 65537
    while phi % e == 0: e += 2
    d = mod_inv(e, phi)
    return {"public": (e, n), "private": (d, n)}


def sign(message, private_key):
    d, n = private_key
    h = int.from_bytes(hashlib.sha256(message.encode()).digest()[:8], "big") % n
    return pow(h, d, n)


def verify(message, signature, public_key):
    e, n = public_key
    h = int.from_bytes(hashlib.sha256(message.encode()).digest()[:8], "big") % n
    return pow(signature, e, n) == h


print("== 生成密钥对 ==")
alice_keys = generate_keys(32)
bob_keys = generate_keys(32)
print(f"  Alice 公钥 (e,n): {alice_keys['public']}")
print(f"  Alice 私钥 (d,n): {alice_keys['private']}")
print(f"  Bob   公钥 (e,n): {bob_keys['public']}")

print("\n== 签名与验证 ==")
msg = "Alice 转给 Bob 5 BTC"
sig = sign(msg, alice_keys["private"])
print(f"  消息: {msg!r}")
print(f"  签名: {sig}")
print(f"  用 Alice 公钥验证: {verify(msg, sig, alice_keys['public'])}")
print(f"  用 Bob   公钥验证: {verify(msg, sig, bob_keys['public'])}（应为 False）")

print("\n== 篡改检测 ==")
tampered_msg = "Alice 转给 Bob 500 BTC"
print(f"  篡改消息: {verify(tampered_msg, sig, alice_keys['public'])}")
tampered_sig = (sig + 1) % alice_keys["private"][1]
print(f"  篡改签名: {verify(msg, tampered_sig, alice_keys['public'])}")

print("\n== 不可伪造性 ==")
print("  没有私钥的人无法伪造签名：")
for fake_sig in (sig + 1, sig - 1, 42, 0):
    print(f"    fake_sig={fake_sig}: {verify(msg, fake_sig, alice_keys['public'])}")
print("  只有持有私钥 d 的人才能生成有效签名（数学困难性：RSA 问题）")

print("\n== 签名的三个性质 ==")
for line in (
    "  不可伪造 unforgeable: 没有私钥就无法产生有效签名",
    "  不可抵赖 non-repudiation: 签名后不能否认自己签过",
    "  不可篡改 tamper-evident: 消息任何改动都导致签名验证失败",
):
    print(" ", line)

print("\n== 数字签名 vs HMAC ==")
print(f"  {'维度':<14}{'数字签名':<22}{'HMAC'}")
for row in (("密钥", "公私钥对（非对称）", "共享密钥（对称）"),
            ("验证方", "任何人用公钥", "只有持有密钥的人"),
            ("不可否认", "是", "否（双方都知道密钥）"),
            ("速度", "慢", "快")):
    print(f"  {row[0]:<14}{row[1]:<22}{row[2]}")

print("\n== 在区块链中的应用 ==")
for line in [
    "  交易签名：发起者用私钥签名交易，节点用公钥验证",
    "  地址 = 公钥的哈希：公钥暴露后才暴露地址（隐私保护）",
    "  Bitcoin 用 ECDSA secp256k1，本课用简化 RSA 教学签名",
    "  与第76课玩具 RSA 加密的区别：加密是保密性，签名是认证性",
]:
    print("  -", line)

print("\n== 工程要点 ==")
for line in [
    "  真实签名用椭圆曲线（ECDSA/Ed25519），密钥更短速度更快",
    "  签名前必须哈希消息，防止「签名预言机」攻击",
    "  密钥管理最重要：私钥泄露 = 所有被签消息失效",
    "  生产用 cryptography / PyNaCl，绝不用自制 RSA",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 用第837课 UTXO 模型集成签名验证：交易必须用正确的私钥签名。
# 2. 实现「多重签名」：需要 k 个签名中的 m 个有效才通过交易。
# 3. 实现 Ed25519 的简化教学版（用小椭圆曲线参数）。
# 4. 思考：为什么签名用哈希后的小整数，而不是对完整消息做模幂？
