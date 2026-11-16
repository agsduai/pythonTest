# ===== 第703课：密码学协议进阶-Shamir秘密共享 =====
# 知识点：
#   - (k, n) 门限：把秘密拆成 n 份，任意 k 份可恢复，少于 k 份一无所知
#   - 原理：k-1 次多项式 f(x)，f(0)=秘密；k 个点唯一确定多项式
#   - 拉格朗日插值在有限域 GF(p) 上做（p 为素数且 > 秘密与 n），避免浮点误差
#   - 模逆用费马小定理 pow(a, p-2, p) 或扩展欧几里得
#   - 少于 k 份时，每个可能的秘密都存在一个一致的多项式 -> 信息论安全
#   - 本课为教学实现：无认证、无可验证性，生产用 SSKR / VSS 方案
# 依赖：无（标准库）
import secrets

P = 2**127 - 1        # 梅森素数，足够大的有限域（教学用）


def mod_inv(a, p=P):
    return pow(a % p, p - 2, p)


def split(secret: int, k: int, n: int, p=P):
    """把 secret 拆成 n 个 (x, y) 份额。"""
    if not 1 <= k <= n < p:
        raise ValueError("需满足 1 <= k <= n < p")
    if secret >= p:
        raise ValueError("秘密必须小于 p")
    coeffs = [secret] + [secrets.randbelow(p - 1) + 1 for _ in range(k - 1)]
    def f(x):
        y = 0
        for power, c in enumerate(coeffs):
            y = (y + c * pow(x, power, p)) % p
        return y
    return [(x, f(x)) for x in range(1, n + 1)]


def recover(shares, p=P):
    """拉格朗日插值求 f(0)。"""
    k = len(shares)
    total = 0
    for i, (xi, yi) in enumerate(shares):
        num = den = 1
        for j, (xj, _) in enumerate(shares):
            if i == j:
                continue
            num = num * (-xj) % p
            den = den * (xi - xj) % p
        total = (total + yi * num % p * mod_inv(den, p)) % p
    return total % p


SECRET = 20261114
k, n = 3, 5
shares = split(SECRET, k, n)
print(f"== 拆分：秘密={SECRET}，门限 (k={k}, n={n}) ==")
for x, y in shares:
    print(f"  份额 {x}: ({x}, {y})")

print("\n== 任意 k 份可恢复 ==")
subsets = [
    shares[:3], shares[2:5], [shares[0], shares[2], shares[4]],
    [shares[4], shares[1], shares[3]],
]
for sub in subsets:
    got = recover(sub)
    print(f"  用份额 {[x for x, _ in sub]} -> {got}  正确={got == SECRET}")

print("\n== 少于 k 份无法恢复 ==")
for sub in (shares[:1], shares[:2], [shares[0], shares[3]]):
    # 只取子集做「插值」会得到某个值，但它不是唯一的真秘密
    fake = recover(sub)
    print(f"  用份额 {[x for x, _ in sub]} 插值得到 {fake}（不是秘密，且无法判断真伪）")
print("  信息论安全：任意候选秘密都能配上一条一致的多项式")

print("\n== 为什么 2 份不够（k=3）：任意候选秘密都自洽 ==")
# 给定 2 个点与任意候选 s，总能在有限域里解出 a1,a2 使二次多项式过这三点
(x1, y1), (x2, y2) = shares[0], shares[1]
for candidate in (0, 1, 999, SECRET):
    r1, r2 = (y1 - candidate) % P, (y2 - candidate) % P
    # 解 [x1 x1²; x2 x2²] · [a1,a2]ᵀ = [r1,r2]ᵀ
    det = (x1 * x2 * x2 - x2 * x1 * x1) % P
    a1 = (r1 * x2 * x2 - r2 * x1 * x1) * mod_inv(det) % P
    a2 = (x1 * r2 - x2 * r1) * mod_inv(det) % P
    # 用解出的多项式回代验两点
    ok = all((a1 * x + a2 * x * x + candidate) % P == y
             for x, y in ((x1, y1), (x2, y2)))
    print(f"  候选秘密 {candidate:>10}: 存在一致多项式={ok}")
print("  -> 少于 k 份时，任何猜测都自洽，攻击者得不到任何信息")

print("\n== 份额泄露/损坏的影响 ==")
corrupted = list(shares[:3])
corrupted[2] = (corrupted[2][0], (corrupted[2][1] + 1) % P)
print(f"  改动 1 个份额后恢复 = {recover(corrupted)}（错误）")
print("  基础 Shamir 无校验：需要可验证秘密共享（VSS）或额外 MAC")

print("\n== 动态门限与刷新 ==")
for line in (
    "  提高门限: 用新随机多项式重新拆分（原份额作废）",
    "  份额刷新: 保持 f(0) 不变，给每个份额加同一条零常数多项式",
    "  撤销某人: 刷新后不给该人新份额，旧份额自动失效",
    "  这些操作都不需要重建原始秘密",
):
    print(" ", line)

print("\n== 应用场景 ==")
for line in [
    "  密钥托管 / 恢复码分片 / 多方签名阈值",
    "  磁盘加密的恢复密钥拆分给多位管理员",
    "  区块链阈值签名（TSS）、分布式密钥生成（DKG）",
    "  与第72章工作流结合：审批门限 = 需要 k 个管理员份额",
]:
    print("  -", line)

print("\n== 工程注意 ==")
for line in [
    "  p 必须大于所有可能的秘密与份额数；真实用 256-bit 素数",
    "  系数用 CSPRNG（secrets），不能用 random",
    "  份额本身要加密存储 + 认证，防止篡改与关联",
    "  生产用 audited 库（如 Shamir39/SSKR），本课是原理版",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现份额刷新：保持秘密不变，给大家发新份额，验证旧份额失效。
# 2. 给每个份额加 HMAC 校验，实现「可验证」的恢复（检测被改的份额）。
# 3. 把秘密换成一段 UTF-8 文本（先转整数），验证拆分/恢复无损。
# 4. 思考：为什么必须在有限域上做插值，而不是普通浮点多项式？
