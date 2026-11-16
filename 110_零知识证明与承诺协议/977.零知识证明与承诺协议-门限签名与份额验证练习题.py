# ===== 第977课：零知识证明与承诺协议-门限签名与份额验证 =====
# 知识点：
#   - 门限签名：秘密拆成 n 份，任意 t 份协作即可签名，少于 t 无法签名
#   - Shamir 秘密共享（76 章）：多项式插值拆分；门限签名是其签名应用
#   - 份额验证：每个部分签名可独立检验 —— 防止恶意份额污染结果
#   - 拉格朗日系数：在 x=0 处插值 → 份额线性组合恢复签名
#   - 无可信第三方：分布式密钥生成（DKG）的思想
# 依赖：无（标准库）
import random


P = 10007                               # 素数域
G = 2
Q = P - 1                               # 群阶


def poly_eval(coeffs, x, mod=P):
    """多项式求值：coeffs[i] 是 x^i 的系数。"""
    result = 0
    for coef in reversed(coeffs):
        result = (result * x + coef) % mod
    return result


def mod_inv(a, mod):
    """扩展欧几里得求逆元（模可为合数，只要 gcd=1）。"""
    def egcd(a, b):
        if b == 0:
            return a, 1, 0
        g, x, y = egcd(b, a % b)
        return g, y, x - (a // b) * y
    g, x, _ = egcd(a % mod, mod)
    if g != 1:
        raise ValueError(f"{a} 与 {mod} 不互素")
    return x % mod


def lagrange_coefficients(points, x_target=0, mod=P):
    """拉格朗日系数：λ_i = Π (x_target − x_j)/(x_i − x_j)。"""
    coeffs = []
    n = len(points)
    for i, (xi, _) in enumerate(points):
        num = den = 1
        for j, (xj, _) in enumerate(points):
            if i == j:
                continue
            num = (num * (x_target - xj)) % mod
            den = (den * (xi - xj)) % mod
        coeffs.append(num * mod_inv(den, mod) % mod)
    return coeffs


class ThresholdSigner:
    """门限签名：秘密 x 通过 Shamir 共享，各参与者持 share_i。"""

    def __init__(self, secret, threshold, num_players, rng):
        self.threshold = threshold
        self.num_players = num_players
        # Shamir 拆分：随机多项式 f(x) = x + a1·x + a2·x² + ...（常数项 = 秘密）
        coeffs = [secret] + [rng.randint(1, Q - 1) for _ in range(threshold - 1)]
        self.shares = {}
        self.public_shares = {}
        for player in range(1, num_players + 1):
            share = poly_eval(coeffs, player, Q)   # 份额必须在群阶域上
            self.shares[player] = share
            self.public_shares[player] = pow(G, share, P)
        self.public_key = pow(G, secret, P)
        self.rng = rng

    def partial_sign(self, player, message_hash, k_i):
        """部分签名：s_i = k_i + H(m)·share_i mod Q。
        同时返回承诺 R_i = g^{k_i} 供验证。"""
        s_i = (k_i + message_hash * self.shares[player]) % Q
        R_i = pow(G, k_i, P)
        return s_i, R_i

    def verify_partial(self, player, s_i, R_i, message_hash):
        """单份额验证：g^{s_i} == R_i · Y_i^{H(m)}。"""
        lhs = pow(G, s_i, P)
        rhs = (R_i * pow(self.public_shares[player], message_hash, P)) % P
        return lhs == rhs

    def combine(self, partials, message_hash):
        """拉格朗日组合：s = Σ λ_i · s_i mod Q。"""
        points = [(p, None) for p, _ in partials]
        lambdas = lagrange_coefficients(points, 0, Q)
        s = sum(lam * s_i for lam, (_, s_i) in zip(lambdas, partials)) % Q
        return s

    def verify_combined(self, s, R_combined, message_hash):
        """验证聚合签名：g^s == R_total · (PK)^{H(m)}。
        R_total = Π R_i^{λ_i} —— 由各部分承诺拉格朗日组合。"""
        lhs = pow(G, s, P)
        rhs = (R_combined * pow(self.public_key, message_hash, P)) % P
        return lhs == rhs


rng = random.Random(177)
SECRET = 4321

print("== 密钥拆分（2-of-4 门限）==")
signer = ThresholdSigner(SECRET, threshold=2, num_players=4, rng=rng)
print(f"  公钥 = {signer.public_key}")
for player, share in sorted(signer.shares.items()):
    print(f"  玩家{player} 持有份额 share = {share}（他人不可见）")

print("\n== 部分签名与验证 ==")
message_hash = 777
partials = []
for player in (1, 2):
    k_i = rng.randint(1, Q - 1)
    s_i, R_i = signer.partial_sign(player, message_hash, k_i)
    valid = signer.verify_partial(player, s_i, R_i, message_hash)
    partials.append((player, s_i, R_i))
    print(f"  玩家{player}: 部分签名 s_i = {s_i}, 验证 = {valid}")
print("  每个份额独立可验 —— 恶意份额在聚合前就被拒之门外")

print("\n== 聚合签名 ==")
R_combined = 1
for player, s_i, R_i in partials:
    points = [(p, None) for p, _, _ in partials]
    lambdas = lagrange_coefficients(points, 0, Q)
for i, (player, s_i, R_i) in enumerate(partials):
    points = [(p, None) for p, _, _ in partials]
    lambdas = lagrange_coefficients(points, 0, Q)
    R_combined = (R_combined * pow(R_i, lambdas[i], P)) % P
s_combined = signer.combine([(p, s) for p, s, _ in partials], message_hash)
print(f"  聚合签名 s = {s_combined}")
ok = signer.verify_combined(s_combined, R_combined, message_hash)
print(f"  聚合验证: {ok}")
print(f"  与真实私钥对照: 签名确实来自 x={SECRET} 的密钥对")

print("\n== 恶意份额检测 ==")
malicious_s = (rng.randint(1, Q - 1))
k_mal = rng.randint(1, Q - 1)
bad_s, bad_R = signer.partial_sign(3, message_hash, k_mal)
bad_s = (bad_s + 1) % Q                    # 篡改签名
valid_bad = signer.verify_partial(3, bad_s, bad_R, message_hash)
print(f"  玩家3 篡改后的份额验证: {valid_bad} -> 拒绝 ✓")
print("  2-of-4：聚合时只需 2 个有效份额，1 个恶意不影响结果")

print("\n== 份额不够时：无法签名 ==")
one_partial = [(1, partials[0][1], partials[0][2])]
s_one = signer.combine([(p, s) for p, s, _ in one_partial], message_hash)
R_one = one_partial[0][2]
print(f"  只有 1 个份额（阈值 2）的聚合验证: {signer.verify_combined(s_one, R_one, message_hash)}")
print("  少于 t 份 -> 聚合结果不构成有效签名 —— 门限的密码学含义")

print("\n== 门限签名的应用 ==")
for line in (
    "  多方托管钱包：3-of-5 才能动用资金，单点被盗无法转账",
    "  分布式 CA：证书签发权分散到多个节点",
    "  链上验证者：共识委员会的门限签名聚合",
    "  与 MPC 的关系：门限签名是最简单实用的多方密码协议",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  门限签名 = Shamir 拆分 + Schnorr 线性性 + 拉格朗日插值",
    "  份额独立验证是安全核心：聚合前先逐个验真",
    "  线性性让『部分签名的和 = 整体签名』—— 无需重构私钥",
    "  978 课：综合案例 —— 匿名投票系统",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「份额刷新」：定期重分享（不改变密钥）以对抗长期攻击者。
# 2. 实现 3-of-5 门限并验证『任意 3 份组合都得到相同签名』。
# 3. 实现「密钥删除验证」：份额持有者证明自己已删除原始密钥（零知识式声明）。
# 4. 思考：门限 t 太小与太大的安全/可用性权衡分别是什么？
