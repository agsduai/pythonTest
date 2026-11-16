# ===== 第428课：机器学习进阶-随机森林 =====
# 知识点：
#   - 集成学习：多个弱模型投票，通常比单个强模型更稳
#   - Bagging：每棵树用“有放回抽样”的训练子集（bootstrap）
#   - 随机特征：每次切分只考虑随机一部分特征，降低树之间相关性
#   - 预测：分类按多数投票；回归取平均
#   - 代价：训练/预测时间 × 树的数量；换来更低的方差
# 依赖：pip install numpy

import numpy as np
from collections import Counter


class Node:
    __slots__ = ("feature", "threshold", "left", "right", "pred")

    def __init__(self, pred=None):
        self.feature = self.threshold = self.left = self.right = None
        self.pred = pred


def best_split(X, y, features):
    n = len(y)
    best = (None, None, float("inf"))
    for f in features:
        order = np.argsort(X[:, f])
        xs, ys = X[order, f], y[order]
        c1 = np.cumsum(ys)
        i = np.arange(1, n)
        valid = xs[:-1] < xs[1:]
        left1, left0 = c1[:-1], i - c1[:-1]
        right1 = c1[-1] - c1[:-1]
        right0 = (n - i) - right1
        g_left = 1 - (left1 / i) ** 2 - (left0 / i) ** 2
        g_right = 1 - (right1 / (n - i)) ** 2 - (right0 / (n - i)) ** 2
        weighted = np.where(valid, (i * g_left + (n - i) * g_right) / n, np.inf)
        idx = int(np.argmin(weighted))
        if weighted[idx] < best[2]:
            best = (int(f), float((xs[idx] + xs[idx + 1]) / 2), float(weighted[idx]))
    return best


def build_tree(X, y, features, depth=0, max_depth=4, min_samples=4):
    if depth >= max_depth or len(y) < min_samples or len(np.unique(y)) == 1:
        return Node(pred=int(round(y.mean())))
    f, t, _ = best_split(X, y, features)
    if f is None:
        return Node(pred=int(round(y.mean())))
    mask = X[:, f] <= t
    node = Node()
    node.feature, node.threshold = f, t
    node.left = build_tree(X[mask], y[mask], features, depth + 1, max_depth, min_samples)
    node.right = build_tree(X[~mask], y[~mask], features, depth + 1, max_depth, min_samples)
    return node


def predict_one(node, x):
    while node.pred is None:
        node = node.left if x[node.feature] <= node.threshold else node.right
    return node.pred


class RandomForest:

    def __init__(self, n_trees=15, max_depth=4, max_features=None, seed=42):
        self.n_trees = n_trees
        self.max_depth = max_depth
        self.max_features = max_features
        self.rng = np.random.default_rng(seed)
        self.trees = []
        self.feature_sets = []

    def fit(self, X, y):
        n, d = X.shape
        k = self.max_features or max(1, int(np.sqrt(d)))
        self.trees, self.feature_sets = [], []
        for _ in range(self.n_trees):
            idx = self.rng.integers(0, n, size=n)          # bootstrap
            feats = self.rng.choice(d, size=k, replace=False)
            tree = build_tree(X[idx], y[idx], feats, max_depth=self.max_depth)
            self.trees.append(tree)
            self.feature_sets.append(feats)
        return self

    def predict(self, X):
        votes = np.zeros((len(X), self.n_trees), dtype=int)
        for j, tree in enumerate(self.trees):
            votes[:, j] = [predict_one(tree, x) for x in X]
        return np.array([Counter(row).most_common(1)[0][0] for row in votes])

    def feature_importance(self, d):
        counts = Counter()
        for feats in self.feature_sets:
            counts.update(feats)
        total = sum(counts.values())
        return {f"x{i}": counts[i] / total for i in range(d)}


# ---- 数据：4 个特征，只有 2 个真正有用 + 噪声 ----
rng = np.random.default_rng(11)
n = 400
X = rng.normal(size=(n, 4))
y = ((X[:, 0] ** 2 + X[:, 1] ** 2 > 1.3) ^ (rng.random(n) < 0.05)).astype(int)

idx = rng.permutation(n)
split = int(n * 0.7)
X_train, X_test = X[idx[:split]], X[idx[split:]]
y_train, y_test = y[idx[:split]], y[idx[split:]]

single = build_tree(X_train, y_train, list(range(4)), max_depth=4)
acc_single = np.mean([predict_one(single, x) for x in X_test] == y_test)
print(f"单棵树测试准确率：{acc_single:.3f}")

forest = RandomForest(n_trees=15, max_depth=4, seed=42).fit(X_train, y_train)
acc_forest = np.mean(forest.predict(X_test) == y_test)
print(f"随机森林（15 棵）测试准确率：{acc_forest:.3f}")

print("\n== 树数量对准确率的影响 ==")
for n_trees in (1, 5, 10, 20, 40):
    rf = RandomForest(n_trees=n_trees, max_depth=4, seed=7).fit(X_train, y_train)
    acc = np.mean(rf.predict(X_test) == y_test)
    print(f"  {n_trees:2d} 棵 → {acc:.3f}")

print("\n== 特征使用占比（近似重要性）==")
for name, score in sorted(forest.feature_importance(4).items(), key=lambda kv: -kv[1]):
    print(f"  {name}: {score:.2f}")
print("  x0/x1 是真实信号，x2/x3 是噪声 —— 看占比是否吻合")

# ===== 练习题 =====
# 1. 把投票改成“概率平均”（用叶子节点内正类比例），对比效果。
# 2. 增加袋外评估（OOB）：用未被抽中的样本评估每棵树。
# 3. 把森林用于第427课的圆环数据，对比单棵树准确率。
# 4. 思考：为什么“随机特征”能降低树之间的相关性？
