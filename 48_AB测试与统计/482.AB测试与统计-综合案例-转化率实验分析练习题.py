# ===== 第482课：AB测试与统计-综合案例-转化率实验分析 =====
# 知识点：
#   - 综合运用：样本量（480）+ 两比例检验 + 置信区间（476）+ 分层 + 多重比较（481）
#   - 完整分析流程：实验设计 → 数据检查 → 整体检验 → 分层检验 → 结论
#   - 两比例 z 检验：合并方差算标准误，正态近似求 p 值
#   - 决策不能只看 p：效应量、CI、业务成本、分层一致性
#   - 输出一份可交付的实验报告（JSON + Markdown）
import json
import random
import tempfile
from pathlib import Path
from statistics import NormalDist

NORMAL = NormalDist()


# ---------------- 1. 实验设计 ----------------
BASELINE = 0.10
TREATMENT_RATE = 0.12
ALPHA = 0.05
POWER = 0.8


def required_sample_size(p1, p2, alpha=ALPHA, power=POWER):
    z_a = NORMAL.inv_cdf(1 - alpha / 2)
    z_p = NORMAL.inv_cdf(power)
    p_bar = (p1 + p2) / 2
    num = (z_a * (2 * p_bar * (1 - p_bar)) ** 0.5
           + z_p * (p1 * (1 - p1) + p2 * (1 - p2)) ** 0.5) ** 2
    return int(num / (p2 - p1) ** 2) + 1


n_needed = required_sample_size(BASELINE, TREATMENT_RATE)
N_PER_GROUP = max(n_needed, 5000)
print("== 实验设计 ==")
print(f"  基线 {BASELINE:.0%} → 目标 {TREATMENT_RATE:.0%}，α={ALPHA}，power={POWER}")
print(f"  每组所需 {n_needed:,} 人，实际计划 {N_PER_GROUP:,} 人/组")


# ---------------- 2. 模拟实验数据 ----------------
def simulate(n, rate, seed):
    rng = random.Random(seed)
    return sum(1 for _ in range(n) if rng.random() < rate)


random.seed(7)
control_conv = simulate(N_PER_GROUP, BASELINE, seed=1)
treat_conv = simulate(N_PER_GROUP, TREATMENT_RATE, seed=2)

# 分层数据（移动端 / 桌面端），用于检查一致性
segments = {
    "移动端": {"control_n": 3200, "control_conv": int(3200 * 0.09),
               "treat_n": 3200, "treat_conv": int(3200 * 0.105)},
    "桌面端": {"control_n": 1800, "control_conv": int(1800 * 0.118),
               "treat_n": 1800, "treat_conv": int(1800 * 0.145)},
}

print("\n== 原始数据 ==")
print(f"  对照组：{control_conv}/{N_PER_GROUP} = {control_conv / N_PER_GROUP:.2%}")
print(f"  实验组：{treat_conv}/{N_PER_GROUP} = {treat_conv / N_PER_GROUP:.2%}")


# ---------------- 3. 两比例 z 检验 ----------------
def two_proportion_test(c1, n1, c2, n2, alpha=0.05):
    p1, p2 = c1 / n1, c2 / n2
    diff = p2 - p1
    pooled = (c1 + c2) / (n1 + n2)
    se_pooled = (pooled * (1 - pooled) * (1 / n1 + 1 / n2)) ** 0.5
    z = diff / se_pooled if se_pooled else 0.0
    p_value = 2 * (1 - NORMAL.cdf(abs(z)))
    se_unpooled = (p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2) ** 0.5
    z_crit = NORMAL.inv_cdf(1 - alpha / 2)
    ci = (diff - z_crit * se_unpooled, diff + z_crit * se_unpooled)
    return {
        "p1": p1, "p2": p2, "diff": diff,
        "relative_lift": diff / p1 if p1 else 0,
        "z": z, "p_value": p_value,
        "ci95": ci, "significant": p_value < alpha,
    }


result = two_proportion_test(control_conv, N_PER_GROUP, treat_conv, N_PER_GROUP)
print("\n== 整体检验 ==")
print(f"  转化率：{result['p1']:.2%} → {result['p2']:.2%}，"
      f"绝对提升 {result['diff'] * 100:+.2f}pp，相对提升 {result['relative_lift']:+.1%}")
