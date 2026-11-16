# ===== 第427课：机器学习进阶-决策树 =====
# 知识点：
#   - 决策树：每次选“最能区分类别”的特征与阈值切分，递归建树
#   - 基尼不纯度：1 - Σ p_i²；越小越纯，切分后加权基尼下降最多者为最优
#   - 停止条件：纯节点 / 达到最大深度 / 样本太少
#   - 可解释性：树结构就是规则（if x1 <= 0.5 and x2 > 1.2 → 类别 0）
#   - 缺点：单棵树容易过拟合，下一课用随机森林集成
# 依赖：pip install numpy

import numpy as np


class Node:
    __slots__ = ("feature", "threshold", "left", "right", "pred", "samples")

    def __init__(self, pred=None, samples=0):
        self.feature = None
        self.threshold = None
        self.left = None
        self.right = None
        self.pred = pred              # 非 None 表示叶子
        self.samples = samples


def gini(labels: np.ndarray) -> float:
    if len(labels) == 0:
        return 0.0
    p = labels.mean()
    return 1 - p ** 2 - (1 - p) ** 2


def best_split(X: np.ndarray, y: np.ndarray):
    """返回 (feature, threshold, 加权基尼)。只支持二分类 0/1。"""
    n = len(y)
    best = (None, None, float("inf"))
    for f in range(X.shape[1]):
        order = np.argsort(X[:, f])
        xs, ys = X[order, f], y[order]
        c1 = np.cumsum(ys)                       # 左半部分类别 1 的累计数
        i = np.arange(1, n)
        valid = xs[:-1] < xs[1:]                 # 只在不同取值之间切

        left1, left0 = c1[:-1], i - c1[:-1]
        right1 = c1[-1] - c1[:-1]
        right0 = (n - i) - right1

        g_left = 1 - (left1 / i) ** 2 - (left0 / i) ** 2
        g_right = 1 - (right1 / (n - i)) ** 2 - (right0 / (n - i)) ** 2
        weighted = (i * g_left + (n - i) * g_right) / n
        weighted = np.where(valid, weighted, np.inf)

        idx = int(np.argmin(weighted))
        if weighted[idx] < best[2]:
            best = (f, float((xs[idx] + xs[idx + 1]) / 2), float(weighted[idx]))
    return best


def build_tree(X, y, depth=0, max_depth=3, min_samples=5):
    if (depth >= max_depth or len(y) < min_samples
            or len(np.unique(y)) == 1):
        return Node(pred=int(round(y.mean())), samples=len(y))

    feature, threshold, score = best_split(X, y)
    if feature is None:
        return Node(pred=int(round(y.mean())), samples=len(y))

    mask = X[:, feature] <= threshold
    node = Node(samples=len(y))
    node.feature, node.threshold = feature, threshold
    node.left = build_tree(X[mask], y[mask], depth + 1, max_depth, min_samples)
    node.right = build_tree(X[~mask], y[~mask], depth + 1, max_depth, min_samples)
    return node


def predict_one(node: Node, x: np.ndarray) -> int:
    while node.pred is None:
        node = node.left if x[node.feature] <= node.threshold else node.right
    return node.pred


def predict(tree: Node, X: np.ndarray) -> np.ndarray:
    return np.array([predict_one(tree, x) for x in X])


def print_tree(node: Node, indent=0):
    pad = "  " * indent
    if node.pred is not None:
        print(f"{pad}└─ 预测 {node.pred}（样本 {node.samples}）")
        return
    print(f"{pad}├─ x{node.feature} <= {node.threshold:.3f} ? （样本 {node.samples}）")
    print(f"{pad}│  是：")
    print_tree(node.left, indent + 1)
    print(f"{pad}│  否：")
    print_tree(node.right, indent + 1)


# ---- 数据：圆环内为 0、圆环外为 1（需要非线性边界）----
rng = np.random.default_rng(7)
n = 400
X = rng.uniform(-2, 2, size=(n, 2))
radius = np.sqrt((X ** 2).sum(axis=1))
y = (radius > 1.2).astype(int)
noise = rng.random(n) < 0.08                 # 8% 标签噪声
y[noise] = 1 - y[noise]

idx = rng.permutation(n)
split = int(n * 0.7)
train, test = idx[:split], idx[split:]

tree = build_tree(X[train], y[train], max_depth=3)
print("== 决策树结构 ==")
print_tree(tree)

train_acc = np.mean(predict(tree, X[train]) == y[train])
test_acc = np.mean(predict(tree, X[test]) == y[test])
print(f"\n训练集准确率：{train_acc:.3f} | 测试集准确率：{test_acc:.3f}")

# ---- 深度的影响 ----
print("\n== 最大深度对比 ==")
for depth in (1, 2, 3, 5, 8):
    t = build_tree(X[train], y[train], max_depth=depth, min_samples=3)
    acc = np.mean(predict(t, X[test]) == y[test])
    print(f"  depth={depth} → 测试准确率 {acc:.3f}")

# ---- 单点预测 ----
for point in ([0.5, 0.5], [1.8, 1.8]):
    print(f"  点 {point} 预测：{predict_one(tree, np.array(point))}")

# ===== 练习题 =====
# 1. 把基尼换成信息熵（-Σ p log p），对比树结构与准确率。
# 2. 增加 max_features 参数，每次只在随机子集特征中选切分。
# 3. 实现 print_rules(tree)：把树翻译成 if/else 规则文本。
# 4. 思考：为什么树越深训练准确率越高，但测试可能变差？
