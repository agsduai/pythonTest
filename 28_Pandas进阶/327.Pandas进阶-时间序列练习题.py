# ===== 第327课：Pandas进阶-时间序列 =====
# 知识点：
#   - pd.date_range：批量生成日期索引
#   - DatetimeIndex 作行索引后：日期切片、按周/月重采样
#   - resample：按时间粒度聚合（"W" 周 / "ME" 月底）
#   - rolling：移动平均，看趋势不抖动的标准手法
# 依赖：pip install pandas numpy

import numpy as np
import pandas as pd

# 30 天的日销量
rng = np.random.default_rng(1)
idx = pd.date_range("2026-11-01", periods=30, freq="D")
sales = pd.Series(rng.integers(100, 500, size=30), index=idx, name="销量")
print(sales.head(3), end="\n\n")

# ---- 日期切片：像切字符串一样自然 ----
print("11月10日~12日：", sales["2026-11-10":"2026-11-12"].to_dict(), sep="\n")

# ---- 重采样：按周汇总 ----
print("按周汇总：", sales.resample("W").sum().to_dict(), sep="\n")

# ---- 移动平均：7 日均线 ----
print("7 日均线（最后3天）：", sales.rolling(7).mean().round(1).tail(3).to_dict(), sep="\n")

# ---- 找出销量最高的日期与“周最高” ----
print("销量峰值日：", sales.idxmax().date(), "=", sales.max())
print("最强一周：", sales.resample("W").sum().idxmax().date())

# 与字符串日期互转（第230课 strftime 的 pandas 版）
print("日期类型：", sales.index.dtype, "| 转字符串：", sales.index.strftime("%m/%d")[:3].tolist())

# ===== 练习题 =====
# 1. 用 resample("ME") 造一份“跨越三个月”的月度汇总。
# 2. 给 7 日均线加“超过均线视为热销”的布尔列。
# 3. 思考：rolling 和 resample 的区别？（滑动 vs 降粒度）
