# ===== 第972课：零知识证明与承诺协议-哈希承诺与Pedersen承诺 =====
# 知识点：
#   - 承诺 = 数字信封：先锁定（commit）后揭示（open），两阶段不可反悔
#   - 隐藏性（hiding）：承诺不泄露 m；绑定性（binding）：承诺后换不了 m
#   - 哈希承诺：C = SHA256(m ∥ salt) —— salt 提供随机性
#   - Pedersen 承诺：C = g^m · h^r（模素数）—— 同态：C(m1)·C(m2) = C(m1+m2)
#   - 同态性让『密文状态下做加法』成为可能 —— 匿名投票的地基（978 课）
# 依赖：无（标准库）
import hashlib
import random


P = 10007
G = 2
# 第二个生成元 h = g^K_H。教学域里 K_H 是已知的（方便讲解）；
# 真实部署必须保证没人知道 g 与 h 之间的离散对数关系，否则绑定性失效。
K_H = 3333
H = pow(G, K_H, P)


def hash_commit(message, salt):
    """哈希承诺：SHA256(mess || salt)。salt 由承诺者保密。"""
    data = f"{message}||{salt}".encode()
    return hashlib.sha256(data).hexdigest()


def pedersen_commit(m, r, p=P, g=G, h=H):
    """Pedersen 承诺：C = g^m · h^r mod p。"""
    return (pow(g, m, p) * pow(h, r, p)) % p


def pedersen_open(commitment, m, r, p=P, g=G, h=H):
    return commitment == (pow(g, m, p) * pow(h, r, p)) % p


rng = random.Random(172)

print("== 哈希承诺 ==")
secret_vote = "yes"
salt = rng.randint(1, 2 ** 32)
commitment = hash_commit(secret_vote, salt)
print(f"  投票 = {secret_vote!r}, salt = {salt}")
print(f"  承诺 = {commitment[:16]}...（发布给所有人）")
print(f"  揭示阶段: m={secret_vote!r}, salt={salt} → "
      f"重算哈希一致: {hash_commit(secret_vote, salt) == commitment}")
tampered = hash_commit("no", salt)
print(f"  改票后重算一致: {tampered == commitment}（绑定性：换不了）")

print("\n== 哈希承诺的隐藏性依赖 salt ==")
no_salt = hashlib.sha256(b"yes").hexdigest()
print(f"  'yes' 的裸哈希 = {no_salt[:16]}...（可被字典攻击）")
print("  没有 salt → 投票空间只有 yes/no → 裸哈希直接查表破解")
print("  salt 必须足够长且随机 —— 确定性哈希承诺隐藏性的全部来源")

print("\n== Pedersen 承诺（同态）==")
m1, r1 = 25, rng.randint(1, P - 2)
m2, r2 = 17, rng.randint(1, P - 2)
c1 = pedersen_commit(m1, r1)
c2 = pedersen_commit(m2, r2)
print(f"  C(m1=25) = {c1}")
print(f"  C(m2=17) = {c2}")
c_sum = (c1 * c2) % P
print(f"  C(m1)·C(m2) mod p = {c_sum}")
r_sum = (r1 + r2) % (P - 1)
c_direct = pedersen_commit(m1 + m2, r_sum)
print(f"  C(m1+m2)      = {c_direct}")
print(f"  同态等式成立: {c_sum == c_direct}（承诺值可直接相加！）")

print("\n== Pedersen 的隐藏性与绑定性 ==")
# 隐藏性：C 是均匀分布的（因为 r 随机 → h^r 覆盖整个群）
samples = {pedersen_commit(0, rng.randint(1, P - 2)) for _ in range(2000)}
print(f"  2000 个 C(m=0) 的不同承诺值 = {len(samples)}（几乎全不同 → 隐藏）")
# 绑定性：打开到两个不同的 m 需要离散对数知识
# C = g^m1 h^r1 = g^m2 h^r2 → g^(m1-m2) = h^(r2-r1) → 需要 K_H（trapdoor）
print(f"  打开到两个值需要知道 K_H={K_H}（h 与 g 的关系）—— 承诺者不知道")
print("  所以承诺者无法作弊：绑定性建立在『不知道离散对数关系』上")

print("\n== 为什么密码学需要两个承诺方案 ==")
print(f"  {'维度':<14}{'哈希承诺':<20}{'Pedersen 承诺'}")
for row in (("计算成本", "一次哈希", "两次模幂"),
            ("同态性", "无", "有（加法同态）"),
            ("隐藏性", "统计隐藏（salt）", "完美隐藏（信息论）"),
            ("用途", "一般承诺", "投票/门限/零知识")):
    print(f"  {row[0]:<14}{row[1]:<20}{row[2]}")

print("\n== 承诺-揭示协议模板 ==")
for line in (
    "  阶段 1（commit）：所有人广播 C_i，锁死选择",
    "  阶段 2（reveal）：所有人公开 (m_i, r_i)",
    "  阶段 3（verify）：验证 C_i == commit(m_i, r_i)",
    "  应用：拍卖出价、投票、石头剪刀布、抽签排序",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  承诺 = 隐藏性（先不看）+ 绑定性（后不改）的组合",
    "  哈希承诺靠 salt，Pedersen 靠群上随机盲化 —— 两种世界观",
    "  同态性是 Pedersen 的杀手锏：密文可加 → 匿名计票",
    "  973 课：承诺 + 挑战响应 = Schnorr 识别协议",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「多人承诺拍卖」：N 个竞拍者 commit，揭示后找最高价并验证全部承诺。
# 2. 实现 Pedersen 的减法同态：C(m1) / C(m2) = C(m1 − m2)。
# 3. 实现向量承诺：对 (m1, m2, m3) 各承诺一份并验证单点揭示。
# 4. 思考：为什么 Pedersen 是『完美隐藏』而哈希承诺只是『统计隐藏』？
