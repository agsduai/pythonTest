# ===== 第704课：密码学协议进阶-玩具RSA与数字签名 =====
# 知识点：
#   - RSA：选两素数 p,q，n=pq，φ=(p-1)(q-1)；取 e 与 φ 互素，d=e⁻¹ mod φ
#   - 加密 c=m^e mod n，解密 m=c^d mod n；签名 s=H(m)^d mod n，验证 s^e mod n == H(m)
#   - 模逆用扩展欧几里得；素性用 Miller-Rabin；pow(x,e,n) 三参数模幂
#   - 教科书 RSA 不安全：无填充、确定性、小指数、可被选择密文攻击
#   - 真实用 OAEP 填充加密 / PSS 填充签名、2048-bit+ 密钥、cryptography 库
#   - 本课用 64 位以内的教学参数，明文标注「绝不可用于生产」
# 依赖：无（标准库）
import hashlib
import secrets

print("== 扩展欧几里得求模逆 ==")
def egcd(a, b):
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = egcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)

def mod_inv(a, m):
    g, x, _ = egcd(a % m, m)
    if g != 1:
        raise ValueError(f"{a} 与 {m} 不互素")
    return x % m

print("  7⁻¹ mod 40 =", mod_inv(7, 40), "（7*23=161 ≡ 1 mod 40）")

print("\n== Miller-Rabin 素性检测 ==")
def is_prime(n, rounds=20):
    if n < 2: return False
    for small in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % small == 0:
            return n == small
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2; r += 1
    for _ in range(rounds):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True

def gen_prime(bits=32):
    while True:
        cand = secrets.randbits(bits) | (1 << (bits - 1)) | 1
        if is_prime(cand):
            return cand

for bits in (16, 24, 32):
    q = gen_prime(bits)
    print(f"  {bits}-bit 素数: {q}  素性={is_prime(q)}")

print("\n== 生成玩具 RSA 密钥 ==")
p, q = gen_prime(24), gen_prime(24)
while p == q:
    q = gen_prime(24)
n = p * q
phi = (p - 1) * (q - 1)
e = 65537
while phi % e == 0 or egcd(e, phi)[0] != 1:
    e += 2
d = mod_inv(e, phi)
print(f"  p={p}  q={q}")
print(f"  n={n} ({n.bit_length()} bit)  φ={phi}")
print(f"  公钥 (e={e}, n)  私钥 (d={d}, n)")
print("  注意：真实 RSA ≥2048 bit，这里仅 48 bit，瞬间可分解")

print("\n== 加解密（整数消息）==")
def encrypt(m, e, n): return pow(m, e, n)
def decrypt(c, d, n): return pow(c, d, n)

for m in (42, 1234, 999):
    c = encrypt(m, e, n)
    back = decrypt(c, d, n)
    print(f"  m={m:<5} -> c={c:<14} -> m'={back:<5} 一致={back == m}")
print("  确定性：同一 m 每次得到同一 c（这正是教科书 RSA 的缺陷之一）")

print("\n== 数字签名（对哈希签名，不是对消息本身）==")
def hash_int(text):
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big") % n

def sign(text, d, n):
    return pow(hash_int(text), d, n)

def verify(text, s, e, n):
    return pow(s, e, n) == hash_int(text)

msg = "转账 100 元给 Alice"
s = sign(msg, d, n)
print(f"  消息: {msg!r}")
print(f"  签名 s={s}")
print(f"  验证通过: {verify(msg, s, e, n)}")
print(f"  改金额后验证: {verify('转账 999 元给 Alice', s, e, n)}")
print(f"  改签名后验证: {verify(msg, (s + 1) % n, e, n)}")

print("\n== 签名 ≠ 加密 ==")
for line in (
    "  加密: 公钥加密，只有私钥能读（保密性）",
    "  签名: 私钥签名，任何人可用公钥验（完整性 + 不可否认）",
    "  签名前先哈希：否则长消息、 malleability、成本都成问题",
    "  真实签名用 RSA-PSS / ECDSA / Ed25519，带随机化填充",
):
    print(" ", line)

print("\n== 教科书 RSA 的漏洞 ==")
for line in [
    "  无填充 -> 相同明文相同密文，且 c1*c2 对应 m1*m2（乘法同态）",
    "  小 e / 小 m -> m^e 未超过 n 时可直接开 e 次方",
    "  共模攻击 / 低私钥指数 / 时序攻击 / 选择密文攻击",
    "  参数自造 -> p,q 太近可被费马分解，本例 48 bit 秒破",
]:
    print("  -", line)

print("\n== 混合加密（真实系统做法）==")
for line in (
    "  1) 生成随机对称密钥 K（AES-GCM / ChaCha20-Poly1305）",
    "  2) 用 K 加密大数据（快）",
    "  3) 用接收方公钥加密 K（RSA-OAEP 或 ECDH 派生）",
    "  4) 附带 MAC/认证标签，防篡改",
    "  公钥密码只处理「密钥」，对称密码处理「数据」",
):
    print(" ", line)

print("\n== 工程结论 ==")
print("  本课所有代码仅用于理解数学结构，绝不可用于任何真实系统")
print("  生产请使用 cryptography / PyNaCl 的 audited 实现")

# ===== 练习题 =====
# 1. 生成 128-bit 玩具密钥，测量加解密耗时，观察指数增长。
# 2. 实现 RSA-OAEP 的简化填充（mask + hash），验证相同明文不再相同密文。
# 3. 演示共模攻击：同一 n、两个互素 e 下，由两组密文恢复明文。
# 4. 思考：为什么签名要对「哈希」而不是对「原始消息」做模幂？