print(f"  z = {result['z']:.2f}，p = {result['p_value']:.4f}")
print(f"  95% CI：[{result['ci95'][0] * 100:+.2f}pp, {result['ci95'][1] * 100:+.2f}pp]")
print(f"  结论：{'显著' if result['significant'] else '不显著'}")

# ---------------- 4. 分层一致性检查 ----------------
print("\n== 分层分析 ==")
segment_results = {}
for name, seg in segments.items():
    r = two_proportion_test(seg["control_conv"], seg["control_n"],
                            seg["treat_conv"], seg["treat_n"])
    segment_results[name] = r
    print(f"  {name}：{r['p1']:.2%} → {r['p2']:.2%}，"
          f"提升 {r['diff'] * 100:+.2f}pp，p={r['p_value']:.4f}")

# 检查方向是否一致（辛普森悖论防御）
directions = [r["diff"] > 0 for r in segment_results.values()]
print(f"  各分层方向一致（都为正）：{all(directions)}")

# ---------------- 5. 多重比较 ----------------
print("\n== 多重比较校正 ==")
metrics = {
    "转化率": result["p_value"],
    "移动端转化": segment_results["移动端"]["p_value"],
    "桌面端转化": segment_results["桌面端"]["p_value"],
    "客单价(假设)": 0.03,
    "留存率(假设)": 0.12,
}
m = len(metrics)
bonferroni = ALPHA / m
print(f"  m={m}，Bonferroni 阈值 {bonferroni:.4f}")
for name, p in metrics.items():
    print(f"  {name:10s} p={p:.4f} → "
          f"{'显著' if p < bonferroni else '不显著'}（校正后）")

# ---------------- 6. 决策与报告 ----------------
decision = ("上线" if result["significant"] and result["diff"] > 0
            and all(directions) else "继续观察")
print("\n== 决策 ==")
print("  建议：", decision)
print("  理由：整体显著、方向为正、分层一致；但需关注桌面端效应更小")

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    report = {
        "design": {"baseline": BASELINE, "target": TREATMENT_RATE,
                   "alpha": ALPHA, "power": POWER,
                   "n_per_group": N_PER_GROUP, "n_needed": n_needed},
        "overall": {k: (round(v, 6) if isinstance(v, float) else v)
                    for k, v in result.items()},
        "segments": {name: {k: (round(v, 6) if isinstance(v, float) else v)
                            for k, v in r.items()}
                     for name, r in segment_results.items()},
        "multiple_comparison": {"m": m, "threshold": bonferroni},
        "decision": decision,
    }
    json_path = tmp / "experiment_report.json"
    md_path = tmp / "experiment_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# A/B 实验报告",
        "",
        f"- 实验设计：{BASELINE:.0%} → {TREATMENT_RATE:.0%}，每组 {N_PER_GROUP:,} 人",
        f"- 整体：{result['p1']:.2%} → {result['p2']:.2%}，"
        f"提升 {result['diff'] * 100:+.2f}pp（p={result['p_value']:.4f}）",
        f"- 95% CI：{result['ci95'][0] * 100:+.2f}pp ~ {result['ci95'][1] * 100:+.2f}pp",
        f"- 分层：移动端 {segment_results['移动端']['diff'] * 100:+.2f}pp，"
        f"桌面端 {segment_results['桌面端']['diff'] * 100:+.2f}pp",
        f"- 决策：{decision}",
    ]
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    print("\n== 报告文件 ==")
    print(md_path.read_text(encoding="utf-8"))
    print("JSON 大小：", json_path.stat().st_size, "字节")

# ---------------- 分析清单 ----------------
print("== 分析清单 ==")
for item in [
    "1. 实验前：定指标、算样本量、随机分流",
    "2. 实验中：不要偷看/提前停止",
    "3. 实验后：先做数据质量检查（分流是否均匀、埋点是否丢失）",
    "4. 整体检验 → 置信区间 → 效应量",
    "5. 分层检查一致性 + 多重比较校正",
    "6. 结合业务成本做决策，并记录结论与后续动作",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把实验组转化率改成 11%，观察 p 值与决策变化。
# 2. 给报告增加“每用户平均收益”指标，并做 Bonferroni 校正。
# 3. 模拟“偷看数据”：每 500 人检验一次，统计假阳性率。
# 4. 思考：如果移动端提升显著、桌面端不显著，产品该怎么 rollout？
