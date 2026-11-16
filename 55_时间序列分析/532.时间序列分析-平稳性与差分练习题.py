# ===== 第532课：时间序列分析-平稳性与差分 =====
# 知识点：
#   - 平稳性：均值、方差不随时间变化，自相关只与滞后有关
#   - 非平稳的典型：带趋势、带季节、随机游走
#   - 差分：y_t - y_{t-1} 去趋势；季节差分 y_t - y_{t-12}
#   - ACF（自相关函数）：序列与自身滞后 k 期的相关性
#   - 白噪声 ACF 接近 0；随机游走 ACF 衰减极慢；差分后接近白噪声
#   - 很多模型（AR/ARIMA）要求先平稳化
# 依赖：pip install numpy

import numpy as np


def acf(x, max_lag=10):
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    denom = np.sum(x * x)
    return np.array([np.sum(x[:-k] * x[k:]) / denom if k else 1.0
                     for k in range(max_lag + 1)])


def diff(x, periods=1):
    x = np.asarray(x, dtype=float)
    return x[periods:] - x[:-periods]


rng = np.random.default_rng(3)
n = 200

white_noise = rng.normal(0, 1, n)
random_walk = np.cumsum(rng.normal(0, 1, n))
trend_series = 0.5 * np.arange(n) + rng.normal(0, 2, n)
seasonal_series = 10 * np.sin(2 * np.pi * np.arange(n) / 12) + rng.normal(0, 1, n)

series_dict = {
    "白噪声": white_noise,
    "随机游走": random_walk,
    "带趋势": trend_series,
    "带季节": seasonal_series,
}

print("== 各序列的 ACF（滞后 0~5）==")
print(f"  {'序列':<8}{'ACF1':>8}{'ACF2':>8}{'ACF3':>8}{'ACF4':>8}{'ACF5':>8}")
for name, x in series_dict.items():
    a = acf(x, 5)
    print(f"  {name:<8}" + "".join(f"{v:>8.2f}" for v in a[1:]))

print("\n== 差分后 ACF ==")
print(f"  {'序列':<10}{'处理':<10}{'ACF1':>8}{'ACF2':>8}{'ACF3':>8}")
for name, x in series_dict.items():
    if name == "带季节":
        d = diff(x, 12)
        label = "季节差分"
    else:
        d = diff(x, 1)
        label = "一阶差分"
    a = acf(d, 3)
    print(f"  {name:<10}{label:<10}" + "".join(f"{v:>8.2f}" for v in a[1:]))

# ---- 平稳性粗略判断 ----
print("\n== 粗略判断（分段均值/方差）==")
def rough_stationarity(x, parts=4):
    chunks = np.array_split(np.asarray(x, dtype=float), parts)
    means = [c.mean() for c in chunks]
    stds = [c.std() for c in chunks]
    mean_shift = max(means) - min(means)
    std_ratio = max(stds) / (min(stds) + 1e-9)
    return means, stds, mean_shift, std_ratio


for name, x in series_dict.items():
    means, stds, shift, ratio = rough_stationarity(x)
    verdict = "可能平稳" if shift < 0.5 * np.std(x) and ratio < 2 else "可能非平稳"
    print(f"  {name:<8} 分段均值范围 {shift:7.2f}，标准差比 {ratio:5.2f} → {verdict}")

# ---- 差分演示 ----
print("\n== 随机游走差分 ==")
rw = random_walk
print("  原始均值/方差：", f"{rw.mean():.2f} / {rw.var():.2f}")
print("  差分均值/方差：", f"{diff(rw).mean():.2f} / {diff(rw).var():.2f}")
print("  差分后方差稳定，ACF 快速衰减 → 接近白噪声")

# ---- 差分阶数选择 ----
print("\n== 差分阶数 ==")
print("  d=0：原序列已平稳")
print("  d=1：线性趋势 / 随机游走 → 一阶差分")
print("  d=2：二次趋势（少见，容易过差分）")
print("  D=1：季节差分（周期 12），与 d 可叠加")

print("\n== 过差分的迹象 ==")
for item in [
    "差分后 ACF 在滞后 1 出现强负相关（如 -0.5）",
    "方差反而变大",
    "序列出现明显的锯齿振荡",
]:
    print("  -", item)

# ---- 与建模的衔接 ----
print("\n== 接下来 ==")
print("  平稳化之后才能用 AR/ARIMA 等模型（第535课）")
print("  季节差分后再做 Holt-Winters 或 SARIMA（第534课）")

# ===== 练习题 =====
# 1. 生成一个二次趋势序列，比较一阶与二阶差分。
# 2. 实现 PACF（偏自相关）的简化版，或说明它与 ACF 的区别。
# 3. 用第531课的分解结果做去趋势+去季节，再算 ACF。
# 4. 思考：为什么“方差随时间变大”的序列要先取对数？
