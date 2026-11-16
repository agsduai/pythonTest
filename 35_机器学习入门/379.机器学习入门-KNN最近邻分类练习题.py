# ===== 第379课：机器学习入门-KNN最近邻分类 =====
# 知识点：
#   - KNN：不训练参数，预测时找“最近的 K 个邻居”投票
#   - 距离：欧氏距离 √Σ(xi-yi)²；先标准化否则大数值特征垄断距离
#   - K 的影响：太小易受噪声影响（过拟合），太大边界变钝（欠拟合）
#   - 优点：简单、无假设、天然多分类；缺点：预测时要遍历全部训练样本
#   - 与第247课“最近邻”思想、第253课“距离/相似度”一脉相承
# 依赖：pip install numpy

import numpy as np


def train_test_split(X, y, test_size=0.25, seed=42):
    idx = np.random.default_rng(seed).permutation(len(X))
    n_test = int(len(X) * test_size)
    return X[idx[n_test:]], X[idx[:n_test]], y[idx[n_test:]], y[idx[:n_test]]


def knn_predict(X_train, y_train, X_test, k=5):
    """向量化算距离 + 多数投票。"""
    # (n_test, n_train) 的距离平方矩阵
    diff = X_test[:, None, :] - X_train[None, :, :]
    dist2 = np.sum(diff ** 2, axis=2)

    neighbor_idx = np.argsort(dist2, axis=1)[:, :k]     # 每行最近的 k 个
    preds = []
    for row in neighbor_idx:
        labels = y_train[row]
        values, counts = np.unique(labels, return_counts=True)
        preds.append(values[np.argmax(counts)])         # 票数最多
    return np.array(preds)


def accuracy(y_true, y_pred):
    return float(np.mean(y_true == y_pred))


# ---- 三类数据：三个高斯团 ----
rng = np.random.default_rng(11)
centers = np.array([[0, 0], [4, 4], [0, 5]])
X_parts, y_parts = [], []
for label, center in enumerate(centers):
    X_parts.append(rng.normal(center, 1.0, size=(40, 2)))
    y_parts.append(np.full(40, label))
X_raw = np.vstack(X_parts)
y = np.concatenate(y_parts)

# ---- 标准化 + 划分 ----
X = (X_raw - X_raw.mean(axis=0)) / X_raw.std(axis=0)
X_train, X_test, y_train, y_test = train_test_split(X, y)
print(f"训练 {len(X_train)} 条，测试 {len(X_test)} 条")

# ---- 不同 K 值的准确率 ----
print("\nK 值对准确率的影响：")
for k in (1, 3, 5, 9, 15, 25):
    pred = knn_predict(X_train, y_train, X_test, k=k)
    print(f"  K={k:2d} → 测试集准确率 {accuracy(y_test, pred):.3f}")

# ---- 逐条看一条预测过程 ----
k = 5
sample = X_test[0]
dist = np.sqrt(np.sum((X_train - sample) ** 2, axis=1))
nearest = np.argsort(dist)[:k]
print(f"\n测试样本 {sample.round(2)} 的 {k} 个最近邻：")
for i in nearest:
    print(f"  距离 {dist[i]:.3f}，标签 {int(y_train[i])}")
print("预测类别：", int(knn_predict(X_train, y_train, sample.reshape(1, -1), k)[0]))
print("真实类别：", int(y_test[0]))

# ---- 预测“新数据” ----
new_points = np.array([[0.2, 0.1], [4.1, 3.9], [0.1, 5.2]])
new_scaled = (new_points - X_raw.mean(axis=0)) / X_raw.std(axis=0)
print("\n新点预测：", knn_predict(X_train, y_train, new_scaled, k=5).tolist())

# ===== 练习题 =====
# 1. 把 K 改成 41（接近训练集规模），观察准确率为何下降。
# 2. 改用曼哈顿距离（绝对值之和），对比准确率。
# 3. 把标准化去掉再跑，观察准确率变化并解释。
# 4. 思考：KNN 的“训练”几乎为零，代价转移到了哪里？
