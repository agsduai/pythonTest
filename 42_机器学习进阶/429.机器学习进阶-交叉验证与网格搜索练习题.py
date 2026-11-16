# ===== 第429课：机器学习进阶-交叉验证与网格搜索 =====
# 知识点：
#   - 单次划分的评估有运气成分 → K 折交叉验证：轮流当验证集，取平均
#   - 偏差-方差权衡：K 越大评估越稳，但训练次数越多（常用 5/10）
#   - 网格搜索：穷举超参数组合，用 CV 分数选最优
#   - 数据泄漏红线：标准化等预处理必须在每折训练集内 fit
#   - 与第375课划分、第379课 KNN 配套使用
# 依赖：pip install numpy

import numpy as np


def make_data(n=240, seed=3):
    rng = np.random.default_rng(seed)
    centers = np.array([[0, 0], [4, 4], [0, 5]])
    X, y = [], []
    for label, c in enumerate(centers):
        X.append(rng.normal(c, 1.1, size=(n // 3, 2)))
        y.append(np.full(n // 3, label))
    return np.vstack(X), np.concatenate(y)


def standardize(train, test):
    mean, std = train.mean(axis=0), train.std(axis=0)
    std[std == 0] = 1
    return (train - mean) / std, (test - mean) / std


def knn_predict(X_train, y_train, X_test, k=5):
    diff = X_test[:, None, :] - X_train[None, :, :]
    dist2 = (diff ** 2).sum(axis=2)
    neighbors = np.argsort(dist2, axis=1)[:, :k]
    preds = []
    for row in neighbors:
        values, counts = np.unique(y_train[row], return_counts=True)
        preds.append(values[np.argmax(counts)])
    return np.array(preds)


def kfold_indices(n, k=5, seed=42):
    idx = np.random.default_rng(seed).permutation(n)
    folds = np.array_split(idx, k)
    for i in range(k):
        val = folds[i]
        train = np.concatenate([folds[j] for j in range(k) if j != i])
        yield train, val


def cross_val_accuracy(X, y, k_neighbors, folds=5):
    scores = []
    for train_idx, val_idx in kfold_indices(len(X), folds):
        X_tr, X_val = X[train_idx], X[val_idx]
        y_tr, y_val = y[train_idx], y[val_idx]
        # 关键：标准化只用本折训练集
        X_tr_s, X_val_s = standardize(X_tr, X_val)
        pred = knn_predict(X_tr_s, y_tr, X_val_s, k=k_neighbors)
        scores.append(np.mean(pred == y_val))
    return np.array(scores)


X, y = make_data()
print("数据：", X.shape, "类别分布：", {int(c): int((y == c).sum()) for c in np.unique(y)})

# ---- 网格搜索 K ----
print("\n== 网格搜索：KNN 的 k 值 ==")
results = {}
for k in (1, 3, 5, 7, 9, 15, 21):
    scores = cross_val_accuracy(X, y, k)
    results[k] = (scores.mean(), scores.std())
    print(f"  k={k:2d} → CV 准确率 {scores.mean():.3f} ± {scores.std():.3f}")

best_k = max(results, key=lambda k: results[k][0])
print(f"\n最优 k = {best_k}（均值 {results[best_k][0]:.3f}）")

# ---- 折数与稳定性的关系 ----
print("\n== 折数对比（k 固定为最优）==")
for folds in (3, 5, 10):
    scores = cross_val_accuracy(X, y, best_k, folds=folds)
    print(f"  {folds} 折 → {scores.mean():.3f} ± {scores.std():.3f}（每折验证样本 {len(X)//folds}）")

# ---- 与“单次划分”的对比：证明 CV 更稳 ----
print("\n== 单次划分的波动 ==")
from itertools import islice
accs = []
for seed in range(8):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(X))
    split = int(len(X) * 0.25)
    val, tr = idx[:split], idx[split:]
    X_tr, X_val = X[tr], X[val]
    X_tr_s, X_val_s = standardize(X_tr, X_val)
    pred = knn_predict(X_tr_s, y[tr], X_val_s, k=best_k)
    accs.append(np.mean(pred == y[val]))
print("  8 次不同划分的准确率：", [round(a, 3) for a in accs])
print(f"  波动范围：{min(accs):.3f} ~ {max(accs):.3f}（CV 只用一套折，结论更可信）")

# ---- 网格搜索两个参数（演示套路）----
print("\n== 二维网格（k × 距离权重）==")


def weighted_knn(X_train, y_train, X_test, k=5):
    """距离倒数加权：越近的邻居票越重。"""
    diff = X_test[:, None, :] - X_train[None, :, :]
    dist = np.sqrt((diff ** 2).sum(axis=2)) + 1e-9
    neighbors = np.argsort(dist, axis=1)[:, :k]
    preds = []
    for row, dist_row in zip(neighbors, dist):
        weights = 1 / dist_row[row]
        votes = {}
        for i, w in zip(row, weights):
            votes[y_train[i]] = votes.get(y_train[i], 0) + w
        preds.append(max(votes, key=votes.get))
    return np.array(preds)


def cv_weighted(X, y, k, folds=5):
    scores = []
    for tr, val in kfold_indices(len(X), folds):
        X_tr_s, X_val_s = standardize(X[tr], X[val])
        pred = weighted_knn(X_tr_s, y[tr], X_val_s, k)
        scores.append(np.mean(pred == y[val]))
    return np.mean(scores)


for k in (3, 5, 9):
    print(f"  k={k}: 普通 {results[k][0]:.3f} | 距离加权 {cv_weighted(X, y, k):.3f}")

# ===== 练习题 =====
# 1. 改用分层 K 折（每折类别比例一致），对比普通 K 折。
# 2. 把决策树深度纳入网格搜索（配合第427课）。
# 3. 实现嵌套 CV：外层评估、内层选参，避免“用测试集调参”。
# 4. 思考：为什么 CV 分数很高但上线效果差？（数据分布漂移）
