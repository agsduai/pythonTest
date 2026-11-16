# ===== 第434课：机器学习进阶-综合案例-客户流失预测 =====
# 知识点：
#   - 综合运用：特征工程（430）+ 随机森林（428）+ 评估指标（431）+ 模型持久化（433）
#   - 业务目标：预测哪些客户可能流失，输出“高风险名单”供运营跟进
#   - 类别不平衡：流失率约 25%，不能只看准确率
#   - 交付物：model.pkl + meta.json + churn_scores.csv（含概率与风险等级）
# 依赖：pip install numpy

import csv
import json
import pickle
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np


# ---------------- 1. 造客户数据 ----------------
def make_customers(n=500, seed=2026):
    rng = np.random.default_rng(seed)
    contract = rng.choice(["月付", "年付", "两年"], size=n, p=[0.5, 0.3, 0.2])
    tenure = rng.integers(1, 61, n).astype(float)          # 在网月数
    monthly = rng.normal(80, 25, n).clip(20, 200)          # 月消费
    calls = rng.poisson(1.2, n).astype(float)              # 客服来电次数
    age = rng.integers(18, 70, n).astype(float)

    effect = {"月付": 1.2, "年付": 0.2, "两年": -0.8}
    z = (1.6 - 0.07 * tenure + 0.35 * calls + 0.004 * monthly
         + np.array([effect[c] for c in contract]) - 0.01 * age
         + rng.normal(0, 0.5, n))
    p = 1 / (1 + np.exp(-z))
    churn = (rng.random(n) < p).astype(int)
    return contract, tenure, monthly, calls, age, churn


contract, tenure, monthly, calls, age, churn = make_customers()
print(f"客户数 {len(churn)}，流失率 {churn.mean():.1%}")


# ---------------- 2. 特征工程 ----------------
def build_features(contract, tenure, monthly, calls, age):
    contract = np.asarray(contract)              # 统一成 ndarray，列表也能比较
    contract_onehot = np.column_stack([
        (contract == "年付").astype(float),
        (contract == "两年").astype(float),
    ])
    numeric = np.column_stack([
        tenure,
        monthly,
        calls,
        age,
        monthly / (tenure + 1),                 # 月均消费强度
        calls / (tenure + 1),                   # 投诉密度
        np.log1p(monthly),
    ])
    X = np.hstack([numeric, contract_onehot])
    names = ["tenure", "monthly", "calls", "age", "monthly_per_tenure",
             "calls_per_tenure", "log_monthly", "contract_year", "contract_two_year"]
    return X, names


X, feature_names = build_features(contract, tenure, monthly, calls, age)
print("特征矩阵：", X.shape, "| 特征：", feature_names)


# ---------------- 3. 决策树 + 随机森林（复用第427/428课） ----------------
class Node:
    __slots__ = ("feature", "threshold", "left", "right", "pred", "samples")

    def __init__(self, pred=None, samples=0):
        self.feature = self.threshold = self.left = self.right = None
        self.pred, self.samples = pred, samples


def best_split(X, y):
    n = len(y)
    best = (None, None, float("inf"))
    for f in range(X.shape[1]):
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


def build_tree(X, y, depth=0, max_depth=4, min_samples=6, importance=None):
    if depth >= max_depth or len(y) < min_samples or len(np.unique(y)) == 1:
        return Node(pred=int(round(y.mean())), samples=len(y))
    f, t, _ = best_split(X, y)
    if f is None:
        return Node(pred=int(round(y.mean())), samples=len(y))
    if importance is not None:
        importance[f] += len(y)
    mask = X[:, f] <= t
    node = Node(samples=len(y))
    node.feature, node.threshold = f, t
    node.left = build_tree(X[mask], y[mask], depth + 1, max_depth, min_samples, importance)
    node.right = build_tree(X[~mask], y[~mask], depth + 1, max_depth, min_samples, importance)
    return node


def predict_one(node, x):
    while node.pred is None:
        node = node.left if x[node.feature] <= node.threshold else node.right
    return node.pred


class RandomForest:

    def __init__(self, n_trees=20, max_depth=4, seed=42):
        self.n_trees, self.max_depth = n_trees, max_depth
        self.rng = np.random.default_rng(seed)
        self.trees = []
        self.importance = Counter()

    def fit(self, X, y):
        n, d = X.shape
        k = max(1, int(np.sqrt(d)))
        for _ in range(self.n_trees):
            idx = self.rng.integers(0, n, size=n)
            weights = Counter()
            tree = build_tree(X[idx], y[idx], max_depth=self.max_depth,
                              importance=weights)
            self.trees.append(tree)
            self.importance.update(weights)
        return self

    def predict_proba(self, X):
        probs = np.zeros(len(X))
        for tree in self.trees:
            probs += np.array([predict_one(tree, x) for x in X])
        return probs / self.n_trees

    def predict(self, X, threshold=0.5):
        return (self.predict_proba(X) >= threshold).astype(int)


