# ===== 第971课：零知识证明与承诺协议-模运算与交互证明 =====
# 知识点：
#   - 零知识证明（ZKP）：证明者让验证者相信『我知道 X』而不泄露 X 本身
#   - 三性质：完备性（诚实必过）、可靠性（作伪难过）、零知识（不泄露）
#   - 交互证明：Prover 与 Verifier 对话，挑战-响应模式
#   - 模运算复习：乘法群、生成元、离散对数（76 章 RSA 的数学地基）
#   - 教学域：小素数域上模拟 —— 算法与真实椭圆曲线完全同构
# 依赖：无（标准库）
import random


P = 10007                                # 素数域（教学规模）
G = 2                                    # 生成元（乘法群的底）

assert all(P % i != 0 for i in range(2, int(P ** 0.5) + 1)), "P 必须是素数"


def mod_pow(base, exp, mod=P):
    return pow(base, exp, mod)


def mod_inv(a, mod=P):
    """扩展欧几里得求逆元（76 章 egcd 的应用）。"""
    def egcd(a, b):
        if b == 0:
            return a, 1, 0
        g, x, y = egcd(b, a % b)
        return g, y, x - (a // b) * y
    g, x, _ = egcd(a % mod, mod)
    if g != 1:
        raise ValueError(f"{a} 在模 {mod} 下无逆元")
    return x % mod


def find_generator(p):
    """找乘法群生成元：g^k 遍历 1..p-1。"""
    for g in range(2, p):
        seen = set()
        cur = 1
        for _ in range(p - 1):
            cur = cur * g % p
            seen.add(cur)
        if len(seen) == p - 1:
            return g
    return None


print("== 域参数 ==")
P = 10007                                # 保持与文件头一致
G = find_generator(P)
print(f"  素数域 P = {P}")
print(f"  生成元 G = {G}（G^1..G^(P-1) 覆盖整个乘法群）")
order_check = len({mod_pow(G, k) for k in range(1, P)}) == P - 1
print(f"  生成元验证: {order_check}")

print("\n== 离散对数：单向函数 ==")
secret = 1234
public = mod_pow(G, secret)
print(f"  已知 G={G}, secret={secret} → 公钥 {public}（快速）")
brute = None
for k in range(1, 2000):
    if mod_pow(G, k) == public:
        brute = k
        break
print(f"  反向暴力求 secret：{brute}（教学域可暴力；真实域 2^256 不可行）")
print("  单向性 = 正向容易、反向不可行 —— 所有现代密码学的地基")

print("\n== 交互证明的角色 ==")
for line in (
    "  Prover（证明者）：掌握秘密 w，要证明『我知道 w』",
    "  Verifier（验证者）：随机挑战，检查响应是否成立",
    "  随机挑战 = 验证者的武器：让预先准备的答案失效",
    "  交互轮数越多 → 作弊成功率指数衰减",
):
    print("  -", line)

print("\n== 完备性/可靠性/零知识 三性质 ==")
print(f"  {'性质':<12}{'要求':<34}{'谁受益'}")
for row in (("完备性", "诚实的 Prover 必然通过", "Prover"),
            ("可靠性", "作弊的 Prover 被抓", "Verifier"),
            ("零知识", "Verifier 学不到 w 本身", "Prover")):
    print(f"  {row[0]:<12}{row[1]:<34}{row[2]}")
print("  三者的张力：越可靠越容易泄露，越零知识越难验证 —— 协议设计的艺术")

print("\n== 简单示例：数独『口述证明』的思想实验 ==")
print("  甲知道数独解法：")
print("    1. 甲把解抄到纸条扣在桌上（承诺）")
print("    2. 乙随机喊『给我看第 3 行』（挑战）")
print("    3. 甲翻开第 3 行（响应），乙检查 1-9 无重复")
print("  重复 30 次：乙确信甲会解（可靠性），但从未看到完整解（零知识）")

print("\n== 小结 ==")
for line in (
    "  ZKP = 密码学证明论：把『我告诉你』变成『我自己去验证』",
    "  模乘法群是 ZKP 的舞台：离散对数的单向性是安全性来源",
    "  挑战-响应 + 随机性 = 交互证明的基本节奏",
    "  972 课：承诺方案 —— ZKP 的第一块积木",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现『乘法群阶验证』：给候选 g，返回其生成的子群大小。
# 2. 用费马小定理实现快速逆元（a^(p-2) mod p），与扩展欧几里得结果对账。
# 3. 测量暴力离散对数的时间随 P 的增长曲线（P=1009/10007/100003）。
# 4. 思考：为什么『证明』需要交互？一次性给出完整证明为什么不安全？
