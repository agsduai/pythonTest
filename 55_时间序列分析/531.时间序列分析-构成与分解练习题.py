# ===== 第531课：时间序列分析-构成与分解 =====
# 知识点：
#   - 时间序列 = 趋势（Trend）+ 季节（Seasonality）+ 周期（Cycle）+ 噪声（Residual）
#   - 加法模型：y = T + S + R（季节波动幅度大致固定）
#   - 乘法模型：y = T × S × R（季节波动随趋势放大，如销售额）
#   - 分解步骤：移动平均提取趋势 → 去趋势 → 按月平均得季节因子 → 残差
#   - 分解的价值：看清“增长是真趋势还是季节性”，预测才有依据
#   - 与第28课重采样、第475课描述统计的联系
# 依赖：pip install numpy

import numpy as np

rng = np.random.default_rng(7)

# ---- 构造 48 个月数据：上升趋势 + 月度季节 + 噪声 ----
months = 48
t = np.arange(months)
trend = 100 + 1.8 * t
season_pattern = np.array([-18, -12, -6, 0, 6, 12, 18, 12, 6, 0, -6, -12], dtype=float)
season = np.tile(season_pattern, months // 12)
noise = rng.normal(0, 3, months)
series = trend + season + noise

print("== 前 12 个月 ==")
for i in range(12):
    print(f"  第{i + 1:2d}月：{series[i]:7.2f}（趋势 {trend[i]:6.1f} + 季节 {season[i]:+5.1f} + 噪声 {noise[i]:+5.2f}）")


def centered_moving_average(x: np.ndarray, window: int = 12) -> np.ndarray:
    """居中移动平均：用卷积算，再按窗口居中补齐。"""
    weights = np.ones(window) / window
    ma = np.convolve(x, weights, mode="valid")
    pad_left = window // 2
    pad_right = len(x) - len(ma) - pad_left
    return np.r_[np.full(pad_left, np.nan), ma, np.full(pad_right, np.nan)]


ma = centered_moving_average(series, 12)

# ---- 去趋势，按月份求平均季节因子 ----
detrended = series - ma
seasonal_factors = np.zeros(12)
for m in range(12):
    values = detrended[m::12]
    seasonal_factors[m] = np.nanmean(values)
# 加法模型要求季节因子和为 0，做中心化
seasonal_factors -= seasonal_factors.mean()
residual = series - ma - np.tile(seasonal_factors, months // 12)

print("\n== 提取出的季节因子（加法模型）==")
for m in range(12):
    bar = "█" * int(abs(seasonal_factors[m]) * 2)
    sign = "+" if seasonal_factors[m] >= 0 else "-"
    print(f"  {m + 1:2d}月：{seasonal_factors[m]:+6.2f} {sign}{bar}")

print("\n== 分解质量 ==")
print(f"  原始序列标准差：{series.std():.2f}")
print(f"  趋势（移动平均）标准差：{np.nanstd(ma):.2f}")
print(f"  残差标准差：{np.nanstd(residual):.2f}")
print(f"  季节因子范围：{seasonal_factors.min():.1f} ~ {seasonal_factors.max():.1f}")
print(f"  真实季节范围：{season_pattern.min():.1f} ~ {season_pattern.max():.1f}")

# ---- 可视化（文本折线）----
def sparkline(values, width=48):
    values = np.asarray(values, dtype=float)
    lo, hi = np.nanmin(values), np.nanmax(values)
    levels = "▁▂▃▄▅▆▇█"
    chars = []
    for v in values:
        if np.isnan(v):
            chars.append(" ")
        else:
            idx = int((v - lo) / (hi - lo + 1e-9) * (len(levels) - 1))
            chars.append(levels[idx])
    return "".join(chars)


print("\n== 形态 ==")
print("  原始：", sparkline(series))
print("  趋势：", sparkline(ma))
print("  季节：", sparkline(np.tile(seasonal_factors, months // 12)))

# ---- 加法 vs 乘法 ----
print("\n== 加法 vs 乘法 ==")
print("  加法：季节波动固定（如每月固定多卖 100 件）")
print("  乘法：季节波动是比例的（如 12 月是平时的 1.5 倍）")
print("  判断：画出序列，波动幅度随趋势变大 → 先取对数再加法分解")

# ===== 练习题 =====
# 1. 把噪声标准差改成 8，观察残差占比变化。
# 2. 用乘法模型重做：y/(T) 后求季节因子。
# 3. 把移动平均窗口改成 6，观察趋势线是否更贴合。
# 4. 思考：为什么分解前要先判断加法还是乘法模型？
