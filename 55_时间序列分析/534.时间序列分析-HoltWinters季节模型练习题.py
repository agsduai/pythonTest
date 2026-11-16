# ===== 第534课：时间序列分析-Holt-Winters季节模型 =====
# 知识点：
#   - Holt-Winters = 水平 + 趋势 + 季节 三项指数平滑
#   - 加法模型：季节项是绝对量（y = L + T + S）
#   - 乘法模型：季节项是比例（y = (L + T) × S），适合波动随规模放大
#   - 三个平滑系数：α（水平）、β（趋势）、γ（季节）
#   - 初始化：用第一个周期的均值做水平，季节项 = 实际 - 水平
#   - 预测：L + h×T + S_{(t+h) mod m}
#   - 与第531课分解、第533课 Holt 的关系
# 依赖：pip install numpy

import numpy as np


def holt_winters_additive(series, season_length=12, alpha=0.3, beta=0.1, gamma=0.1):
    """返回 (一步预测序列, 最终状态, 参数)。"""
    y = np.asarray(series, dtype=float)
    n = len(y)
    if n < 2 * season_length:
        raise ValueError("数据至少需要两个完整季节周期")

    level = y[:season_length].mean()
    trend = (y[season_length:2 * season_length].mean() - level) / season_length
    seasonals = [y[i] - level for i in range(season_length)]

    preds = np.full(n, np.nan)
    for i in range(n):
        s = seasonals[i % season_length]
        preds[i] = level + trend + s
        new_level = alpha * (y[i] - s) + (1 - alpha) * (level + trend)
        new_trend = beta * (new_level - level) + (1 - beta) * trend
        seasonals[i % season_length] = gamma * (y[i] - new_level) + (1 - gamma) * s
        level, trend = new_level, new_trend

    return preds, (level, trend, seasonals)


def forecast_hw(state, h, season_length=12):
    level, trend, seasonals = state
    return [level + step * trend + seasonals[(step - 1) % season_length]
            for step in range(1, h + 1)]


def mae(actual, pred):
    mask = ~np.isnan(pred)
    return float(np.mean(np.abs(np.asarray(actual)[mask] - pred[mask])))


# ---- 构造 3 年数据：趋势 + 季节 + 噪声 ----
rng = np.random.default_rng(21)
months = 36
t = np.arange(months)
season = np.array([-15, -10, -5, 0, 5, 10, 15, 10, 5, 0, -5, -10], dtype=float)
y = 200 + 2.0 * t + np.tile(season, 3) + rng.normal(0, 4, months)

print("== 数据 ==")
print("  前 12 个月：", y[:12].round(1))

# ---- 训练前 24 个月，预测后 12 个月 ----
train, test = y[:24], y[24:]
preds, state = holt_winters_additive(train, 12, alpha=0.3, beta=0.1, gamma=0.3)
print(f"\n训练集（前 24 月）一步预测 MAE：{mae(train, preds):.3f}")

forecast = np.array(forecast_hw(state, 12))
print("\n== 未来 12 个月预测 vs 真实 ==")
print(f"  {'月':>3}{'预测':>10}{'真实':>10}{'误差':>10}")
for i in range(12):
    print(f"  {i + 1:>3}{forecast[i]:>10.2f}{test[i]:>10.2f}{forecast[i] - test[i]:>+10.2f}")
print(f"\n  测试集 MAE：{np.mean(np.abs(forecast - test)):.3f}")

# ---- 参数敏感性 ----
print("\n== 参数影响（测试集 MAE）==")
for params in ((0.1, 0.05, 0.1), (0.3, 0.1, 0.3), (0.6, 0.2, 0.6)):
    a, b, g = params
    _, st = holt_winters_additive(train, 12, a, b, g)
    f = forecast_hw(st, 12)
    err = np.mean(np.abs(np.array(f) - test))
    print(f"  α={a}, β={b}, γ={g} → MAE {err:.3f}")

# ---- 加法 vs 乘法 ----
print("\n== 加法 vs 乘法 ==")
print("  加法：季节波动幅度固定，适合“每月固定多/少若干”")
print("  乘法：季节波动按比例放大，适合“旺季是淡季的 N 倍”")
print("  判断：画出序列，波峰波谷的差距随趋势增大 → 乘法")
print("  乘法实现：先 log 变换，再用加法模型，预测后 exp 还原")

# ---- 与简单方法的对比 ----
print("\n== 与基线对比 ==")
def seasonal_naive(series, season_length=12, h=12):
    return np.array([series[-season_length + (i % season_length)] for i in range(h)])

baseline = seasonal_naive(train, 12, 12)
print(f"  季节朴素基线 MAE：{np.mean(np.abs(baseline - test)):.3f}")
print(f"  Holt-Winters MAE：{np.mean(np.abs(forecast - test)):.3f}")
print("  预测模型至少要打过“去年同月”这个基线，否则没有价值")

# ---- 初始化与数据要求 ----
print("\n== 使用注意 ==")
for item in [
    "至少两个完整周期（月度数据至少 24 个月）",
    "异常值会污染初始季节项，先清洗",
    "α/β/γ 用验证集网格搜索，不要手调",
    "长期预测误差会累积，通常只信未来 1~2 个周期",
    "趋势突变（疫情/促销）需要加干预变量或重新训练",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 用乘法模型处理本数据（log 变换），比较 MAE。
# 2. 网格搜索 (α, β, γ) 各取 0.1/0.3/0.5，找最优组合。
# 3. 把季节周期改成 4（季度数据），重跑。
# 4. 思考：为什么 Holt-Winters 的长期预测会越来越“直”？
