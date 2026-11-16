# ===== 第480课：AB测试与统计-样本量与功效 =====
# 知识点：
#   - 功效（power）：真实存在差异时，实验能检测出来的概率（常用 80%）
#   - 样本量太小 → 检出不了真实差异（假阴性）；太大 → 浪费流量/时间
#   - 关键参数：基线转化率 p1、最小可检测提升 MDE、α、power
#   - 两比例样本量公式（正态近似）：
#       n = (z_{1-α/2} + z_{power})² × [p1(1-p1) + p2(1-p2)] / (p2-p1)²
#   - 样本量翻 4 倍，可检测的差异约减半（√n 效应，第476课）
#   - 先算样本量再开实验，避免“跑了一周发现不够”
# 依赖：无（statistics.NormalDist 提供正态分位数）

from statistics import NormalDist

NORMAL = NormalDist()


def required_sample_size(p1: float, p2: float, alpha: float = 0.05,
                         power: float = 0.8) -> int:
    """每组所需样本量（双侧检验）。"""
    if not (0 < p1 < 1 and 0 < p2 < 1):
        raise ValueError("转化率必须在 (0,1) 内")
    if p1 == p2:
        raise ValueError("两组转化率不能相同")
    z_alpha = NORMAL.inv_cdf(1 - alpha / 2)
    z_power = NORMAL.inv_cdf(power)
    p_bar = (p1 + p2) / 2
    numerator = (z_alpha * (2 * p_bar * (1 - p_bar)) ** 0.5
                 + z_power * (p1 * (1 - p1) + p2 * (1 - p2)) ** 0.5) ** 2
    return int(numerator / (p2 - p1) ** 2) + 1


def power_for_n(p1: float, p2: float, n: int, alpha: float = 0.05) -> float:
    """给定每组样本量，计算能检出 p1→p2 的功效。"""
    p_bar = (p1 + p2) / 2
    se0 = (2 * p_bar * (1 - p_bar) / n) ** 0.5
    se1 = ((p1 * (1 - p1) + p2 * (1 - p2)) / n) ** 0.5
    if se1 == 0:
        return 1.0
    z_alpha = NORMAL.inv_cdf(1 - alpha / 2)
    z = abs(p2 - p1) / se1 - z_alpha * se0 / se1
    return NORMAL.cdf(z)


print("== 基线 10%，想检测不同提升幅度 ==")
baseline = 0.10
for mde in (0.01, 0.02, 0.03, 0.05):
    n = required_sample_size(baseline, baseline + mde)
    print(f"  10% → {baseline + mde:.0%}（+{mde * 100:.0f}pp）：每组 {n:,} 人")

print("\n== 相对提升 20%（10% → 12%）==")
n = required_sample_size(0.10, 0.12)
print(f"  每组样本量：{n:,}")
print(f"  总样本量：{n * 2:,}")

# ---- 流量与实验时长 ----
print("\n== 实验时长估算 ==")
daily_traffic = 5000
for groups in (2,):
    days = n * groups / daily_traffic
    print(f"  日活 {daily_traffic:,}、{groups} 组 → 约需 {days:.1f} 天（按 100% 分流）")
    print(f"  若只分流 50%：约需 {days * 2:.1f} 天")
print("  注意：实验至少覆盖一个完整周（工作日/周末行为不同）")

# ---- 功效随样本量变化 ----
print("\n== 功效曲线（10% → 12%，α=0.05）==")
for n_test in (1000, 2000, 3000, 4000, 5000, 8000):
    pwr = power_for_n(0.10, 0.12, n_test)
    bar = "█" * int(pwr * 30)
    print(f"  n={n_test:5,} → 功效 {pwr:.0%} {bar}")

# ---- α 与功效的权衡 ----
print("\n== α 越小，需要样本越多 ==")
for alpha in (0.10, 0.05, 0.01):
    n_a = required_sample_size(0.10, 0.12, alpha=alpha)
    print(f"  α={alpha:.2f} → 每组 {n_a:,}")

# ---- 常见错误 ----
print("\n== 常见错误 ==")
for item in [
    "先跑实验再看能检测多大差异（应该先算样本量）",
    "用“相对提升”算样本量却忽略基线：5%→6% 比 50%→60% 难得多",
    "中途偷看数据、显著就停（会抬高假阳性，需序贯检验）",
    "忽略分流比例与埋点丢失，实际有效样本远小于计划",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 计算基线 5%、MDE +1pp 所需样本量，和基线 50% 的情况对比。
# 2. 画“MDE-样本量”曲线（用文本柱状图）。
# 3. 实现单侧检验版本的样本量公式。
# 4. 思考：为什么“样本量不够”时看到 p<0.05 反而更可疑？
