# ===== 第285课：办公自动化-Excel读写入门 =====
# 知识点：
#   - openpyxl：读写 .xlsx 的第三方库
#   - Workbook 新建 / load_workbook 读取；wb.active 是默认工作表
#   - append 按行写；["B2"] 或 cell(row, column) 定位单元格
#   - iter_rows(values_only=True) 批量读成元组
# 依赖：pip install openpyxl

import os

from openpyxl import Workbook, load_workbook

# ---- 写：新建工作簿 ----
wb = Workbook()
ws = wb.active
ws.title = "成绩表"
ws.append(["姓名", "语文", "数学"])      # 第一行：表头
ws.append(["小明", 92, 88])
ws.append(["小红", 85, 95])
wb.save("students_285.xlsx")
print("已保存 students_285.xlsx")

# ---- 读：打开已有工作簿 ----
wb2 = load_workbook("students_285.xlsx")
print("所有工作表：", wb2.sheetnames)

ws2 = wb2["成绩表"]
print(f"共 {ws2.max_row} 行 {ws2.max_column} 列")

for row in ws2.iter_rows(values_only=True):
    print(" ", row)

print("B2 单元格：", ws2["B2"].value)
print("按行列取：", ws2.cell(row=2, column=1).value)

# ---- 多工作表 ----
ws3 = wb2.create_sheet("说明")
ws3["A1"] = "本表由脚本自动生成"
wb2.save("students_285.xlsx")
print("追加 sheet 后：", load_workbook("students_285.xlsx").sheetnames)

os.remove("students_285.xlsx")

# ===== 练习题 =====
# 1. 把第284课的 sales_284.csv 数据写进 Excel，再读回验证。
# 2. 编写函数 sheet_to_dict(path)：把工作表读成 [{列名: 值}, ...] 列表。
# 3. 思考：openpyxl 与 pandas.read_excel 各适合什么场景？
