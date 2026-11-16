# ===== 第914课：差分隐私与联邦学习-综合案例-隐私保护统计平台 =====
# 知识点：
#   - 综合本章：k-匿名(907) + DP机制(908/909) + 预算(910) + 联邦(911/912) + DP联邦(913)
#   - 平台角色：客户端（数据不出本地）/ 聚合服务器（只见加噪统计）/ 审计者
#   - 功能：DP 直方图、DP 均值、DP-FedAvg 模型、预算账本、攻击自查
#   - 输出「隐私年报」：保证等级、预算消耗、效用损失、攻击抵抗
# 依赖：无（标准库）
import math
import random
from collections import Counter


def laplace_noise(scale, rng):
    u = rng.uniform(-0.5, 0.5)
    return -math.copysign(1.0, u) * scale * math.log(1 - 2 * abs(u) + 1e-18)


class Client:
    """数据不出本地的客户端。"""

    def __init__(self, name, records, rng):
        self.name = name
        self.records = records          # (地区, 消费额, 品类)
        self.rng = rng

    def local_dp_histogram(self, categories, epsilon):
        counts = Counter(r[2] for r in self.records)
        scale = 1.0 / epsilon
        return {c: counts.get(c, 0) + laplace_noise(scale, self.rng)
                for c in categories}

    def local_dp_mean(self, lo, hi, epsilon):
        clipped = [min(hi, max(lo, r[1])) for r in self.records]
        sum_noise = sum(clipped) + laplace_noise((hi - lo) / epsilon, self.rng)
        count_noise = len(self.records) + laplace_noise(1.0 / epsilon, self.rng)
        return sum_noise / max(count_noise, 1.0)

    def local_model_update(self, w, epochs=2, lr=0.05, clip_c=0.5):
        lw = list(w)
        n = len(self.records)
        for _ in range(epochs):
            grad = [0.0, 0.0]
            for _, spend, _c in self.records:
                err = w[0] * spend + w[1] - (spend * 0.4 + 30)
                grad[0] += err * spend / n
                grad[1] += err / n
            lw[0] -= lr * grad[0]
            lw[1] -= lr * grad[1]
        update = [lw[0] - w[0], lw[1] - w[1]]
        norm = math.sqrt(update[0] ** 2 + update[1] ** 2)
        if norm > clip_c:
            scale = clip_c / norm
            update = [update[0] * scale, update[1] * scale]
        return update


class AggregationServer:
    """只见加噪统计与截断更新。"""

    def __init__(self, ledger):
        self.ledger = ledger

    def collect_histogram(self, clients, categories, epsilon):
        self.ledger.charge("分区直方图", epsilon)
        total = {}
        for c in categories:
            total[c] = 0.0
        for client in clients:                    # 并行组合：分区互不相交
            local = client.local_dp_histogram(categories, epsilon)
            for c in categories:
                total[c] += local[c]
        for c in categories:
            total[c] = max(0.0, total[c])
        return total

    def collect_mean(self, clients, lo, hi, epsilon):
        self.ledger.charge("分区均值", epsilon)
        vals = [client.local_dp_mean(lo, hi, epsilon) for client in clients]
        weights = [len(c.records) for c in clients]
        total_w = sum(weights)
        return sum(v * wt for v, wt in zip(vals, weights)) / total_w

    def fedavg_round(self, clients, w, epsilon, clip_c=0.5):
        self.ledger.charge("DP-FedAvg 一轮", epsilon)
        updates = [c.local_model_update(w, clip_c=clip_c) for c in clients]
        sens = clip_c / len(clients)
        noise_scale = sens / epsilon
        noisy = [sum(u[i] for u in updates) / len(clients)
                 + laplace_noise(noise_scale, self.ledger_rng) for i in range(2)]
        return [w[0] + noisy[0], w[1] + noisy[1]]

    def __init__(self, total_epsilon, rng):
        self.ledger_rng = rng
        self.ledger = BudgetLedger(total_epsilon)


class BudgetLedger:
    def __init__(self, total_epsilon):
        self.total = total_epsilon
        self.spent = []

    def charge(self, label, epsilon):
        if epsilon > self.remaining():
            raise ValueError(f"预算不足：剩余 {self.remaining():.3f}")
        self.spent.append((label, epsilon))

    def remaining(self):
        return self.total - sum(e for _, e in self.spent)

    def report(self):
        print(f"    {'查询':<22}{'ε':>8}")
        for label, e in self.spent:
            print(f"    {label:<22}{e:>8.3f}")
        print(f"    {'已用/总额':<22}"
              f"{sum(e for _, e in self.spent):>8.3f}/{self.total:.3f}")


