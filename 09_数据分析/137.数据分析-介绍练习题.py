# ===== 第137课：数据分析-介绍 =====
# 课程来源：B站 BV1sHU9BmEne
# 依赖：pip install pandas（本章后续课程使用；本课示例仅用标准库）
# 知识点：
#   - 数据分析：从数据中提取有价值信息、支撑决策的过程
#   - 基本流程：明确问题 -> 获取数据 -> 数据清洗 -> 分析建模 -> 可视化 -> 得出结论
#   - 常用工具：Excel、SQL、Python（pandas、NumPy、Matplotlib）
#   - Python 的优势：生态丰富、可自动化、便于和 AI 结合

# 示例：用标准库完成一次迷你销售数据分析
records = [
    {"month": "1月", "sales": 120},
    {"month": "2月", "sales": 95},
    {"month": "3月", "sales": 143},
    {"month": "4月", "sales": 88},
]

total = sum(item["sales"] for item in records)          # 总销售额
average = total / len(records)                          # 月均销售额
best = max(records, key=lambda item: item["sales"])     # 销售额最高的月份
worst = min(records, key=lambda item: item["sales"])    # 销售额最低的月份

print(f"总销售额：{total}")
print(f"月均销售额：{average:.2f}")
print(f"最高月份：{best['month']}（{best['sales']}）")
print(f"最低月份：{worst['month']}（{worst['sales']}）")

# 数据分析的常见产出：统计表、趋势图、对比图、结论报告
# 后续课程将用 pandas 把这些计算写得更简洁，用 Matplotlib 把结果画成图。

# ===== 练习题 =====
# 1. 用自己的话写出数据分析的 5 个基本步骤，并说明每一步的产出。
# 2. 修改示例数据，增加 5 月和 6 月的销售额，重新计算总额与月均值。
# 3. 统计示例中销售额超过 100 的月份，并打印这些月份及其销售额。
