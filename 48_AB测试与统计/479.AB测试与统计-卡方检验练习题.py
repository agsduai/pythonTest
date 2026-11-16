# ===== 第479课：AB测试与统计-卡方检验 =====
# 知识点：
#   - 卡方检验：判断两个分类变量是否相关（如“分组”与“是否转化”）
#   - 2×2 列联表：行=组别，列=转化/未转化
#   - 期望频数 = 行合计 × 列合计 / 总数；卡方 = Σ (观察-期望)² / 期望
#   - 自由度 = (行数-1) × (列数-1)；查临界值判断是否显著
#   - 效应量 Cramér's V：卡方 / (n × min(行-1, 列-1)) 的平方根
#   - 与比例 z 检验（第482课）在 2×2 场景等价；卡方适合多组/多类别
# 依赖：无（标准库）


def chi_square_2x2(control_conv, control_total, treat_conv, treat_total):
    """返回 (chi2, df, cramers_v, expected)。"""
    control_fail = control_total - control_conv
    treat_fail = treat_total - treat_conv
    table = [[control_conv, control_fail], [treat_conv, treat_fail]]
    row_totals = [sum(row) for row in table]
    col_totals = [sum(table[r][c] for r in range(2)) for c in range(2)]
    n = sum(row_totals)

    chi2 = 0.0
    expected = []
    for r in range(2):
        expected_row = []
        for c in range(2):
            e = row_totals[r] * col_totals[c] / n
            expected_row.append(e)
            chi2 += (table[r][c] - e) ** 2 / e
        expected.append(expected_row)

    df = 1
    cramers_v = (chi2 / (n * min(1, 1))) ** 0.5
    return chi2, df, cramers_v, expected, table, n


print("== 2×2 列联表：转化 vs 未转化 ==")
control_conv, control_total = 500, 5000
treat_conv, treat_total = 600, 5000
chi2, df, v, expected, table, n = chi_square_2x2(
    control_conv, control_total, treat_conv, treat_total)

print(f"  观察值：对照组 {table[0]}，实验组 {table[1]}")
print(f"  期望值：对照组 {[round(e, 1) for e in expected[0]]}，"
      f"实验组 {[round(e, 1) for e in expected[1]]}")
print(f"  转化率：对照 {control_conv / control_total:.1%} | "
      f"实验 {treat_conv / treat_total:.1%}")
print(f"  chi² = {chi2:.2f}，df = {df}，Cramér's V = {v:.3f}")

# 临界值表（α=0.05）
CRITICAL = {1: 3.841, 2: 5.991, 3: 7.815, 4: 9.488}
critical = CRITICAL[df]
print(f"  临界值（df={df}, α=0.05）：{critical}")
print(f"  结论：{'显著（拒绝独立假设）' if chi2 > critical else '不显著'}")

# ---- 场景 2：差异不明显 ----
print("\n== 场景 2：差异很小 ==")
chi2b, dfb, vb, _, tableb, nb = chi_square_2x2(500, 5000, 515, 5000)
print(f"  转化率：10.0% vs {515 / 5000:.1%}")
print(f"  chi² = {chi2b:.2f}，Cramér's V = {vb:.3f}")
print(f"  结论：{'显著' if chi2b > CRITICAL[1] else '不显著'}")

# ---- 多组卡方（3 组 2 类别）----
print("\n== 3 组 × 2 类别（df=2）==")
groups = [("A", 100, 1000), ("B", 120, 1000), ("C", 145, 1000)]
total_conv = sum(g[1] for g in groups)
total_n = sum(g[2] for g in groups)
overall_rate = total_conv / total_n

chi2_multi = 0.0
print(f"  总体转化率：{overall_rate:.1%}")
for name, conv, total in groups:
    fail = total - conv
    e_conv = total * overall_rate
    e_fail = total * (1 - overall_rate)
    chi2_multi += (conv - e_conv) ** 2 / e_conv + (fail - e_fail) ** 2 / e_fail
    print(f"  {name}: {conv}/{total} = {conv / total:.1%}")
df_multi = (3 - 1) * (2 - 1)
print(f"  chi² = {chi2_multi:.2f}，df = {df_multi}，临界值 {CRITICAL[df_multi]}")
print(f"  结论：{'组间存在显著差异' if chi2_multi > CRITICAL[df_multi] else '无显著差异'}")

# ---- 注意事项 ----
print("\n== 注意事项 ==")
for item in [
    "期望频数 < 5 的格子较多时，卡方近似不可靠（用 Fisher 精确检验）",
    "卡方显著只说明“有关联”，不说明“谁更好/差多少”",
    "2×2 转化率场景用两比例 z 检验更方便（有方向性）",
    "多组显著后，还需要两两比较 + 多重比较校正（第481课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 2×2 卡方增加 p 值近似（提示：df=1 时 p = erfc(sqrt(chi2/2))）。
# 2. 用 3×2 例子计算 Cramér's V。
# 3. 模拟期望频数 < 5 的数据，观察卡方结论不可靠。
# 4. 思考：卡方与“比例 z 检验”在 2×2 时为什么等价？
