# ===== 第974课：零知识证明与承诺协议-FiatShamir与数字签名 =====
# 知识点：
#   - Fiat-Shamir 变换：用哈希(R, message) 替代 Verifier 的随机挑战
#   - 交互协议 → 非交互签名：Prover 自己算挑战，任何人可验证
#   - 随机预言机模型：哈希被理想化为真随机函数 —— 安全性的标准假设
#   - Schnorr 签名 = Schnorr 识别 + Fiat-Shamir —— Bitcoin 用的签名
#   - 防重放：消息绑进挑战 → 换消息就是换挑战 → 签名不可移植
# 依赖：无（标准库）
import hashlib
import random


P = 10007
G = 2
Q = 5003                                 # G=2 的阶是 (P-1)/2 = 5003（素数）

assert pow(G, Q, P) == 1 and Q != 1, "G 的阶必须是 Q"


def challenge_hash(R, message, prefix=""):
    """Fiat-Shamir 挑战：c = H(R ∥ message) mod Q。"""
    data = f"{prefix}|{R}|{message}".encode()
    return int(hashlib.sha256(data).hexdigest(), 16) % Q


class SchnorrSignature:
    def __init__(self, secret, rng):
        self.x = secret % Q
        self.public_key = pow(G, self.x, P)
        self.rng = rng

    def sign(self, message):
        """签名：承诺 → 哈希挑战 → 响应。"""
        k = self.rng.randint(1, Q - 1)
        R = pow(G, k, P)
        c = challenge_hash(R, message)
        s = (k + c * self.x) % Q
        return {"R": R, "s": s, "message": message}

    def verify(self, signature):
        """任何人可验证：挑战由哈希重算，不需 Prover 在场。"""
        R, s, message = signature["R"], signature["s"], signature["message"]
        c = challenge_hash(R, message)
        lhs = pow(G, s, P)
        rhs = (R * pow(self.public_key, c, P)) % P
        return lhs == rhs


print("== 交互版 vs 非交互版 ==")
print(f"  {'维度':<14}{'交互识别':<22}{'Fiat-Shamir 签名'}")
for row in (("挑战来源", "Verifier 随机发", "哈希(R, message)"),
            ("参与方", "双方在线", "签名后离线可验"),
            ("复用性", "每次都要交互", "一次签名，无限次验证"),
            ("产物", "无（对话消失）", "可传输的签名对象")):
    print(f"  {row[0]:<14}{row[1]:<22}{row[2]}")

print("\n== 签名与验证 ==")
rng = random.Random(174)
signer = SchnorrSignature(1234, rng)
message = "转账 100 元给 Bob"
sig = signer.sign(message)
print(f"  消息: {message!r}")
print(f"  签名: R = {sig['R']}, s = {sig['s']}")
print(f"  验证: {signer.verify(sig)}")

print("\n== 篡改检测 ==")
# 改消息
sig_tampered = dict(sig)
sig_tampered["message"] = "转账 99999 元给 Bob"
print(f"  改消息后验证: {signer.verify(sig_tampered)}"
      f"（挑战随消息变化 → 等式破坏）")
# 改响应
sig_tampered2 = dict(sig)
sig_tampered2["s"] = (sig["s"] + 1) % Q
print(f"  改响应后验证: {signer.verify(sig_tampered2)}")

print("\n== 为什么作弊者仍然无能为力 ==")
print("  作弊者想签任意消息：需要 s 使 g^s = R·X^c 且 c = H(R, msg)")
print("  流程：先选 R → c 被哈希锁定 → 解 s 需要离散对数 x —— 死路")
print("  先选 s → 反推 R 需要满足哈希关系 —— 同样死路")
print("  『先承诺后被锁』的顺序与交互版完全一致 —— 这就是 Fiat-Shamir 的魔法")

print("\n== 重放保护：消息绑定 ==")
sig_moved = dict(sig)
sig_moved["message"] = "转账 100 元给 Alice"          # 拿旧签名签新消息
print(f"  把签名挪到另一条消息: {signer.verify(sig_moved)}")
print("  挑战哈希包含消息 → 换消息 = 换挑战 → 签名不可移植")
print("  交易签名里还嵌入链 ID / nonce → 跨链重放也被阻止")

print("\n== 随机数 k 的致命重要性 ==")
print("  两个签名共用同一个 k：")
rng2 = random.Random(175)
k_reused = 777
def sign_with_k(message, x):
    R = pow(G, k_reused, P)
    c = challenge_hash(R, message)
    s = (k_reused + c * x) % Q
    return R, s, c
sig1 = sign_with_k("消息一", 1234)
sig2 = sign_with_k("消息二", 1234)
# s1 - s2 = c1·x - c2·x = x(c1 - c2) → x = (s1-s2)/(c1-c2)
c1, c2 = sig1[2], sig2[2]
s1, s2 = sig1[1], sig2[1]


def mod_inv(a, mod):
    """扩展欧几里得求逆（Q=10006 是合数，不能用费马小定理）。"""
    def egcd(a, b):
        if b == 0:
            return a, 1, 0
        g, x, y = egcd(b, a % b)
        return g, y, x - (a // b) * y
    g, x, _ = egcd(a % mod, mod)
    if g != 1:
        raise ValueError(f"{a} 与 {mod} 不互素")
    return x % mod


recovered_x = ((s1 - s2) * mod_inv(c1 - c2, Q)) % Q
print(f"  私钥 x = 1234，从两个共用 k 的签名恢复出: {recovered_x}")
print("  私钥泄露！这就是索尼 PS3 被破解的原因 —— k 必须每次全新随机")
print("  注意：Q 是合数，逆元必须用扩展欧几里得（费马小定理只对素数模成立）")

print("\n== 真实世界的 Schnorr ==")
for line in (
    "  Bitcoin Taproot：Schnorr 签名取代 ECDSA（线性 → 可聚合）",
    "  多签聚合：n 个签名合成 1 个（线性性），节省链上空间",
    "  EdDSA（Ed25519）= Schnorr 思想 + Ed 曲线 —— 现代 TLS/SSH 在用",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  Fiat-Shamir 把『信任验证者随机』换成『信任哈希不可预测』",
    "  消息绑进挑战 → 签名同时承担认证与完整性",
    "  k 重用 = 私钥泄露 —— 随机数质量是签名安全的一半",
    "  975 课：更纯粹的零知识 —— 图三着色协议",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「批量验证」：多签名的合并验证 g^(Σs) == Π(R·X^c)。
# 2. 实现「前缀域分离」：不同用途用不同 prefix（签名/身份/投票），验证
#    跨用途重放被阻止。
# 3. 统计 1000 个签名的 s 分布，验证均匀性（数值区间直方图）。
# 4. 思考：Fiat-Shamir 在编程实现中最常见的漏洞是什么？（提示：忘记把
#    所有公共输入包含进哈希）
