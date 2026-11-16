# ===== 第538课：时间序列分析-综合案例-销售预测 =====
# 知识点：
#   - 综合运用：分解（531）+ 差分/平稳（532）+ 指数平滑（533）
#     + Holt-Winters（534）+ 回测（536）+ 异常检查（537）
#   - 流程：造数/清洗 → 分解 → 训练/验证切分 → 基线 → 模型 → 回测 → 预测
#   - 预测不是终点：要给出误差范围、基线对比、业务解释
#   - 输出：未来 6 个月预测 + 指标报告 + CSV
#   - 与第28课 pandas 时间序列、第52课指标口径的配合
# 依赖：pip install numpy
import csv
import tempfile
from pathlib import Path

import numpy as np

rng = np.random.default_rng(2026)

# ---------------- 1. 构造 48 个月销售数据 ----------------
months = 48
t = np.arange(months)
season = np.array([-20, -14, -8, 0, 8, 14, 20, 14, 8, 0, -8, -14], dtype=float)
trend = 300 + 4.0 * t
noise = rng.normal(0, 8, months)
sales = trend + np.tile(season, 4) + noise

# 注入两个异常点
sales[30] += 60
sales[41] -= 50
print("== 数据概况 ==")
print(f"  月数 {months}，范围 {sales.min():.0f} ~ {sales.max():.0f}")
print("  前 6 个月：", sales[:6].round(1))


# ---------------- 2. 简单异常处理（3σ 残差） ----------------
def clean_outliers(series, window=12, threshold=3.0):
    cleaned = series.copy()
    outliers = []
    for i in range(window, len(series)):
        hist = series[i - window:i]
        mu, sd = hist.mean(), hist.std()
        if sd and abs(series[i] - mu) > threshold * sd:
            cleaned[i] = mu
            outliers.append(i)
    return cleaned, outliers


clean, outliers = clean_outliers(sales)
print(f"\n== 异常处理 ==\n  修正位置：{outliers}")


# ---------------- 3. 分解：趋势 + 季节 ----------------
def decompose_additive(series, period=12):
    weights = np.ones(period) / period
    ma = np.convolve(series, weights, mode="valid")
    pad = period // 2
    trend = np.r_[np.full(pad, np.nan), ma, np.full(len(series) - len(ma) - pad, np.nan)]
    detrended = series - trend
    seasonal = np.zeros(period)
    for m in range(period):
        seasonal[m] = np.nanmean(detrended[m::period])
    seasonal -= seasonal.mean()
    residual = series - trend - np.tile(seasonal, len(series) // period)
    return trend, seasonal, residual


trend_est, seasonal_est, residual = decompose_additive(clean)
print("\n== 分解结果 ==")
print("  季节因子：", seasonal_est.round(1))
print(f"  残差标准差：{np.nanstd(residual):.2f}")
print("  解释：1 月最低、7 月最高，符合“夏季旺季”的业务假设")


# ---------------- 4. Holt-Winters 模型 ----------------
def holt_winters(series, period=12, alpha=0.3, beta=0.1, gamma=0.2, horizon=6):
    n = len(series)
    level = series[:period].mean()
    trend = (series[period:2 * period].mean() - level) / period
    seasonals = [series[i] - level for i in range(period)]
    for i in range(n):
        s = seasonals[i % period]
        new_level = alpha * (series[i] - s) + (1 - alpha) * (level + trend)
        new_trend = beta * (new_level - level) + (1 - beta) * trend
        seasonals[i % period] = gamma * (series[i] - new_level) + (1 - gamma) * s
        level, trend = new_level, new_trend
    forecasts = [level + h * trend + seasonals[(h - 1) % period]
                 for h in range(1, horizon + 1)]
    return np.array(forecasts), (level, trend, seasonals)


# ---------------- 5. 训练/验证切分与基线 ----------------
train, valid = clean[:36], clean[36:]
print("\n== 训练/验证 ==")
print(f"  训练 36 个月，验证 12 个月")

baseline = np.array([train[-12 + i % 12] for i in range(12)])
hw_valid, state = holt_winters(train, horizon=12)
mae_base = np.mean(np.abs(baseline - valid))
mae_hw = np.mean(np.abs(hw_valid - valid))
print(f"  季节朴素基线 MAE：{mae_base:.2f}")
print(f"  Holt-Winters MAE：{mae_hw:.2f}")


def metrics(actual, pred):
    mae = np.mean(np.abs(actual - pred))
    rmse = np.sqrt(np.mean((actual - pred) ** 2))
    mape = np.mean(np.abs((actual - pred) / actual)) * 100
    return mae, rmse, mape


print("\n== 验证集指标 ==")
for name, pred in (("季节朴素", baseline), ("Holt-Winters", hw_valid)):
    mae, rmse, mape = metrics(valid, pred)
    print(f"  {name:14s} MAE {mae:6.2f} | RMSE {rmse:6.2f} | MAPE {mape:5.2f}%")

# ---------------- 6. 用全量数据重训并预测未来 6 个月 ----------------
future_pred, final_state = holt_winters(clean, horizon=6)
print("\n== 未来 6 个月预测 ==")
for i, value in enumerate(future_pred, 1):
    print(f"  第 {i} 个月：{value:.1f}")

# 误差范围：用验证集残差标准差近似
residual_std = np.std(valid - hw_valid)
print(f"\n  参考区间（±1.96σ）：[{future_pred[0] - 1.96 * residual_std:.1f}, "
      f"{future_pred[0] + 1.96 * residual_std:.1f}]（首月）")

# ---------------- 7. 输出报告与 CSV ----------------
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    csv_path = tmp / "forecast.csv"
    report_path = tmp / "report.md"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["月份序号", "预测销售额"])
        for i, value in enumerate(future_pred, 1):
            writer.writerow([i, round(float(value), 2)])

    report = [
        "# 销售预测报告",
        "",
        f"- 历史数据：{months} 个月，异常点 {len(outliers)} 个（已修正）",
        f"- 季节因子：{seasonal_est.round(1).tolist()}",
        f"- 验证集 MAE：Holt-Winters {mae_hw:.2f}，基线 {mae_base:.2f}",
        f"- 未来 6 个月预测：{[round(float(v), 1) for v in future_pred]}",
        f"- 建议：7 月旺季提前备货；1 月淡季控制库存",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n== 报告 ==")
    print(report_path.read_text(encoding="utf-8"))
    print("CSV 行数：", len(csv_path.read_text(encoding="utf-8-sig").splitlines()))

# ---------------- 8. 分析清单 ----------------
print("== 预测项目清单 ==")
for item in [
    "1. 数据检查：缺失、异常、口径变更",
    "2. 分解：确认趋势与季节性是否稳定",
    "3. 切分：按时间切，不能随机",
    "4. 基线：naive/季节 naive 必须先跑",
    "5. 模型：Holt-Winters/ARIMA/ML，用回测选",
    "6. 评估：MAE/RMSE/MAPE + 业务可解释性",
    "7. 输出：预测值 + 区间 + 假设 + 建议",
    "8. 上线后持续监控误差，分布漂移要重训",
]:
    print("  ", item)

# ===== 练习题 =====
# 1. 用网格搜索找最优 (α, β, γ)，比较验证 MAE。
# 2. 把预测区间改成 ±2σ，并输出到 CSV。
# 3. 加入“促销月”虚拟变量，观察预测是否更准。
# 4. 思考：为什么销售预测报告必须写清“假设”和“误差范围”？
