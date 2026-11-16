# ===== 第377课：机器学习入门-线性回归(梯度下降) =====
# 知识点：
#   - 梯度下降：沿损失下降最快的方向小步走，重复到收敛
#   - 参数更新：w = w - lr * ∂L/∂w；MSE 的梯度 = (2/n) * Xᵀ(Xw - y)
#   - 学习率：太小学得慢，太大直接发散（打印 loss 曲线判断）
#   - 标准化让梯度下降收敛更快（不同量纲导致“峡谷形”损失面）
#   - 闭式解 vs 迭代法：小数据闭式解快，大数据/复杂模型只能迭代
# 依赖：pip install numpy

import numpy as np


def add_bias(X):
    return np.c_[np.ones(len(X)), X]


def mse(y_true, y_pred):
    return float(np.mean((y_true - y_pred) ** 2))


def gradient_descent(X, y, lr=0.1, epochs=3000, verbose_every=500):
    """线性回归的梯度下降版。返回 (w, loss_history)。"""
    n, d = X.shape
    w = np.zeros(d)                      # 从 0 开始
    losses = []
    for epoch in range(1, epochs + 1):
        pred = X @ w
        err = pred - y
        grad = (2.0 / n) * X.T @ err     # MSE 的梯度
        w -= lr * grad
        loss = float(np.mean(err ** 2))
        losses.append(loss)
        if verbose_every and epoch % verbose_every == 0:
            print(f"  epoch {epoch:5d} | loss {loss:.4f} | w {w.round(3)}")
    return w, losses


# ---- 数据（与 376 课相同规律）----
rng = np.random.default_rng(7)
n = 120
X_raw = np.c_[rng.uniform(0, 10, n), rng.uniform(-2, 2, n)]
TRUE_W = np.array([1.2, 2.5, 0.8])
y = add_bias(X_raw) @ TRUE_W + rng.normal(0, 1.2, n)
X = add_bias(X_raw)

# ---- 未标准化直接梯度下降：收敛慢、学习率难选 ----
print("== 不标准化（特征量纲差异大）==")
w_raw, losses_raw = gradient_descent(X, y, lr=0.01, epochs=1000, verbose_every=500)

# ---- 标准化后再下降：快且稳 ----
print("\n== 标准化后 ==")
mean, std = X_raw.mean(axis=0), X_raw.std(axis=0)
X_scaled = add_bias((X_raw - mean) / std)
w_scaled, losses_scaled = gradient_descent(X_scaled, y, lr=0.1, epochs=1000, verbose_every=500)

print(f"\n原始空间 loss：{losses_raw[0]:.2f} → {losses_raw[-1]:.4f}")
print(f"标准化空间 loss：{losses_scaled[0]:.2f} → {losses_scaled[-1]:.4f}")

# ---- 与闭式解对账 ----
w_closed, *_ = np.linalg.lstsq(X_scaled, y, rcond=None)
print("\n闭式解权重：", w_closed.round(3))
print("梯度下降权重：", w_scaled.round(3))
print("差值很小说明两种方法殊途同归")

# ---- 学习率实验：过大直接发散 ----
print("\n== 学习率 1.0（过大）==")
_, losses_bad = gradient_descent(X_scaled, y, lr=1.0, epochs=10, verbose_every=0)
print("loss 前 5 轮：", [round(v, 2) for v in losses_bad[:5]])
print("loss 是否爆炸：", any(not np.isfinite(v) or v > 1e6 for v in losses_bad))

# ===== 练习题 =====
# 1. 把 epochs 拉到 5000，打印最后 5 轮 loss，看是否还在下降。
# 2. 学习率分别试 0.001 / 0.01 / 0.1 / 0.5，记录哪一档收敛最快。
# 3. 实现“随机梯度下降”（每次只用一个样本），观察 loss 抖动。
# 4. 思考：为什么第 376 课的闭式解不需要学习率？（提示：直接解方程）