# ---------------- 4. 划分 + 训练 + 评估 ----------------
rng = np.random.default_rng(1)
idx = rng.permutation(len(X))
split = int(len(X) * 0.7)
train, test = idx[:split], idx[split:]

# 标准化（用训练集统计量）
mean, std = X[train].mean(axis=0), X[train].std(axis=0)
std[std == 0] = 1
X_train = (X[train] - mean) / std
X_test = (X[test] - mean) / std

forest = RandomForest(n_trees=20, max_depth=4).fit(X_train, churn[train])
y_pred = forest.predict(X_test)
y_true = churn[test]

tp = int(np.sum((y_true == 1) & (y_pred == 1)))
fp = int(np.sum((y_true == 0) & (y_pred == 1)))
fn = int(np.sum((y_true == 1) & (y_pred == 0)))
tn = int(np.sum((y_true == 0) & (y_pred == 0)))
precision = tp / (tp + fp) if tp + fp else 0
recall = tp / (tp + fn) if tp + fn else 0
f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
accuracy = (tp + tn) / len(y_true)

print("\n== 测试集评估 ==")
print(f"  准确率 {accuracy:.3f} | 精确率 {precision:.3f} | 召回率 {recall:.3f} | F1 {f1:.3f}")
print(f"  混淆矩阵：TP={tp} FP={fp} FN={fn} TN={tn}")

# ---------------- 5. 特征重要性 ----------------
total = sum(forest.importance.values()) or 1
print("\n== 特征重要性（切分样本占比）==")
for i, score in forest.importance.most_common(5):
    print(f"  {feature_names[i]:20s} {score / total:.1%}")

# ---------------- 6. 保存模型 + 批量打分 ----------------
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    bundle = {
        "version": "1.0",
        "features": feature_names,
        "mean": mean,
        "std": std,
        "trees": forest.trees,
        "threshold": 0.5,
        "metrics": {"accuracy": round(accuracy, 4), "f1": round(f1, 4)},
    }
    model_path = tmp / "churn_model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(bundle, f, protocol=pickle.HIGHEST_PROTOCOL)
    (tmp / "meta.json").write_text(json.dumps({
        "version": "1.0", "created_at": datetime.now().isoformat(timespec="seconds"),
        "features": feature_names, "metrics": bundle["metrics"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n模型已保存：{model_path.stat().st_size} 字节")

    # 新客户批量打分
    new_contract = ["月付", "两年", "年付", "月付", "两年"]
    new_tenure = np.array([3, 48, 24, 8, 60], dtype=float)
    new_monthly = np.array([120, 60, 90, 150, 45], dtype=float)
    new_calls = np.array([5, 0, 1, 3, 0], dtype=float)
    new_age = np.array([25, 50, 35, 30, 55], dtype=float)

    X_new, _ = build_features(new_contract, new_tenure, new_monthly,
                              new_calls, new_age)
    X_new = (X_new - mean) / std
    probs = forest.predict_proba(X_new)

    def risk_level(p):
        if p >= 0.7:
            return "高"
        if p >= 0.4:
            return "中"
        return "低"

    csv_path = tmp / "churn_scores.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["合同", "在网月数", "月消费", "来电次数", "流失概率", "风险等级"])
        for c, t, m, call, p in zip(new_contract, new_tenure, new_monthly,
                                    new_calls, probs):
            writer.writerow([c, int(t), m, int(call), round(float(p), 3), risk_level(p)])

    print("\n== 新客户流失评分 ==")
    print(csv_path.read_text(encoding="utf-8-sig"))

# 业务落地：
#   高风险管理名单 → 运营发优惠/回访；阈值可按人力调整（第431课）
#   每月重训一次，指标下降触发告警（第417课）

# ===== 练习题 =====
# 1. 把决策阈值从 0.5 调到 0.35，观察召回率与精确率变化。
# 2. 增加特征“是否投诉过”（calls>0）和“高价值客户”（monthly>100）。
# 3. 用第429课的 5 折 CV 评估，对比单次划分的稳定性。
# 4. 思考：预测“会流失”之后，业务动作应该怎么设计才不冒犯客户？
