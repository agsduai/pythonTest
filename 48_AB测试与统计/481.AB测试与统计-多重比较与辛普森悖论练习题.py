# ===== 第481课：AB测试与统计-多重比较与辛普森悖论 =====
# 知识点：
#   - 多重比较：同时检验很多指标/分组，假阳性会累积
#   - 族错误率：做 m 次独立检验，至少一次假阳性的概率 ≈ 1-(1-α)^m
#   - Bonferroni 校正：每次检验用 α/m，简单保守
#   - FDR（错误发现率）：控制“判为显著的里面有多少是假的”，更宽松
#   - 辛普森悖论：分组看 A 更好，合起来看 B 更好 —— 因为分组构成不同
#   - 防御：先定指标与分组、看整体也看分层、报告样本构成
# 依赖：无

from statistics import NormalDist

NORMAL = NormalDist()

# ---------------- 1. 多重比较 ----------------
print("== 多重比较的假阳性 ==")
alpha = 0.05
for m in (1, 5, 10, 20, 50):
    family_error = 1 - (1 - alpha) ** m
    print(f"  检验 {m:2d} 个指标：至少一次假阳性的概率 ≈ {family_error:.1%}")

# ---- 模拟：H0 全为真，仍会“显著” ----
import random
random.seed(3)
false_positive_rounds = 0
for _ in range(2000):
    p_values = [random.random() for _ in range(20)]
    if any(p < 0.05 for p in p_values):
        false_positive_rounds += 1
print(f"\n  模拟 2000 轮，每轮 20 个真 H0：至少一个 p<0.05 的比例 "
      f"{false_positive_rounds / 2000:.1%}（理论 {1 - 0.95 ** 20:.1%}）")

# ---------------- 2. Bonferroni 校正 ----------------
print("\n== Bonferroni 校正 ==")
p_values = {
    "转化率": 0.008,
    "客单价": 0.021,
    "留存率": 0.049,
    "分享率": 0.12,
    "退款率": 0.35,
}
m = len(p_values)
threshold = alpha / m
print(f"  m={m}，校正阈值 α/m = {threshold:.4f}")
for name, p in p_values.items():
    raw = "显著" if p < alpha else "不显著"
    corrected = "显著" if p < threshold else "不显著"
    print(f"  {name:5s} p={p:.3f} | 未校正：{raw:3s} | Bonferroni：{corrected}")

# ---------------- 3. 辛普森悖论 ----------------
print("\n== 辛普森悖论 ==")
# 两种治疗方案，按结石大小分层
# 方案 A：小结石 81/87=93.1%，大结石 192/263=73.0%，合计 273/350=78.0%
# 方案 B：小结石 234/270=86.7%，大结石 55/80=68.8%，合计 289/350=82.6%
data = {
    "方案A": {"小结石": (81, 87), "大结石": (192, 263)},
    "方案B": {"小结石": (234, 270), "大结石": (55, 80)},
}

print(f"  {'方案':<5}{'分层':<8}{'成功/总数':<12}{'成功率'}")
for name, segments in data.items():
    total_success = total_n = 0
    for seg, (success, n) in segments.items():
        print(f"  {name:<5}{seg:<8}{success}/{n:<9}{success / n:.1%}")
        total_success += success
        total_n += n
    print(f"  {name:<5}{'合计':<8}{total_success}/{total_n:<9}"
          f"{total_success / total_n:.1%}")
    print()

print("  结论：每个分层里 A 的成功率都更高，但合计 B 更高。")
print("  原因：A 的病例多为大结石（难治），B 的病例多为小结石（好治）。")

# ---- 为什么会这样：构成不同 ----
print("\n== 分组构成 ==")
for name, segments in data.items():
    total = sum(n for _, n in segments.values())
    share_small = segments["小结石"][1] / total
    print(f"  {name}：小结石占比 {share_small:.1%}，大结石占比 {1 - share_small:.1%}")

# ---- 防御清单 ----
print("\n== 如何避免 ==")
for item in [
    "实验设计阶段就固定分组与指标，不要事后挑分组",
    "同时报告整体与分层结果，并给出分层样本量",
    "分层差异大时，用加权/分层分析而不是简单汇总",
    "多重比较必须校正（Bonferroni 或 FDR）",
    "看到“整体显著但每个分层都不显著”要警惕辛普森悖论",
]:
    print("  -", item)

# ---- 近似 p 值计算（正态）----
print("\n== 附：两比例 z 检验的 p 值 ==")
def two_proportion_p(c1, n1, c2, n2):
    p1, p2 = c1 / n1, c2 / n2
    pooled = (c1 + c2) / (n1 + n2)
    se = (pooled * (1 - pooled) * (1 / n1 + 1 / n2)) ** 0.5
    if se == 0:
        return 0.0
    z = (p2 - p1) / se
    return 2 * (1 - NORMAL.cdf(abs(z))), z

p, z = two_proportion_p(500, 5000, 600, 5000)
print(f"  10% vs 12%：z={z:.2f}，p={p:.4f}")

# ===== 练习题 =====
# 1. 用 Bonferroni 校正第482课的多指标结果。
# 2. 构造一个辛普森悖论的数值例子（自己设计四组数据）。
# 3. 计算“检验 100 个指标、α=0.05”的族错误率。
# 4. 思考：Bonferroni 太保守会漏掉真实效果，什么场景该改用 FDR？
