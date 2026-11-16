# ===== 第376课：机器学习入门-线性回归(最小二乘) =====
# 知识点：
#   - 线性模型：y = w0 + w1*x1 + ... + wn*xn，矩阵形式 y = Xw
#   - 偏置项 b：给 X 加一列全 1，b 就变成第 0 个权重
#   - 最小二乘：最小化误差平方和，闭式解 w = (XᵀX)⁻¹Xᵀy
#   - 数值稳定写法：np.linalg.lstsq（内部用 SVD，避免显式求逆）
#   - 评估：R² 决定系数，1 完美、0 等于“只会猜均值”、可为负
# 依赖：pip install numpy

import numpy as np


def add_bias(X):
    """在特征矩阵左侧拼一列 1，用于承载截距。"""
    return np.c_[np.ones(len(X)), X]


def fit_lstsq(X, y):
    """最小二乘闭式解。返回权重向量 w（长度 = 特征数 + 1）。"""
    w, *_ = np.linalg.lstsq(X, y, rcond=None)
    return w


def predict(X, w):
    return X @ w


def r2_score(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - y_true.mean()) ** 2)
    return 1 - ss_res / ss_tot


# ---- 数据：真实规律 y = 1.2 + 2.5*x + 0.8*x2 + 噪声 ----
rng = np.random.default_rng(7)
n = 120
X_raw = np.c_[rng.uniform(0, 10, n), rng.uniform(-2, 2, n)]
TRUE_W = np.array([1.2, 2.5, 0.8])
y = add_bias(X_raw) @ TRUE_W + rng.normal(0, 1.2, n)

# ---- 拟合 ----
X = add_bias(X_raw)
w = fit_lstsq(X, y)
print("真实权重：", TRUE_W, "（含截距 1.2）")
print("拟合权重：", w.round(3))

# ---- 预测与评估 ----
y_pred = predict(X, w)
print("\n前 5 条预测 vs 真实：")
for t, p in list(zip(y, y_pred))[:5]:
    print(f"  真实 {t:6.2f} | 预测 {p:6.2f} | 误差 {p - t:+.2f}")

print(f"\nR² = {r2_score(y, y_pred):.4f}（越接近 1 越好）")
print(f"均方误差 MSE = {np.mean((y - y_pred) ** 2):.3f}")

# ---- 只用一个特征对比：模型会不会“欠拟合” ----
X_one = add_bias(X_raw[:, :1])
w_one = fit_lstsq(X_one, y)
print(f"只用第一个特征时 R² = {r2_score(y, predict(X_one, w_one)):.4f}")
print("说明：少了重要特征，模型再准也补不回来 —— 特征工程 > 调参")

# ---- 预测新样本 ----
new_x = np.array([[5.0, 1.0]])
new_pred = predict(add_bias(new_x), w)
print(f"\n新样本 {new_x[0]} 预测值：{new_pred[0]:.2f}")

# ===== 练习题 =====
# 1. 把噪声标准差加到 5，观察 R² 下降多少。
# 2. 手动用公式 (XᵀX)⁻¹Xᵀy 算一遍，与 lstsq 结果对比（打印差异）。
# 3. 构造一个“R² 为负”的预测（比如全部预测成均值再故意偏移），解释含义。
# 4. 思考：特征之间存在强相关（共线性）时，闭式解会出什么问题？
