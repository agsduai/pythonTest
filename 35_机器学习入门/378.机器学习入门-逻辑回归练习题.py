# ===== 第378课：机器学习入门-逻辑回归 =====
# 知识点：
#   - 逻辑回归 = 线性模型 + sigmoid，把输出压到 (0,1) 当概率
#   - sigmoid(z) = 1 / (1 + e^(-z))；z = 0 时概率 0.5，即分类边界
#   - 损失用交叉熵（对数损失），梯度依然是 (1/n) * Xᵀ(p - y)
#   - 阈值 0.5 可调：阈值低 → 召回高，阈值高 → 精确率高（第381课展开）
#   - 这是最常用的二分类基线模型
# 依赖：pip install numpy

import numpy as np


def sigmoid(z):
    # 分正负两支，避免 exp 溢出（工程细节）
    out = np.empty_like(z, dtype=float)
    pos = z >= 0
    out[pos] = 1 / (1 + np.exp(-z[pos]))
    exp_z = np.exp(z[~pos])
    out[~pos] = exp_z / (1 + exp_z)
    return out


def fit_logistic(X, y, lr=0.1, epochs=3000):
    """交叉熵 + 梯度下降。X 需含偏置列且已标准化。"""
    w = np.zeros(X.shape[1])
    for _ in range(epochs):
        p = sigmoid(X @ w)
        grad = (1 / len(y)) * X.T @ (p - y)
        w -= lr * grad
    return w


def predict_proba(X, w):
    return sigmoid(X @ w)


def predict(X, w, threshold=0.5):
    return (predict_proba(X, w) >= threshold).astype(int)


# ---- 造两类数据：两个高斯团，略有重叠 ----
rng = np.random.default_rng(3)
n = 300
X0 = rng.normal([2, 2], [1.2, 1.2], size=(n // 2, 2))      # 类别 0
X1 = rng.normal([5, 5], [1.2, 1.2], size=(n // 2, 2))      # 类别 1
X_raw = np.vstack([X0, X1])
y = np.r_[np.zeros(n // 2), np.ones(n // 2)]

# ---- 标准化 + 加偏置 ----
mean, std = X_raw.mean(axis=0), X_raw.std(axis=0)
X = np.c_[np.ones(n), (X_raw - mean) / std]

# ---- 训练 ----
w = fit_logistic(X, y, lr=0.5, epochs=3000)
print("权重（含偏置）：", w.round(3))

# ---- 评估 ----
prob = predict_proba(X, w)
pred = predict(X, w)
acc = np.mean(pred == y)
print(f"\n训练集准确率：{acc:.3f}")
print("前 5 条概率：", prob[:5].round(3))
print("前 5 条真实标签：", y[:5].astype(int))

# ---- 决策边界：w0 + w1*z1 + w2*z2 = 0 ----
print("\n决策边界（标准化空间）："
      f"{w[1]:.2f}*z1 + {w[2]:.2f}*z2 + {w[0]:.2f} = 0")

# ---- 阈值变化对预测的影响 ----
for th in (0.3, 0.5, 0.7):
    p = predict(X, w, threshold=th)
    print(f"阈值 {th}: 预测为正类 {p.sum()} 条，准确率 {np.mean(p == y):.3f}")

# ---- 用模型预测一个新点 ----
new_point = np.array([[3.5, 3.5]])
new_z = np.c_[np.ones(1), (new_point - mean) / std]
print(f"\n新点 {new_point[0]} 属于类别 1 的概率：{predict_proba(new_z, w)[0]:.3f}")

# ===== 练习题 =====
# 1. 把两类团拉近（均值 [2,2] 与 [3.5,3.5]），观察准确率下降。
# 2. 打印 20 个阈值（0.05~0.95），画“阈值-准确率”表格找最优点。
# 3. 故意喂入未标准化的特征训练，观察收敛与准确率变化。
# 4. 思考：逻辑回归为什么叫“回归”却用来做分类？
