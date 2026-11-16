# ===== 第536课：时间序列分析-评估与回测 =====
# 知识点：
#   - 时间序列不能随机划分：必须按时间切（过去训练、未来测试）
#   - 滚动 origin 回测：不断把预测起点往后移，模拟真实上线
#   - 基线：naive（上一期）、seasonal naive（去年同月）、均值、移动平均
#   - 指标：MAE、RMSE、MAPE（注意 0 值）、sMAPE
#   - 模型必须打过基线才算有价值
#   - 与第475课描述统计、第527课离线评估的思路一致
# 依赖：pip install numpy

import numpy as np

rng = np.random.default_rng(31)
n = 48
t = np.arange(n)
season = np.array([-12, -8, -4, 0, 4, 8, 12, 8, 4, 0, -4, -8], dtype=float)
series = 100 + 1.5 * t + np.tile(season, 4) + rng.normal(0, 3, n)


def metrics(actual, pred):
    actual, pred = np.asarray(actual, float), np.asarray(pred, float)
    mae = np.mean(np.abs(actual - pred))
    rmse = np.sqrt(np.mean((actual - pred) ** 2))
    mask = actual != 0
    mape = np.mean(np.abs((actual[mask] - pred[mask]) / actual[mask])) * 100 if mask.any() else float("nan")
    smape = np.mean(2 * np.abs(actual - pred) / (np.abs(actual) + np.abs(pred) + 1e-9)) * 100
    return {"MAE": mae, "RMSE": rmse, "MAPE%": mape, "sMAPE%": smape}


# ---------------- 基线预测器 ----------------
def naive(train, horizon):
    return np.repeat(train[-1], horizon)


def seasonal_naive(train, horizon, season_length=12):
    return np.array([train[-season_length + i % season_length] for i in range(horizon)])


def mean_forecast(train, horizon):
    return np.repeat(np.mean(train), horizon)


def sma_forecast(train, horizon, window=6):
    level = np.mean(train[-window:])
    return np.repeat(level, horizon)


FORECASTERS = {
    "naive": naive,
    "seasonal_naive": seasonal_naive,
    "mean": mean_forecast,
    "sma6": sma_forecast,
}

# ---------------- 单次切分评估 ----------------
print("== 单次切分（前 36 训练，后 12 测试）==")
train, test = series[:36], series[36:]
for name, fn in FORECASTERS.items():
    pred = fn(train, len(test))
    m = metrics(test, pred)
    print(f"  {name:14s} MAE {m['MAE']:6.2f} | RMSE {m['RMSE']:6.2f} | "
          f"MAPE {m['MAPE%']:6.2f}%")

# ---------------- 滚动 origin 回测 ----------------
def rolling_backtest(series, forecaster, initial_train=24, horizon=1):
    actual, pred = [], []
    for start in range(initial_train, len(series) - horizon + 1):
        train = series[:start]
        forecast = forecaster(train, horizon)
        actual.extend(series[start:start + horizon])
        pred.extend(forecast)
    return np.array(actual), np.array(pred)


print("\n== 滚动回测（初始 24，步长 1，预测 1 期）==")
results = {}
for name, fn in FORECASTERS.items():
    actual, pred = rolling_backtest(series, fn, initial_train=24, horizon=1)
    results[name] = metrics(actual, pred)
    m = results[name]
    print(f"  {name:14s} MAE {m['MAE']:6.2f} | RMSE {m['RMSE']:6.2f}")

best = min(results, key=lambda k: results[k]["MAE"])
print(f"\n  最优基线：{best}（MAE {results[best]['MAE']:.2f}）")

# ---- 多步回测 ----
print("\n== 多步回测（预测 3 期）==")
for name, fn in FORECASTERS.items():
    actual, pred = rolling_backtest(series, fn, initial_train=24, horizon=3)
    m = metrics(actual, pred)
    print(f"  {name:14s} MAE {m['MAE']:6.2f} | MAPE {m['MAPE%']:6.2f}%")

# ---- 误差随预测步长增加 ----
print("\n== 误差随步长增加（seasonal_naive）==")
for h in (1, 2, 3, 6, 12):
    actual, pred = rolling_backtest(series, seasonal_naive, initial_train=24, horizon=h)
    m = metrics(actual, pred)
    print(f"  预测 {h:2d} 期：MAE {m['MAE']:6.2f}，MAPE {m['MAPE%']:6.2f}%")

# ---- 指标选择 ----
print("\n== 指标选择 ==")
rows = [
    ("MAE", "平均绝对误差", "同单位、易解释", "受量纲影响"),
    ("RMSE", "均方根误差", "惩罚大误差", "受极端值影响"),
    ("MAPE", "平均绝对百分比误差", "跨序列可比", "0 值/接近 0 时爆炸"),
    ("sMAPE", "对称 MAPE", "缓解 MAPE 偏差", "仍有局限"),
]
print(f"  {'指标':<8}{'含义':<16}{'优点':<18}{'缺点'}")
for r in rows:
    print(f"  {r[0]:<8}{r[1]:<16}{r[2]:<18}{r[3]}")

# ---- 回测注意 ----
print("\n== 回测注意 ==")
for item in [
    "绝不能随机打乱时间顺序（数据泄漏）",
    "预处理（归一化/差分）只能用训练段统计量",
    "多步预测的误差会累积，按业务关注步长评估",
    "基线很强时，复杂模型的收益可能很小",
    "线上还要看 A/B（第482课），离线好不等于线上好",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 增加“漂移法”基线（最后值 + 平均变化量）。
# 2. 实现带置信区间的预测（用残差标准差）。
# 3. 比较 horizon=1 与 horizon=12 时各基线的排名。
# 4. 思考：为什么“回测很好”的模型上线后可能翻车？
