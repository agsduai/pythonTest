# ===== 第286课：办公自动化-Excel样式与公式 =====
# 知识点：
#   - Font 加粗/颜色、PatternFill 填充、Alignment 对齐、Border 边框
#   - column_dimensions["A"].width 设置列宽
#   - 公式直接写 "=B2+C2"：由 Excel 打开时计算
#   - 注意：openpyxl 读回公式时拿到的是公式文本，不是计算结果
# 依赖：pip install openpyxl

import os

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active
ws.title = "成绩单"

data = [
    ["姓名", "语文", "数学", "总分"],
    ["小明", 92, 88],
    ["小红", 85, 95],
]
for row in data:
    ws.append(row)

# ---- 样式：表头蓝底白字居中 ----
header_fill = PatternFill("solid", fgColor="4472C4")
for cell in ws[1]:
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal="center")

# ---- 公式：总分 = 语文 + 数学 ----
for r in range(2, ws.max_row + 1):
    ws.cell(row=r, column=4, value=f"=B{r}+C{r}")

# ---- 列宽与全表边框 ----
ws.column_dimensions["A"].width = 12
for col in "BCD":
    ws.column_dimensions[col].width = 10
thin = Side(style="thin", color="CCCCCC")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=4):
    for cell in row:
        cell.border = border

wb.save("styled_286.xlsx")
print("已生成 styled_286.xlsx —— 用 Excel/WPS 打开即可看到样式，总分列是活公式")

# 读回验证：公式单元格拿到的就是公式文本
check = ws.cell(row=2, column=4).value
print("D2 内容：", check)
print("get_column_letter(4) =", get_column_letter(4), "（数字列号转字母）")

os.remove("styled_286.xlsx")

# ===== 练习题 =====
# 1. 给"总分"最高的行加绿色填充（提示：先在 Python 里算好哪行最高）。
# 2. 用 AVERAGE 公式给表尾追加"平均分"行。
# 3. 思考：想让 Python 直接拿到公式的计算结果，有哪两条路？
#    （提示：load_workbook(data_only=True) / 自己算）
