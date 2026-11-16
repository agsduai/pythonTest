# ===== 第973课：零知识证明与承诺协议-Schnorr识别协议 =====
# 知识点：
#   - Schnorr 识别（Σ 协议）：证明『我知道离散对数 x』而不用出示 x
#   - 三步：承诺 R = g^k → 挑战 c → 响应 s = k + c·x (mod q)
#   - 验证方程：g^s == R · X^c —— 一行代数完成全部检查
#   - 可靠性误差 1/2：单轮作弊成功率 50%，t 轮后 (1/2)^t
#   - 诚实 Verifier 的零知识：响应 s 均匀分布，与 x 无关（模拟器可复现）
# 依赖：无（标准库）
import random


P = 10007                               # 素数域
G = 2                                   # 生成元
Q = P - 1                               # 群的阶（G^q = 1）


class SchnorrProver:
    def __init__(self, secret, rng):
        self.x = secret % Q
        self.rng = rng
        self.public_key = pow(G, self.x, P)
        self.pending_r = None
        self.pending_R = None

    def commit(self):
        """第一步：随机盲化因子 k → 承诺 R = g^k。"""
        self.pending_r = self.rng.randint(1, Q - 1)
        self.pending_R = pow(G, self.pending_r, P)
        return self.pending_R

    def respond(self, challenge):
        """第三步：响应 s = k + c·x mod Q。"""
        s = (self.pending_r + challenge * self.x) % Q
        return s


def schnorr_verify(public_key, R, challenge, response):
    """验证方程：g^s == R · X^c (mod P)。"""
    lhs = pow(G, response, P)
    rhs = (R * pow(public_key, challenge, P)) % P
    return lhs == rhs


rng = random.Random(173)
prover = SchnorrProver(secret=1234, rng=rng)
public_key = prover.public_key

print("== 协议参数 ==")
print(f"  公钥 X = G^x mod P = {public_key}（秘密 x = 1234 绝不出现）")

print("\n== 完整的一轮交互 ==")
R = prover.commit()
print(f"  ① Prover 承诺: R = G^k = {R}")
challenge = rng.randint(1, Q - 1)
print(f"  ② Verifier 挑战: c = {challenge}")
s = prover.respond(challenge)
print(f"  ③ Prover 响应: s = k + c·x mod Q = {s}")
ok = schnorr_verify(public_key, R, challenge, s)
print(f"  ④ 验证: g^s == R·X^c -> {ok}")

print("\n== 代数原理：为什么验证方程成立 ==")
print(f"  g^s = g^(k + c·x) = g^k · (g^x)^c = R · X^c")
print("  响应里藏着 x，但被 k 盲化 —— Verifier 能验证却推不出 x")

print("\n== 可靠性：作弊者的困境 ==")


def cheating_prover(rng, x_pub):
    """作弊者不掌握 x：先随机选 s，再按『猜的挑战 c_guess』反推 R，
    使 g^s = R·X^c_guess 成立。只有当真实挑战 c 恰好等于 c_guess 才通过。"""
    s = rng.randint(1, Q - 1)
    c_guess = rng.randint(1, Q - 1)
    # R = g^s · X^(-c_guess)
    X_inv_c = pow(pow(x_pub, c_guess, P), P - 2, P)
    R = (pow(G, s, P) * X_inv_c) % P
    return R, s, c_guess


rng2 = random.Random(174)
success = 0
trials = 2000
for _ in range(trials):
    R, s, c_guess = cheating_prover(rng2, public_key)
    c_real = rng2.randint(1, Q - 1)      # 真实挑战（在作弊者之后随机）
    if schnorr_verify(public_key, R, c_real, s):
        success += 1
print(f"  作弊者 {trials} 轮的通过率 = {success / trials:.1%}"
      f"（需要精确猜中挑战，概率 ≈ 1/Q = {1 / Q:.4%}）")
print("  这是『先定 s 再被挑战』的作弊路线 —— 猜中概率极低")
print("  另一条路线『先看挑战再定 s』：需要解离散对数，同样不可行")

