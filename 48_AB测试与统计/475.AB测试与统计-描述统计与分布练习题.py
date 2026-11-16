# ===== 第475课：AB测试与统计-描述统计与分布 =====
# 知识点：
#   - 描述统计：均值、中位数、标准差、分位数，用几个数字概括一批数据
#   - 均值对极端值敏感；中位数更稳健（收入、房价、响应时间常用中位数）
#   - 标准差衡量波动；分位数（P50/P90/P99）看尾部
#   - 分布形态：对称 vs 右偏（长尾）—— 决定该用均值还是中位数
#   - A/B 实验报告里，“均值 ± 标准差”和“P95”要一起给
# 依赖：无（statistics 标准库）

import random
import statistics

random.seed(42)


def describe(values: list[float], label: str):
    values = sorted(values)
    n = len(values)
    mean = statistics.mean(values)
    median = statistics.median(values)
    stdev = statistics.stdev(values) if n > 1 else 0.0
    p90 = values[int(n * 0.9) - 1] if n > 1 else values[0]
    p99 = values[int(n * 0.99) - 1] if n > 1 else values[0]
    print(f"\n== {label}（n={n}）==")
    print(f"  均值 {mean:.2f} | 中位数 {median:.2f} | 标准差 {stdev:.2f}")
    print(f"  P50 {median:.2f} | P90 {p90:.2f} | P99 {p99:.2f}")
    print(f"  最小 {values[0]:.2f} | 最大 {values[-1]:.2f}")
    return {"mean": mean, "median": median, "stdev": stdev}


# ---- 1. 近似正态：均值 ≈ 中位数 ----
normal_like = [random.gauss(100, 15) for _ in range(500)]
describe(normal_like, "近似正态分布")

# ---- 2. 右偏：少数极端值把均值拉高 ----
skewed = [random.expovariate(1 / 30) for _ in range(500)]       # 长尾
skewed.extend([500, 800, 1200])                                  # 极端值
describe(skewed, "右偏分布（含极端值）")

# ---- 3. 响应时间：为什么看 P95/P99 ----
latency = [random.gauss(80, 10) for _ in range(980)] + [500, 800, 1200, 2000]
describe(latency, "接口响应时间")
print("  说明：均值 80 多毫秒看起来正常，但 P99 已经到秒级 —— 用户体验由尾部决定")

# ---- 4. 分位数计算（statistics.quantiles）----
data = [random.randint(1, 100) for _ in range(100)]
quartiles = statistics.quantiles(data, n=4)
print("\n== 四分位数 ==")
print("  Q1/Q2/Q3：", [round(q, 1) for q in quartiles])
print("  IQR（四分位距）：", round(quartiles[2] - quartiles[0], 1), "（越大越分散）")

# ---- 5. 用直方图看分布（文本版）----
def histogram(values, bins=10, width=40):
    lo, hi = min(values), max(values)
    step = (hi - lo) / bins or 1
    counts = [0] * bins
    for v in values:
        idx = min(bins - 1, int((v - lo) / step))
        counts[idx] += 1
    peak = max(counts) or 1
    print("\n== 分布形态 ==")
    for i, count in enumerate(counts):
        left = lo + i * step
        bar = "█" * int(count / peak * width)
        print(f"  {left:8.1f} | {bar} {count}")


histogram(normal_like, bins=8)
histogram(skewed, bins=8)

# ---- 报告模板 ----
print("\n== A/B 报告里该怎么写 ==")
print("  转化率：12.3%（对照组 10.1%），提升 2.2 个百分点")
print("  样本量：每组 5000")
print("  置信区间：差异 95% CI [0.9pp, 3.5pp]")
print("  不要只写“平均提升 20%” —— 基数和区间同样重要")

# ===== 练习题 =====
# 1. 生成两组不同标准差的数据，比较均值和 P95 的差异。
# 2. 用 statistics.mode 找众数，思考它适合什么数据。
# 3. 写函数 trimmed_mean(values, k)：去掉首尾各 k% 再求均值。
# 4. 思考：为什么“平均工资”常被吐槽，而“工资中位数”更受认可？
