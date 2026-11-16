# ===== 第912课：差分隐私与联邦学习-非IID数据与联邦轮次模拟 =====
# 知识点：
#   - 非 IID：每个客户端的数据分布不同 —— 现实世界的常态
#   - 后果：本地最优互不一致 → 平均后震荡、收敛慢、甚至发散
#   - 缓解：更多全局轮次、更少本地步、动量/近端项（FedProx 思想）
#   - FedProx：本地目标加 μ·‖w − w_global‖²，把本地拉回全局附近
#   - 客户端异质性还带来加权公平性问题（大客户端主导聚合）
# 依赖：无（标准库）
import math
import random


def predict(w, x):
    return w[0] * x + w[1]


def mse(w, data):
    return sum((predict(w, x) - y) ** 2 for x, y in data) / len(data)


def local_train(w, data, epochs, lr, mu=0.0, global_w=None):
    """本地训练；mu > 0 时启用 FedProx 近端项。"""
    w = list(w)
    n = len(data)
    for _ in range(epochs):
        grad = [0.0, 0.0]
        for x, y in data:
            err = predict(w, x) - y
            grad[0] += err * x / n
            grad[1] += err / n
        if mu > 0 and global_w is not None:
            grad[0] += mu * (w[0] - global_w[0])
            grad[1] += mu * (w[1] - global_w[1])
        w[0] -= lr * grad[0]
        w[1] -= lr * grad[1]
    return w


def fedavg(clients, rounds, epochs, lr, mu=0.0):
    w = [0.0, 0.0]
    hist = []
    for r in range(rounds):
        new_w = [0.0, 0.0]
        total = 0
        for data in clients:
            lw = local_train(w, data, epochs, lr, mu, w)
            weight = len(data)
            for i in range(2):
                new_w[i] += lw[i] * weight
            total += weight
        w = [v / total for v in new_w]
        all_data = [item for d in clients for item in d]
        hist.append((r + 1, mse(w, all_data)))
    return w, hist


rng = random.Random(105)

print("== 非 IID 数据：每个客户端的斜率/截距都不同 ==")
clients_noniid = []
slopes = [1.0, 2.0, 3.0, 4.0, 5.0]
for c, slope in enumerate(slopes):
    xs = [rng.uniform(c * 2, c * 2 + 4) for _ in range(150)]      # 特征范围也错开
    data = [(x, slope * x - 2.0 + rng.gauss(0, 0.8)) for x in xs]
    clients_noniid.append(data)
    print(f"  客户端{c + 1}: y ≈ {slope}x − 2, x∈[{c * 2:.0f},{c * 2 + 4:.0f}]")
all_data = [item for d in clients_noniid for item in d]
print(f"  全局『最优单模型』其实不存在 —— 数据本身就是多模态的")

print("\n== FedAvg 在非 IID 下的震荡 ==")
w, hist = fedavg(clients_noniid, rounds=15, epochs=5, lr=0.05)
print(f"  {'轮':>4}{'全局MSE':>12}")
for r, e in hist:
    print(f"  {r:>4}{e:>12.4f}")
mvals = [e for _, e in hist]
print(f"  轮间 MSE 最大波动 = {max(mvals) - min(mvals):.4f}")
print("  本地最优互相拉扯：平均后的模型在每个客户端都不好 -> 来回震荡")

print("\n== FedProx：近端项驯服漂移 ==")
w_prox, hist_prox = fedavg(clients_noniid, rounds=15, epochs=5, lr=0.05, mu=0.5)
print(f"  {'轮':>4}{'FedAvg MSE':>12}{'FedProx MSE':>14}")
for (r, e1), (_, e2) in zip(hist, hist_prox):
    print(f"  {r:>4}{e1:>12.4f}{e2:>14.4f}")
print("  近端项让本地更新『不敢走远』—— 折中收敛与个性化")

print("\n== 本地轮数的敏感性（非 IID 放大）==")
print(f"  {'本地轮数E':>10}{'FedAvg最终MSE':>14}{'FedProx最终MSE':>16}")
for E in (1, 3, 5, 10):
    w1, h1 = fedavg(clients_noniid, rounds=15, epochs=E, lr=0.05)
    w2, h2 = fedavg(clients_noniid, rounds=15, epochs=E, lr=0.05, mu=0.5)
    print(f"  {E:>10}{h1[-1][1]:>14.4f}{h2[-1][1]:>16.4f}")
print("  E 越大漂移越猛：非 IID 下 E=1（每步通信）反而最稳 —— 通信换稳定")

print("\n== 数据量不均：谁说了算 ==")
unbalanced = [clients_noniid[0]] * 0 + \
             [clients_noniid[1][:10], clients_noniid[2][:15],
              clients_noniid[3], clients_noniid[4], clients_noniid[0]]
w_u, h_u = fedavg(unbalanced, rounds=10, epochs=5, lr=0.05)
w_eq = [0.0, 0.0]
# 等权聚合对照
w_eq_cur = [0.0, 0.0]
for r in range(10):
    acc = [0.0, 0.0]
    for data in unbalanced:
        lw = local_train(w_eq_cur, data, 5, 0.05)
        acc[0] += lw[0] / len(unbalanced)
        acc[1] += lw[1] / len(unbalanced)
    w_eq_cur = acc
all_u = [item for d in unbalanced for item in d]
print(f"  样本量加权聚合 MSE = {h_u[-1][1]:.4f}")
print(f"  等权聚合 MSE       = {mse(w_eq_cur, all_u):.4f}")
print("  加权被大客户端主导（此处 150 样本 vs 10 样本）；等权尊重每个参与者")
print("  公平性是联邦的系统设计问题，不只是算法问题")

print("\n== 客户端漂移可视化 ==")
print("  本地最优 w* 的分布（每个客户端单独训练到底）:")
for i, data in enumerate(clients_noniid):
    lw = local_train([0.0, 0.0], data, 200, 0.05)
    print(f"    客户端{i + 1}: w = [{lw[0]:.2f}, {lw[1]:.2f}]")
print("  平均了 5 个互不相同的本地最优 —— 平均永远不等于任何一个")

print("\n== 小结 ==")
for line in (
    "  非 IID 是联邦学习的真正难点：漂移、震荡、个性化需求都由此而来",
    "  FedProx 的近端项是『别走太远』的软约束，一行代码的改进",
    "  聚合权重是政治问题：样本量加权 vs 等权 vs 参与度加权",
    "  913 课：在联邦之上叠加差分隐私 —— 双层防御",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 SCAFFOLD 的控制变量思想（本地修正项），与 FedProx 对比。
# 2. 实现「客户端聚类联邦」：先按数据分布聚类，再组内联邦，评估全局 MSE。
# 3. 扫描 μ ∈ {0, 0.1, 0.5, 1.0, 2.0}，画 FedProx 的 μ-精度曲线。
# 4. 思考：什么时候应该放弃全局模型、改做『每个客户端个性化 + 联邦特征层』？
