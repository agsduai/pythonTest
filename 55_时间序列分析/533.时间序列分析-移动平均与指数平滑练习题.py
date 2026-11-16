# ===== 第533课：时间序列分析-移动平均与指数平滑 =====
# 知识点：
#   - 简单移动平均（SMA）：最近 k 期平均，平滑但滞后
#   - 加权移动平均：近期权重更高
#   - 简单指数平滑（SES）：level = α·y + (1-α)·level，只需存一个状态
#   - α 越大越跟手（对噪声敏感），越小越平滑（滞后大）
#   - Holt 线性趋势：在 SES 上增加 trend 项，适合带趋势的序列
#   - 评估：一步预测 MAE / RMSE（第536课系统展开）
# 依赖：pip install numpy

import numpy as np

rng = np.random.default_rng(11)
n = 60
# 带趋势 + 噪声的序列
y = 50 + 1.2 * np.arange(n) + rng.normal(0, 4, n)


def sma_forecast(series, window):
    """用前 window 个值的均值预测下一个点。"""
    preds = np.full(len(series), np.nan)
    for i in range(window, len(series)):
        preds[i] = series[i - window:i].mean()
    return preds


def wma_forecast(series, window):
    weights = np.arange(1, window + 1, dtype=float)
    weights /= weights.sum()
    preds = np.full(len(series), np.nan)
    for i in range(window, len(series)):
        preds[i] = np.dot(series[i - window:i], weights)
    return preds


def ses_forecast(series, alpha):
    """返回一步预测序列（preds[i] 用 i 之前的信息）。"""
    preds = np.full(len(series), np.nan)
    level = series[0]
    for i in range(1, len(series)):
        preds[i] = level
        level = alpha * series[i] + (1 - alpha) * level
    return preds, level


def holt_forecast(series, alpha=0.3, beta=0.1):
    preds = np.full(len(series), np.nan)
    level = series[0]
    trend = series[1] - series[0]
    for i in range(1, len(series)):
        preds[i] = level + trend
        new_level = alpha * series[i] + (1 - alpha) * (level + trend)
        trend = beta * (new_level - level) + (1 - beta) * trend
        level = new_level
    return preds, level, trend


def mae(actual, pred):
    mask = ~np.isnan(pred)
    return float(np.mean(np.abs(actual[mask] - pred[mask])))


print("== 移动平均（窗口 5）==")
for name, preds in (("SMA", sma_forecast(y, 5)), ("WMA", wma_forecast(y, 5))):
    print(f"  {name} MAE：{mae(y, preds):.3f}")

print("\n== SES：不同 α ==")
for alpha in (0.1, 0.3, 0.6, 0.9):
    preds, last_level = ses_forecast(y, alpha)
    print(f"  α={alpha:.1f} → MAE {mae(y, preds):.3f}，下一期预测 {last_level:.2f}")

print("\n== Holt 线性趋势 ==")
preds_h, level_h, trend_h = holt_forecast(y, alpha=0.3, beta=0.1)
print(f"  MAE：{mae(y, preds_h):.3f}")
print(f"  当前水平 {level_h:.2f}，趋势 {trend_h:.2f}")
print("  未来 3 期预测：", [round(level_h + h * trend_h, 2) for h in (1, 2, 3)])

# ---- 对比：SES 在趋势序列上的滞后 ----
print("\n== 为什么 SES 不适合强趋势 ==")
preds_ses, _ = ses_forecast(y, 0.3)
print("  真实最后 5 个：", y[-5:].round(1))
print("  SES 预测最后 5 个：", preds_ses[-5:].round(1))
print("  预测系统性偏低 → 因为它只会跟水平，不会外推趋势")

# ---- α 的直观影响 ----
print("\n== α 的影响 ==")
for alpha in (0.1, 0.9):
    preds, _ = ses_forecast(y, alpha)
    # 看预测的波动（标准差）
    print(f"  α={alpha}: 预测值标准差 {np.nanstd(preds):.2f}"
          f"（越小越平滑）")

# ---- 选择建议 ----
print("\n== 选择建议 ==")
for item in [
    "无明显趋势、短期预测 → SES，α 用 0.2~0.5",
    "有明显趋势 → Holt（水平 + 趋势）",
    "有季节 → Holt-Winters（第534课）",
    "数据抖动大 → α 小一些；变化快 → α 大一些",
    "用验证集选 α，不要凭感觉（第536课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把窗口改成 3 和 12，比较 SMA 的 MAE。
# 2. 用网格搜索找 SES 的最优 α（步长 0.05）。
# 3. 实现阻尼趋势 Holt（trend 每期乘 φ）。
# 4. 思考：为什么指数平滑只需要存“水平+趋势”，而 AR 需要存多个滞后？
