# ===== 第913课：差分隐私与联邦学习-DP联邦聚合与成员推断 =====
# 知识点：
#   - 联邦架构隐藏数据、参数仍可能泄露 → 需要在聚合上加 DP
#   - DP-FedAvg：客户端更新截断 + 服务器加噪 → (ε,δ) 级保证
#   - 成员推断攻击（MIA）：判断「某人的数据是否被用于训练」
#   - 过拟合的模型是 MIA 的温床：成员损失低、非成员损失高
#   - DP 压低过拟合 → MIA 成功率趋近 50%（瞎猜）→ 隐私-效用二次权衡
# 依赖：无（标准库）
import math
import random


def predict(w, x):
    return w[0] * x + w[1]


def mse_one(w, x, y):
    return (predict(w, x) - y) ** 2


def mse(w, data):
    return sum(mse_one(w, x, y) for x, y in data) / len(data)


def laplace_noise(scale, rng):
    u = rng.uniform(-0.5, 0.5)
    return -math.copysign(1.0, u) * scale * math.log(1 - 2 * abs(u) + 1e-18)


def train_nonfederated(data, epochs=300, lr=0.03):
    """集中式训练（容易过拟合的对照基线）。"""
    w = [0.0, 0.0]
    n = len(data)
    for _ in range(epochs):
        grad = [0.0, 0.0]
        for x, y in data:
            err = predict(w, x) - y
            grad[0] += err * x / n
            grad[1] += err / n
        w[0] -= lr * grad[0]
        w[1] -= lr * grad[1]
    return w


def train_fedavg_dp(clients, rounds=20, epochs=2, lr=0.05,
                    clip_c=0.5, epsilon_per_round=1.0, rng=None):
    """DP-FedAvg：本地更新截断 + 服务器噪声 + 预算累加。"""
    w = [0.0, 0.0]
    history = []
    total_eps = 0.0
    for r in range(rounds):
        updates = []
        for data in clients:
            lw = [list(w)[0], list(w)[1]]
            n = len(data)
            grad = [0.0, 0.0]
            lw2 = list(w)
            for _ in range(epochs):
                grad = [0.0, 0.0]
                for x, y in data:
                    err = predict(lw2, x) - y
                    grad[0] += err * x / n
                    grad[1] += err / n
                lw2[0] -= lr * grad[0]
                lw2[1] -= lr * grad[1]
            update = [lw2[0] - w[0], lw2[1] - w[1]]
            norm = math.sqrt(update[0] ** 2 + update[1] ** 2)
            if norm > clip_c:                       # 截断到 C
                scale = clip_c / norm
                update = [update[0] * scale, update[1] * scale]
            updates.append(update)
        # 聚合：均值（n 公开）+ 噪声（敏感度 = C / 客户端数）
        sens = clip_c / len(clients)
        noise_scale = sens / epsilon_per_round
        noisy = [sum(u[i] for u in updates) / len(clients)
                 + laplace_noise(noise_scale, rng) for i in range(2)]
        w = [w[0] + noisy[0], w[1] + noisy[1]]
        total_eps += epsilon_per_round
        all_data = [item for d in clients for item in d]
        history.append((r + 1, mse(w, all_data), total_eps))
    return w, history


rng = random.Random(106)

print("== 数据：成员/非成员划分 ==")
member_data = [(x, 3.0 * x - 2.0 + rng.gauss(0, 0.8))
               for x in [rng.uniform(0, 10) for _ in range(150)]]
nonmember_data = [(x, 3.0 * x - 2.0 + rng.gauss(0, 0.8))
                  for x in [rng.uniform(0, 10) for _ in range(150)]]
print(f"  成员数据 {len(member_data)} 条（真实参与训练）")
print(f"  非成员数据 {len(nonmember_data)} 条（攻击者的『未参与』对照组）")

print("\n== 集中式训练（过拟合基线）的成员推断 ==")
w_central = train_nonfederated(member_data, epochs=300)
loss_member = sum(mse_one(w_central, x, y) for x, y in member_data) / len(member_data)
loss_nonmember = sum(mse_one(w_central, x, y) for x, y in nonmember_data) / len(nonmember_data)
print(f"  成员平均损失 = {loss_member:.4f}")
print(f"  非成员平均损失 = {loss_nonmember:.4f}")
print(f"  损失差 = {loss_nonmember - loss_member:.4f}")


