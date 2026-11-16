# ===== 第535课：时间序列分析-自回归AR模型 =====
# 知识点：
#   - AR(p)：用过去 p 期的值预测当前值：y_t = c + φ1·y_{t-1} + ... + φp·y_{t-p} + ε
#   - 本质是线性回归，特征就是滞后项 → 最小二乘即可求解
#   - 平稳序列才能直接建 AR；非平稳先差分
#   - 定阶：试不同 p，用验证集误差或 AIC/BIC 选择
#   - 预测：递归地把预测值当作下一期的历史值
#   - 与第376课线性回归、第532课平稳性的联系
# 依赖：pip install numpy

import numpy as np


def simulate_ar2(n=120, phi1=0.6, phi2=-0.2, seed=5):
    rng = np.random.default_rng(seed)
    y = np.zeros(n)
    for t in range(2, n):
        y[t] = phi1 * y[t - 1] + phi2 * y[t - 2] + rng.normal(0, 1)
    return y


def fit_ar(series, p):
    """构造滞后特征矩阵，最小二乘求系数（含截距）。"""
    y = np.asarray(series, dtype=float)
    X, target = [], []
    for t in range(p, len(y)):
        X.append([1.0] + [y[t - i] for i in range(1, p + 1)])
        target.append(y[t])
    w, *_ = np.linalg.lstsq(np.array(X), np.array(target), rcond=None)
    return w


def forecast_ar(series, w, p, horizon=1):
    history = list(series[-p:])
    preds = []
    for _ in range(horizon):
        features = [1.0] + list(reversed(history[-p:]))
        value = float(np.dot(w, features))
        preds.append(value)
        history.append(value)
    return np.array(preds)


series = simulate_ar2()
print("== 模拟数据（真实 φ1=0.6, φ2=-0.2）==")
print("  前 10 个值：", series[:10].round(2))

print("\n== 拟合 AR(2) ==")
w = fit_ar(series, 2)
print("  截距：", round(w[0], 3))
print("  φ1：", round(w[1], 3), "（真实 0.6）")
print("  φ2：", round(w[2], 3), "（真实 -0.2）")

# ---- 一步预测误差 ----
preds = []
for t in range(3, len(series)):            # 至少留出 p+1 个样本，避免空矩阵
    w_roll = fit_ar(series[:t], 2)          # 用历史滚动拟合（演示用，真实应固定参数）
    preds.append(float(np.dot(w_roll, [1.0, series[t - 1], series[t - 2]])))
preds = np.array(preds)
actual = series[3:]
print(f"\n  一步预测 MAE：{np.mean(np.abs(actual - preds)):.3f}")
print(f"  序列标准差：{series.std():.3f}（MAE 应明显更小）")

# ---- 定阶 ----
print("\n== 不同 p 的验证误差 ==")
train, test = series[:100], series[100:]
for p in (1, 2, 3, 4, 5, 8):
    w = fit_ar(train, p)
    f = forecast_ar(train, w, p, horizon=len(test))
    mae = np.mean(np.abs(f - test))
    print(f"  p={p} → 多步预测 MAE {mae:.3f}")

print("\n  p 太小：欠拟合（漏掉真实滞后）")
print("  p 太大：过拟合（参数多、方差大）")
print("  真实 p=2，误差通常在 p=2 附近最小（样本有限会有波动）")

# ---- 预测未来 5 期 ----
w = fit_ar(train, 2)
future = forecast_ar(train, w, 2, horizon=5)
print("\n== 未来 5 期预测 ==")
print("  ", future.round(2))

# ---- AR 的适用条件 ----
print("\n== 适用条件 ==")
for item in [
    "序列平稳（第532课）：均值/方差不随时间变化",
    "非平稳先差分，得到 ARIMA 的思路",
    "有季节 → 先季节差分，或用 SARIMA",
    "AR 只能捕捉线性自相关；非线性需其他模型",
    "多步预测会快速收敛到均值（AR 的长期预测能力有限）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 模拟 AR(1)（φ=0.8），用 AR(1) 拟合，验证系数。
# 2. 实现 AIC 计算，比较 p=1..5 的 AIC。
# 3. 对带趋势的序列直接建 AR，观察预测为何失真。
# 4. 思考：AR 与线性回归（第376课）到底有什么本质区别？
