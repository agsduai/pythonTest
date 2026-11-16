# ===== 第700课：密码学协议进阶-Diffie-Hellman密钥协商 =====
# 知识点：
#   - DH 让双方在不安全信道上协商出共享密钥，窃听者只看到公开值也算不出
#   - 参数：大素数 p、生成元 g；私钥 a/b 保密，公钥 A=g^a mod p、B=g^b mod p
#   - 共享密钥 s = B^a mod p = A^b mod p = g^(ab) mod p（幂运算交换律）
#   - 安全性基于离散对数难题：由 A 反推 a 很难（p 足够大时）
#   - pow(base, exp, mod) 是模幂，必须用三参数版，别先算 g**a 再取模
#   - 裸 DH 不认证身份，会被中间人攻击（MITM）；需配合签名/证书（第706课）
#   - 本课用小素数做教学演示，真实部署用 2048-bit+ 群或 ECDH（cryptography 库）
# 依赖：无（标准库）
import hashlib
import secrets

print("== 教学用小参数 ==")
p = 23          # 素数
g = 5           # 生成元
print(f"  公开参数: p={p}, g={g}")
print("  说明：真实系统用 RFC 3526 的 2048/3072-bit MODP 群或椭圆曲线")

print("\n== 模幂（务必用 pow 三参数版）==")
def pub(private, p, g):
    return pow(g, private, p)

def shared(other_pub, private, p):
    return pow(other_pub, private, p)

a = secrets.randbelow(p - 2) + 1      # Alice 私钥
b = secrets.randbelow(p - 2) + 1      # Bob 私钥
A, B = pub(a, p, g), pub(b, p, g)
print(f"  Alice: 私钥 a={a}（保密） -> 公钥 A={A}（公开）")
print(f"  Bob  : 私钥 b={b}（保密） -> 公钥 B={B}（公开）")
s1, s2 = shared(B, a, p), shared(A, b, p)
print(f"  Alice 算 s=B^a mod p={s1}")
print(f"  Bob   算 s=A^b mod p={s2}")
print(f"  一致: {s1 == s2}，且应等于 g^(ab) mod p={pow(g, a*b, p)}")

print("\n== 窃听者视角 ==")
print("  公开可见: p, g, A, B")
def brute_force(p, g, target):
    for x in range(1, p):
        if pow(g, x, p) == target:
            return x
    return None
print(f"  小素数下暴力求 a = {brute_force(p, g, A)}（教学参数可被穷举）")
print("  p 为 2048 位时，最好的已知算法也需要天文级算力")

print("\n== 用不同素数规模看「离散对数」难度 ==")
for bits, pp in ((5, 23), (8, 251), (16, 65521)):
    gg = 2
    priv = secrets.randbelow(pp - 2) + 1
    public = pow(gg, priv, pp)
    found = brute_force(pp, gg, public)
    print(f"  p≈{bits:>2} bit({pp:>6}): 穷举空间 {pp-1:>6}，找到私钥={found is not None}")

print("\n== 从共享密钥派生会话密钥 ==")
def kdf(s, context=b"session"):
    return hashlib.sha256(context + str(s).encode()).digest()

k = kdf(s1)
print(f"  s={s1} -> HKDF 简化版会话密钥 {k.hex()[:32]}...")
print("  实际用 HKDF（extract + expand），并从密钥派生出加密密钥与 MAC 密钥")

print("\n== 中间人攻击（裸 DH 无认证）==")
# Mallory 分别与 Alice、Bob 各做一次 DH
m = secrets.randbelow(p - 2) + 1
M = pub(m, p, g)
s_am = shared(M, a, p)       # Alice 以为在和 Bob 通信
s_mb = shared(B, m, p)       # Mallory 与 Bob 的共享密钥
print(f"  Alice <-> Mallory 密钥={s_am}, Mallory <-> Bob 密钥={s_mb}")
print("  Mallory 可解密、篡改、再加密转发，而双方毫无察觉")
print("  -> DH 只解决「密钥协商」，不解决「对方是谁」")

print("\n== 前向保密（PFS）==")
for line in (
    "  每次会话用临时私钥（ephemeral DH, DHE/ECDHE），用完即丢",
    "  即使长期私钥日后泄露，历史会话密钥也推不出来",
    "  静态 DH（长期公钥固定）没有前向保密",
    "  TLS 1.3 已强制使用带前向保密的密钥交换",
):
    print(" ", line)

print("\n== 参数选择要点 ==")
for line in [
    "  p 必须是安全素数（p=2q+1，q 也是素数），防小步大步/Pohlig-Hellman",
    "  g 的阶要足够大；别用 g=1 这类退化值",
    "  私钥用 secrets 生成，且检查 1 < a < p-1",
    "  生产用标准群（RFC 7919 ffdhe）或 X25519，别自己造参数",
]:
    print("  -", line)

print("\n== 工程结论 ==")
print("  本课代码是教学玩具：p=23 完全不安全")
print("  真实项目用 cryptography 的 X25519 / ECDH + 签名认证（第706课）")

# ===== 练习题 =====
# 1. 用 Miller-Rabin 素性检测生成 512 位安全素数，重跑协商流程。
# 2. 实现三方 DH（Alice/Bob/Carol 协商同一个组密钥）并验证一致。
# 3. 给 DH 加「公钥固定为长期身份密钥」的简化签名，阻止上面的 MITM。
# 4. 思考：为什么 TLS 1.3 废弃静态 RSA/DH 密钥交换，只留 DHE/ECDHE？
