# ===== 第291课：办公自动化-综合案例-月度销售报表 =====
# 知识点：
#   - 综合运用：CSV 明细（284）→ Excel 汇总+图表（285/286）→ Word 报告（288）
#   - openpyxl.chart.BarChart：在 Excel 里生成原生柱状图
#   - 一条流水线：数据 → 分析 → 成品文档，全部脚本化
# 依赖：pip install openpyxl python-docx

import csv
import os
import random
from collections import defaultdict

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference

# ---- 1. 生成 11 月销售明细 CSV ----
random.seed(1)
products = ["键盘", "鼠标", "显示器", "耳机"]
with open("detail_291.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["日期", "商品", "金额"])
    for day in range(1, 31):
        for _ in range(random.randint(2, 5)):
            writer.writerow([f"2026-11-{day:02d}", random.choice(products), random.randint(50, 2000)])

# ---- 2. 流式统计 ----
total = defaultdict(int)
record_count = 0
with open("detail_291.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        total[row["商品"]] += int(row["金额"])
        record_count += 1
grand_total = sum(total.values())
print(f"明细 {record_count} 条，总销售额 {grand_total} 元")

# ---- 3. 写 Excel 汇总 + 柱状图 ----
wb = Workbook()
ws = wb.active
ws.title = "汇总"
ws.append(["商品", "销售额"])
for product, amount in sorted(total.items(), key=lambda kv: -kv[1]):
    ws.append([product, amount])

chart = BarChart()
chart.title = "11月商品销售额"
chart.y_axis.title = "金额（元）"
chart.x_axis.title = "商品"
data_ref = Reference(ws, min_col=2, min_row=1, max_row=ws.max_row)
cats_ref = Reference(ws, min_col=1, min_row=2, max_row=ws.max_row)
chart.add_data(data_ref, titles_from_data=True)
chart.set_categories(cats_ref)
chart.width, chart.height = 14, 8
ws.add_chart(chart, "D2")
wb.save("sales_report_291.xlsx")
print("已生成 sales_report_291.xlsx（含原生柱状图）")

# ---- 4. Word 月报 ----
from docx import Document

doc = Document()
doc.add_heading("11 月销售月报", level=0)
doc.add_paragraph(f"本月共 {record_count} 笔订单，总销售额 {grand_total} 元。")
doc.add_heading("商品排名", level=1)
table = doc.add_table(rows=1, cols=3)
table.style = "Table Grid"
head = table.rows[0].cells
head[0].text, head[1].text, head[2].text = "排名", "商品", "销售额"
for i, (product, amount) in enumerate(sorted(total.items(), key=lambda kv: -kv[1]), 1):
    row = table.add_row().cells
    row[0].text = str(i)
    row[1].text = product
    row[2].text = f"{amount} 元"
doc.save("sales_report_291.docx")
print("已生成 sales_report_291.docx")

for f in ("detail_291.csv", "sales_report_291.xlsx", "sales_report_291.docx"):
    os.remove(f)

# ===== 练习题 =====
# 1. 给月报增加“日销售额趋势”：按日期分组统计，生成折线图（LineChart）。
# 2. 把整条流水线封装成 make_monthly_report(month) 一键运行。
# 3. 思考：如果明细数据来自数据库而非 CSV，流水线哪几步要换、哪几步不动？
