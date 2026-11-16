# ===== 第478课：AB测试与统计-两样本t检验 =====
# 知识点：
#   - 两样本 t 检验：比较两组均值是否有显著差异
#   - Welch t 检验：不假设两组方差相等（更稳妥，默认选它）
#   - t 统计量 = 均值差 / 标准误；自由度用 Welch 公式近似
#   - p 值由 t 分布计算；样本大时接近正态
#   - 效应量 Cohen's d：差异相对于波动的倍数，回答“差异有多大”
#   - 前提：观测近似独立；严重偏态/极端值要用 Bootstrap（第476课）
# 依赖：无（math 标准库实现 t 分布）

import math
import random
import statistics


# ---------------- t 分布 CDF（正则化不完全 Beta）----------------
def _betacf(a, b, x, max_iter=200, eps=3e-12):
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < 1e-30:
        d = 1e-30
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1e-30 if abs(d) < 1e-30 else d
        c = 1.0 + aa / c
        c = 1e-30 if abs(c) < 1e-30 else c
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1e-30 if abs(d) < 1e-30 else d
        c = 1.0 + aa / c
        c = 1e-30 if abs(c) < 1e-30 else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _betai(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    bt = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log(1 - x)
    )
    if x < (a + 1) / (a + b + 2):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1 - x) / b


def t_two_sided_p(t: float, df: float) -> float:
    """双侧 p 值。"""
    x = df / (df + t * t)
    return _betai(df / 2.0, 0.5, x)


def welch_ttest(a: list[float], b: list[float]):
    n1, n2 = len(a), len(b)
    m1, m2 = statistics.mean(a), statistics.mean(b)
    v1, v2 = statistics.variance(a), statistics.variance(b)
    se = math.sqrt(v1 / n1 + v2 / n2)
    if se == 0:
        return 0.0, 1.0, float("nan")
    t = (m1 - m2) / se
    df = (v1 / n1 + v2 / n2) ** 2 / (
        (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
    )
    p = t_two_sided_p(t, df)
    return t, p, df


def cohens_d(a, b):
    n1, n2 = len(a), len(b)
    s1, s2 = statistics.variance(a), statistics.variance(b)
    pooled = math.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))
    return (statistics.mean(a) - statistics.mean(b)) / pooled if pooled else 0.0


# ---- 自检：已知值 ----
print("== t 分布自检 ==")
print(f"  t=2.0, df=10 → 双侧 p = {t_two_sided_p(2.0, 10):.4f}（参考 0.0734）")
print(f"  t=1.96, df=1000 → p = {t_two_sided_p(1.96, 1000):.4f}（接近 0.05）")

# ---- 场景 1：两组均值有差异 ----
random.seed(11)
control = [random.gauss(100, 15) for _ in range(120)]
treatment = [random.gauss(106, 15) for _ in range(120)]
t, p, df = welch_ttest(treatment, control)
d = cohens_d(treatment, control)
print("\n== 场景 1：均值 100 vs 106 ==")
print(f"  均值：{statistics.mean(control):.2f} vs {statistics.mean(treatment):.2f}")
print(f"  t = {t:.3f}，df = {df:.1f}，p = {p:.4f}")
print(f"  Cohen's d = {d:.2f}（0.2 小 / 0.5 中 / 0.8 大）")
print(f"  结论：{'差异显著' if p < 0.05 else '差异不显著'}")

# ---- 场景 2：差异小、样本小 ----
control2 = [random.gauss(100, 20) for _ in range(20)]
treatment2 = [random.gauss(102, 20) for _ in range(20)]
t2, p2, df2 = welch_ttest(treatment2, control2)
print("\n== 场景 2：小样本 + 小差异 ==")
print(f"  t = {t2:.3f}，df = {df2:.1f}，p = {p2:.4f}")
print(f"  结论：{'显著' if p2 < 0.05 else '不显著（样本不足，别急着下结论）'}")

# ---- 场景 3：大样本 + 微小差异 ----
control3 = [random.gauss(100, 15) for _ in range(5000)]
treatment3 = [random.gauss(100.5, 15) for _ in range(5000)]
t3, p3, df3 = welch_ttest(treatment3, control3)
print("\n== 场景 3：大样本 + 0.5 的微小差异 ==")
print(f"  t = {t3:.3f}，p = {p3:.6f}，d = {cohens_d(treatment3, control3):.3f}")
print("  显著但效应量很小：是否上线要看业务收益与成本")

# ---- 与置换检验交叉验证 ----
print("\n== 与置换检验对比（场景 1）==")
combined = control + treatment
n_c = len(control)
count = 0
observed = statistics.mean(treatment) - statistics.mean(control)
for _ in range(2000):
    shuffled = combined[:]
    random.shuffle(shuffled)
    diff = statistics.mean(shuffled[n_c:]) - statistics.mean(shuffled[:n_c])
    if abs(diff) >= abs(observed):
        count += 1
print(f"  置换检验 p ≈ {count / 2000:.4f}（与 t 检验 {p:.4f} 应接近）")

# ---- 使用清单 ----
print("\n== 使用清单 ==")
for item in [
    "默认用 Welch t 检验，不假设方差相等",
    "同时报告 p 值与效应量（Cohen's d）",
    "样本 < 30 且分布偏态 → Bootstrap 更稳",
    "t 检验只比较均值；转化率用比例检验（第482课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 用 t_two_sided_p 计算 t=2.5、df=15 的 p 值。
# 2. 生成两组方差差异很大的数据，比较 Welch 与等方差 t 检验。
# 3. 实现配对 t 检验（同一批用户前后测）。
# 4. 思考：p 值很小但 Cohen's d 很小，产品该不该上线？
