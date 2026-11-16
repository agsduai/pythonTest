# ===== 第537课：时间序列分析-异常检测 =====
# 知识点：
#   - 时间序列异常：点异常（单点突变）、上下文异常（季节中不该出现）、集体异常
#   - 3σ / z-score：偏离滑动均值超过 3 个标准差
#   - IQR：超出 Q1-1.5×IQR 或 Q3+1.5×IQR
#   - 残差法：先分解/平滑，再对残差做阈值（最常用）
#   - 评估用 precision/recall/F1（第431课），不能只看“抓了几个”
#   - 阈值越松召回越高、误报越多，要按业务定
# 依赖：pip install numpy

import numpy as np

rng = np.random.default_rng(41)
n = 120
t = np.arange(n)
season = np.array([-10, -6, -2, 2, 6, 10, 6, 2, -2, -6, -10, -6], dtype=float)
series = 200 + 1.5 * t + np.tile(season, 10) + rng.normal(0, 3, n)

# 注入异常
truth = np.zeros(n, dtype=bool)
for idx in (25, 47, 80, 81, 110):
    series[idx] += 40 if idx % 2 == 0 else -35
    truth[idx] = True
print("== 注入异常的位置 ==", np.where(truth)[0].tolist())


def detect_zscore(series, window=12, threshold=3.0):
    flags = np.zeros(len(series), dtype=bool)
    scores = np.zeros(len(series))
    for i in range(window, len(series)):
        hist = series[i - window:i]
        mu, sd = hist.mean(), hist.std()
        if sd == 0:
            continue
        scores[i] = (series[i] - mu) / sd
        flags[i] = abs(scores[i]) > threshold
    return flags, scores


def detect_iqr(series, k=1.5):
    q1, q3 = np.percentile(series, [25, 75])
    iqr = q3 - q1
    return (series < q1 - k * iqr) | (series > q3 + k * iqr)


def detect_residual(series, window=12, threshold=3.0):
    """用移动平均去趋势/季节，残差超过阈值判异常。"""
    preds = np.full(len(series), np.nan)
    for i in range(window, len(series)):
        preds[i] = series[i - window:i].mean()
    residual = series - preds
    mask = ~np.isnan(residual)
    sd = np.nanstd(residual[mask])
    flags = mask & (np.abs(residual) > threshold * sd)
    return flags, residual


def evaluate(flags, truth):
    tp = int(np.sum(flags & truth))
    fp = int(np.sum(flags & ~truth))
    fn = int(np.sum(~flags & truth))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"TP": tp, "FP": fp, "FN": fn,
            "precision": precision, "recall": recall, "F1": f1}


methods = {
    "z-score（窗口12, 3σ）": detect_zscore(series, 12, 3.0)[0],
    "IQR（全局）": detect_iqr(series),
    "残差法（窗口12, 3σ）": detect_residual(series, 12, 3.0)[0],
}

print("\n== 检测效果 ==")
for name, flags in methods.items():
    m = evaluate(flags, truth)
    print(f"  {name}: TP={m['TP']} FP={m['FP']} FN={m['FN']} | "
          f"P={m['precision']:.2f} R={m['recall']:.2f} F1={m['F1']:.2f}")

# ---- 阈值对效果的影响 ----
print("\n== z-score 阈值扫描 ==")
for th in (2.0, 2.5, 3.0, 3.5, 4.0):
    flags, _ = detect_zscore(series, 12, th)
    m = evaluate(flags, truth)
    print(f"  阈值 {th}: P={m['precision']:.2f} R={m['recall']:.2f} F1={m['F1']:.2f}")

# ---- 查看异常分数 ----
flags, scores = detect_zscore(series, 12, 3.0)
print("\n== 被标记的点及分数 ==")
for i in np.where(flags)[0]:
    mark = "✓" if truth[i] else "✗ 误报"
    print(f"  位置 {i:3d}：值 {series[i]:8.2f}，z={scores[i]:+5.2f} {mark}")

# ---- 异常检测的难点 ----
print("\n== 难点 ==")
for item in [
    "异常定义依赖业务：大促暴涨是异常还是正常？",
    "季节性强的序列，全局阈值会误报（应使用残差）",
    "异常成片出现（集体异常）时，滑动窗口会被污染",
    "标注少 → 用无监督 + 人工复核",
    "告警要分级：高置信自动处理，低置信进人工队列",
]:
    print("  -", item)

# ---- 与第45章数据质量的联系 ----
print("\n== 与其他章节的联系 ==")
print("  数据质量规则（第455课）管“格式/范围”，本课管“时间上的突变”")
print("  异常结果可以写入隔离区，交给业务确认（第456课）")

# ===== 练习题 =====
# 1. 用季节分解后的残差做检测，比较与简单移动平均的差异。
# 2. 实现“连续 3 个点超过 2σ 才告警”，降低误报。
# 3. 把异常检测结果导出 CSV（时间/值/分数/是否异常）。
# 4. 思考：为什么“异常检测”很难用准确率评估？
