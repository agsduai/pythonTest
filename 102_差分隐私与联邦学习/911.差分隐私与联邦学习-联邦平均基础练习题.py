# ===== 第911课：差分隐私与联邦学习-联邦平均基础 =====
# 知识点：
#   - 联邦学习：数据不出本地，只上传模型参数/梯度 —— 架构级隐私
#   - FedAvg：客户端本地训练 E 步 → 上传参数 → 服务器按样本量加权平均
#   - 与集中式训练对照：IID 数据下 FedAvg 几乎无损
#   - 客户端参与率、本地轮数 E 是 FedAvg 的关键旋钮
#   - 架构级隐私 ≠ 数学级隐私：参数本身可能泄露（913 课再加 DP）
# 依赖：无（标准库）
import math
import random


def linear_model_prediction(w, x):
    return w[0] * x + w[1]


def mse(w, data):
    return sum((linear_model_prediction(w, x) - y) ** 2 for x, y in data) / len(data)


def local_train(w, data, epochs=5, lr=0.02):
    """本地梯度下降若干轮。"""
    w = list(w)
    n = len(data)
    for _ in range(epochs):
        for x, y in data:
            err = linear_model_prediction(w, x) - y
            w[0] -= lr * err * x / n
            w[1] -= lr * err / n
    return w


def centralized_train(all_data, epochs=40, lr=0.05):
    w = [0.0, 0.0]
    n = len(all_data)
    for _ in range(epochs):
        for x, y in all_data:
            err = linear_model_prediction(w, x) - y
            w[0] -= lr * err * x / n
            w[1] -= lr * err / n
    return w


def fedavg(clients_data, rounds=10, local_epochs=5, participation=1.0, rng=None):
    w = [0.0, 0.0]
    history = []
    for r in range(rounds):
        participants = list(clients_data)
        if rng is not None and participation < 1.0:
            k = max(1, int(len(clients_data) * participation))
            participants = rng.sample(list(clients_data), k)
        new_w = [0.0, 0.0]
        total_weight = 0
        for data in participants:
            lw = local_train(w, data, local_epochs)
            weight = len(data)
            for i in range(2):
                new_w[i] += lw[i] * weight
            total_weight += weight
        for i in range(2):
            new_w[i] /= total_weight
        w = new_w
        # 全量评估
        all_data = [item for data in clients_data for item in data]
        history.append((r + 1, mse(w, all_data)))
    return w, history


rng = random.Random(104)

print("== 数据生成：5 个客户端，IID 分布 ==")
clients_iid = [[(x, 3.0 * x - 2.0 + rng.gauss(0, 1.0))
                for x in [rng.uniform(0, 10) for _ in range(200)]]
               for _ in range(5)]
all_iid = [item for d in clients_iid for item in d]
print(f"  5 客户端 × 200 样本，同一分布 y = 3x − 2 + N(0,1)")
print(f"  集中式训练 40 轮: w = {[round(v, 3) for v in centralized_train(all_iid)]}")

print("\n== FedAvg（全参与）==")
w_fed, hist = fedavg(clients_iid, rounds=10, local_epochs=5)
print(f"  {'轮':>4}{'全局 MSE':>12}")
for r, e in hist[::2]:
    print(f"  {r:>4}{e:>12.4f}")
print(f"  FedAvg 最终 w = {[round(v, 3) for v in w_fed]}")
print(f"  集中式 MSE = {mse(centralized_train(all_iid), all_iid):.4f}  "
      f"FedAvg MSE = {hist[-1][1]:.4f}")
print("  IID 场景：联邦几乎无损 —— 理想情况")

print("\n== 本地轮数 E 的权衡 ==")
print(f"  {'本地轮数E':>10}{'10轮后MSE':>12}")
for E in (1, 5, 20, 50):
    w_e, h_e = fedavg(clients_iid, rounds=10, local_epochs=E)
    print(f"  {E:>10}{h_e[-1][1]:>12.4f}")
print("  E 太小 → 通信开销大；E 太大 → 本地过拟合漂移（IID 下影响小，下一课放大）")

print("\n== 部分参与：掉线与采样 ==")
w_part, hist_part = fedavg(clients_iid, rounds=10, local_epochs=5,
                           participation=0.4, rng=rng)
print(f"  参与率 40%: 最终 MSE = {hist_part[-1][1]:.4f}（全参与 {hist[-1][1]:.4f}）")
print("  部分参与省带宽、抗掉线，收敛稍慢 —— 手机端联邦的真实设定")

print("\n== 通信量对比 ==")
model_size = 2                                     # 两个参数
rounds = 10
fed_comm = rounds * 5 * model_size                 # 每轮上传+下载
central_comm = 0                                   # 数据上传：一次性
print(f"  FedAvg 通信 = {fed_comm} 个参数（{rounds} 轮 × 5 客户端 × 2 参数）")
print(f"  集中式上传 = {len(all_iid)} 条样本")
print("  样本量大时 FedAvg 通信占优；模型大时（百万参数）通信才是瓶颈")
print("  对策：梯度压缩、稀疏化、量化上传")

print("\n== 联邦的隐私边界 ==")
for line in (
    "  不上传原始数据 → 管理员看不到样本（架构级保护）",
    "  但参数/梯度本身可能泄露：可从梯度反推样本（深度泄漏梯度攻击）",
    "  聚合前的参数也可被恶意服务器逐客户端分析",
    "  结论：联邦 = 减少暴露面；要数学保证还需 DP（913 课）+ 安全聚合",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  FedAvg = 本地训练 + 加权平均，IID 时逼近集中式",
    "  三个旋钮：本地轮数 E、参与率、轮数 —— 权衡通信与收敛",
    "  联邦学习是隐私的『必要条件』而非『充分条件』",
    "  912 课：真实世界的非 IID 数据会让 FedAvg 暴露弱点",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「动量版 FedAvg」：服务器聚合时带动量项，对比收敛速度。
# 2. 实现加权 vs 等权聚合的对比实验（客户端样本量差异大时哪个好）。
# 3. 模拟客户端「掉队」（每轮随机跳过），统计完成时间与最终精度的关系。
# 4. 思考：为什么本地训练 E 步过多会导致「客户端漂移」？在 IID 与非 IID
#    下漂移的影响有何不同？