print("\n== 经典可靠性论证：作弊者只能二选一 ==")


def cheating_two_way(rng, x_pub, commit_first=True):
    """作弊者要么先定 R（则答不出 c），要么先定 s（则要猜 c）。
    这里模拟『先定 s，赌 c』路线，展示 1/Q 的猜中率。"""
    s = rng.randint(1, Q - 1)
    c_guess = rng.randint(1, Q - 1)
    X_inv_c = pow(pow(x_pub, c_guess, P), P - 2, P)
    R = (pow(G, s, P) * X_inv_c) % P
    return R, s, c_guess


# 更贴近教科书的演示：把挑战空间缩到 {0,1}，作弊率就是 50%
SMALL_Q = 2
hits_small = 0
for _ in range(2000):
    c_guess = rng2.randint(0, SMALL_Q - 1)
    c_real = rng2.randint(0, SMALL_Q - 1)
    hits_small += (c_guess == c_real)
print(f"  挑战空间={{0,1}} 时猜中率 = {hits_small / 2000:.1%}（理论 50%）")
print(f"  挑战空间=Q={Q} 时猜中率 = {success / trials:.1%}（理论 1/Q）")
print("  t 轮独立挑战：(1/2)^t 或 (1/Q)^t —— 都是指数级压制")
print("  教科书用 {0,1} 挑战（比特挑战）是为了让 1/2 这个数字好记")

print("\n== 零知识：响应与秘密统计独立 ==")
prover2 = SchnorrProver(secret=42, rng=random.Random(175))
prover3 = SchnorrProver(secret=9999, rng=random.Random(176))
resp_dist = {"secret=42": [], "secret=9999": []}
for _ in range(500):
    R2 = prover2.commit()
    resp_dist["secret=42"].append(prover2.respond(rng.randint(1, Q - 1)))
    R3 = prover3.commit()
    resp_dist["secret=9999"].append(prover3.respond(rng.randint(1, Q - 1)))
mean42 = sum(resp_dist["secret=42"]) / 500
mean9999 = sum(resp_dist["secret=9999"]) / 500
print(f"  秘密=42 的响应均值 ≈ {mean42:.0f}")
print(f"  秘密=9999 的响应均值 ≈ {mean9999:.0f}")
print(f"  两者都接近 Q/2 = {Q / 2:.0f} —— 响应是均匀随机的，不含秘密信息")
print("  『模拟器』可以生成同样分布的对话 —— 这就是零知识的定义")

print("\n== 诚实验证者假设 ==")
print("  协议要求挑战 c 由验证者随机选取 —— 若 Prover 自己选 c：")
print("    提前算好 s = k + c·x 对任意 c 成立 → 可伪造！")
print("  所以交互性本身是安全性的一部分（974 课用 Fiat-Shamir 替代交互）")

print("\n== Σ 协议的通用结构 ==")
for line in (
    "  承诺（commit）: 用随机盲化因子锁定一个姿态",
    "  挑战（challenge）: 验证者随机提问",
    "  响应（response）: 用秘密计算答案",
    "  验证（verify）: 代数等式一行检查",
    "  Schnorr/Sigma/Guillou-Quisquater 都是同一骨架的变体",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  Schnorr = 离散对数上的 Σ 协议：一次模幂承诺 + 一次线性响应",
    "  验证方程 g^s = R·X^c 是代数恒等式，不依赖任何秘密",
    "  可靠性靠随机挑战，零知识靠均匀盲化 —— 缺一不可",
    "  974 课：用 Fiat-Shamir 把交互协议变成数字签名",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 t 轮 Schnorr 的作弊成功率曲线（t=1..10），验证指数衰减。
# 2. 实现『多秘密批量证明』：一次交互同时证明两个不同秘密（线性组合响应）。
# 3. 验证响应 s 的分布：卡方检验响应值是否均匀覆盖 [1, Q)。
# 4. 思考：为什么响应必须 mod Q（群的阶）而不是 mod P？