def mia_accuracy(w, member_data, nonmember_data, threshold):
    tp = sum(1 for x, y in member_data if mse_one(w, x, y) < threshold)
    fp = sum(1 for x, y in nonmember_data if mse_one(w, x, y) < threshold)
    return (tp / len(member_data) + (1 - fp / len(nonmember_data))) / 2


threshold = (loss_member + loss_nonmember) / 2
acc_central = mia_accuracy(w_central, member_data, nonmember_data, threshold)
print(f"  阈值法 MIA 准确率 = {acc_central:.1%}（50% = 瞎猜）")
print("  2 参数线性模型的记忆能力有限，MIA 只能到 ~55%；")
print("  真实深度模型（可记忆训练样本）的 MIA 可达 90%+ —— 容量越大越危险")

print("\n== DP-FedAvg 的隐私-效用曲线 ==")
print(f"  {'每轮ε':>8}{'总ε':>8}{'全局MSE':>12}{'MIA准确率':>12}")
for eps_round in (8.0, 2.0, 0.5, 0.1):
    w_dp, hist = train_fedavg_dp(
        [member_data[i::5] for i in range(5)],       # 5 个客户端
        rounds=20, epochs=2, lr=0.05, clip_c=0.5,
        epsilon_per_round=eps_round, rng=rng)
    final_mse = hist[-1][1]
    lm = sum(mse_one(w_dp, x, y) for x, y in member_data) / len(member_data)
    ln = sum(mse_one(w_dp, x, y) for x, y in nonmember_data) / len(nonmember_data)
    thr = (lm + ln) / 2
    acc = mia_accuracy(w_dp, member_data, nonmember_data, thr)
    print(f"  {eps_round:>8.1f}{eps_round * 20:>8.1f}{final_mse:>12.4f}{acc:>12.1%}")
print("  ε 小（隐私强）→ MSE 高（效用差）→ MIA 掉到 ~50%（无法推断）")
print("  本例模型小、攻击面有限（55% 基线）；大模型下 ε 与 MIA 的差距会放大")
print("  这就是隐私-效用曲线的完整形态 —— 选点是业务决策不是数学决策")

print("\n== 截断范数 C 的作用 ==")
print(f"  {'截断C':>8}{'最终MSE':>12}{'说明'}")
for clip_c in (0.1, 0.5, 2.0, 8.0):
    w_c, h_c = train_fedavg_dp(
        [member_data[i::5] for i in range(5)],
        rounds=20, epochs=2, lr=0.05, clip_c=clip_c,
        epsilon_per_round=1.0, rng=rng)
    note = "过强：信息被剪光" if clip_c <= 0.1 else \
           ("合理" if clip_c <= 2.0 else "太松：噪声需求大")
    print(f"  {clip_c:>8.1f}{h_c[-1][1]:>12.4f}  {note}")
print("  C 应覆盖『正常更新』的范数：按历史上位数动态调整（自适应截断）")

print("\n== 防御的层次 ==")
for line in (
    "  架构层：联邦（数据不出域）",
    "  算法层：DP-FedAvg（参数加噪，(ε,δ) 保证）",
    "  系统层：安全聚合（服务器只见总和不见个体）+ 掉线鲁棒",
    "  审计层：隐私预算账本 + 攻击性测试（MIA 红队）",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  MIA 把『隐私威胁』变成可测量的指标：准确率离开 50% 就是泄露",
    "  DP 与 MIA 天然对偶：DP 的定义式恰好封住 MIA 的信息通道",
    "  截断与噪声是 DP-FedAvg 的两个旋钮，都需要按数据分布调",
    "  914 课：把差分隐私与联邦学习拼成完整的隐私统计平台",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「梯度反转 MIA」：训练一个分类器判断样本是否成员，对比阈值法。
# 2. 实现安全聚合的模拟：服务器只能看到 masked 之和，验证单客户端不可见。
# 3. 扫描轮数与 ε 的联合网格，绘制「效用-隐私-成本」三维权衡表。
# 4. 思考：为什么 MIA 对『泛化好的模型』几乎无效？这暗示了隐私与泛化的
#    深刻联系（记忆 vs 学习）。
