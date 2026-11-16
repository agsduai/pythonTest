# ===== 第380课：机器学习入门-KMeans聚类 =====
# 知识点：
#   - 聚类：无标签，把“相似的样本”自动分堆
#   - KMeans 两步循环：①按最近中心分配标签 ②用组内均值更新中心
#   - 惯性 inertia：所有样本到所属中心的距离平方和，越小越紧凑
#   - K 怎么选：肘部法则（inertia 随 K 下降，找“拐点”）
#   - 初始化敏感：可用“随机选样本 + 多次重启取最优”缓解
# 依赖：pip install numpy

import numpy as np


def kmeans(X, k, epochs=100, seed=42):
    """返回 labels, centers, inertia。"""
    rng = np.random.default_rng(seed)
    centers = X[rng.choice(len(X), size=k, replace=False)].copy()   # 随机初始化

    labels = np.zeros(len(X), dtype=int)
    for _ in range(epochs):
        # ① 分配：每个样本找最近中心
        dist2 = ((X[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        new_labels = dist2.argmin(axis=1)

        # ② 更新：每个簇取均值
        new_centers = centers.copy()
        for j in range(k):
            members = X[new_labels == j]
            if len(members):
                new_centers[j] = members.mean(axis=0)

        if np.allclose(new_centers, centers) and np.array_equal(new_labels, labels):
            break
        centers, labels = new_centers, new_labels

    inertia = float(np.sum((X - centers[labels]) ** 2))
    return labels, centers, inertia


# ---- 三类数据（故意不告诉算法标签）----
rng = np.random.default_rng(5)
X = np.vstack([
    rng.normal([0, 0], 0.9, size=(50, 2)),
    rng.normal([6, 1], 0.9, size=(50, 2)),
    rng.normal([3, 6], 1.1, size=(50, 2)),
])
print("数据形状：", X.shape, "（150 个样本，2 个特征）")

# ---- 聚类 K=3 ----
labels, centers, inertia = kmeans(X, k=3)
print("\n聚类中心：\n", centers.round(2))
print("惯性 inertia：", round(inertia, 2))
print("各簇样本数：", [int((labels == j).sum()) for j in range(3)])

# ---- 肘部法则：K=1..6 的惯性 ----
print("\nK 值 → inertia（找拐点）：")
for k in range(1, 7):
    _, _, inertia_k = kmeans(X, k=k, seed=1)
    bar = "█" * int(inertia_k / 200)
    print(f"  K={k}: {inertia_k:10.1f} {bar}")

# ---- 多次重启取最优（缓解初始化敏感）----
best = None
for seed in range(5):
    lab, cen, ini = kmeans(X, k=3, seed=seed)
    if best is None or ini < best[2]:
        best = (lab, cen, ini)
print(f"\n5 次重启的最优 inertia：{best[2]:.2f}（其余：", end="")
print([round(kmeans(X, k=3, seed=s)[2], 1) for s in range(5)], ")")

# ---- 用聚类中心给新样本归类 ----
new_point = np.array([[5.8, 1.2]])
nearest = np.argmin(((best[1] - new_point) ** 2).sum(axis=1))
print(f"\n新点 {new_point[0]} 属于簇 {nearest}")

# ===== 练习题 =====
# 1. 把三类中心改成 [0,0]/[2,0]/[4,0]（更近），观察 inertia 与混淆情况。
# 2. 用 K=2 聚类本数据，打印各簇样本数，解释“强行合并”的后果。
# 3. 实现 kmeans++ 初始化（按距离概率选中心），对比 5 次重启的稳定性。
# 4. 思考：KMeans 为什么对“环形/月牙形”分布效果差？