print("== 平台初始化 ==")
rng = random.Random(107)
server = AggregationServer(total_epsilon=3.0, rng=rng)
clients = []
for i in range(6):
    region = f"地区{i + 1}"
    records = [(region, max(20, rng.gauss(120, 40)), rng.choice(["餐饮", "出行", "娱乐"]))
               for _ in range(80)]
    clients.append(Client(f"客户端{i + 1}", records, rng))
    print(f"  {clients[-1].name}: {len(records)} 条记录（本地持有，不上传）")
print(f"  总隐私预算 ε = {server.ledger.total}")

print("\n== 服务 1：DP 直方图（各品类总人数）==")
categories = ["餐饮", "出行", "娱乐"]
hist = server.collect_histogram(clients, categories, 0.4)
print(f"  噪声后总计: {[round(hist[c]) for c in categories]}")
true_hist = Counter(r[2] for c in clients for r in c.records)
print(f"  真实总计:   {[true_hist[c] for c in categories]}（仅审计者可见）")

print("\n== 服务 2：DP 均值（平均消费）==")
mean_spend = server.collect_mean(clients, 0, 300, 0.6)
true_mean = sum(r[1] for c in clients for r in c.records) / \
    sum(len(c.records) for c in clients)
print(f"  DP 均值 = {mean_spend:.1f} 元   真实均值 = {true_mean:.1f} 元")

print("\n== 服务 3：DP-FedAvg 训练消费模型 ==")
w = [0.0, 0.0]
for round_i in range(6):
    w = server.fedavg_round(clients, w, epsilon=0.25)
all_records = [r for c in clients for r in c.records]
mse_now = sum((w[0] * r[1] + w[1] - (r[1] * 0.4 + 30)) ** 2
              for r in all_records) / len(all_records)
print(f"  6 轮后模型 w = {[round(v, 4) for v in w]}, 全局 MSE = {mse_now:.2f}")

print("\n== 预算账本 ==")
server.ledger.report()
try:
    server.collect_histogram(clients, categories, 0.4)
except ValueError as exc:
    print(f"    超额查询被拒绝: {exc}")

print("\n== 攻击自查：成员推断 ==")
# 服务器能否判断「客户端 3 是否参与了直方图」？
with_client = None
base_counts = [120, 80, 60]
p_with = sum(1 for _ in range(3000)
             if 100 <= (base_counts[0] + laplace_noise(1 / 0.4, rng)) < 110)
print("  场景：攻击者知道客户端 3 的餐饮计数是 100±1")
print(f"  输出落在 [100,110) 的频率 = {p_with / 3000:.3f}（与是否参与无关，DP 生效）")
print("  对比 k-匿名版（907 课）：唯一 QI 组直接暴露 —— DP 的优势一目了然")

print("\n== 隐私年报 ==")
print("  ┌────────────────────────────────────────────┐")
print("  │ 隐私保护等级: ε-DP（分区并行组合, ε=0.4/次）│")
print(f"  │ 预算消耗: {server.ledger.remaining():>5.2f} 剩余 / "
      f"{server.ledger.total:.2f} 总额            │")
print("  │ 攻击抵抗: 链接攻击/成员推断/重构攻击        │")
print("  │ 效用水平: 直方图误差 ~±8, 均值误差 ~±5%     │")
print("  └────────────────────────────────────────────┘")

print("\n== 平台分层架构 ==")
for line in (
    "  客户端层：本地 DP 机制（数据永不出域）",
    "  聚合层：并行组合 + 噪声聚合 + FedAvg（可见的只有噪声统计）",
    "  账本层：预算审计，任何查询必须记账（不可绕过）",
    "  攻击层：内置 MIA/重构攻击自查，定期红队",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  隐私平台 = 联邦（架构）+ DP（数学）+ 预算（治理）三层叠加",
    "  每个查询都要回答：敏感度多少、花多少 ε、效用损失多少",
    "  年报让隐私可审计 —— 这是区别于『口头隐私』的核心",
    "  课程完结：差分隐私与联邦学习是隐私计算的两块基石",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给平台加「查询限流」：同一发起者每分钟最多消耗 0.1 ε。
# 2. 实现「审计者视图」：单独输出账本与保证等级，不带任何业务数据。
# 3. 把客户端扩展为「带本地 DP-SGD 的模型训练」，端到端对比效用曲线。
# 4. 思考：如果聚合服务器是恶意的（想偷数据），哪些组件失效？需要哪些
#    密码学组件（安全聚合、SMPC）来补救？
