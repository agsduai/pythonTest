# ===== 第287课：办公自动化-批量生成个人表格 =====
# 知识点：
#   - “一张总表 → N 张个人小表”的批量套路
#   - 迭代数据行 → 新建工作簿 → 写表头和数据 → 按人名保存
#   - 场景：工资条、成绩单、通知单批量生成
# 依赖：pip install openpyxl

import glob
import os

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

# ---- 1. 模拟工资总表 ----
wb = Workbook()
ws = wb.active
ws.append(["姓名", "部门", "基本工资", "奖金"])
for row in [
    ("小明", "技术", 15000, 3000),
    ("小红", "市场", 12000, 5000),
    ("小刚", "技术", 14000, 2000),
]:
    ws.append(row)
wb.save("payroll_287.xlsx")
print("总表已生成")

# ---- 2. 逐人拆分成独立文件 ----
src = load_workbook("payroll_287.xlsx").active
headers = [cell.value for cell in src[1]]

for row in src.iter_rows(min_row=2, values_only=True):
    out = Workbook()
    sheet = out.active
    sheet.append(headers)
    sheet.append(row)
    # 小美化：数据行加粗
    for cell in sheet[2]:
        cell.font = Font(bold=True)
    out.save(f"工资条_{row[0]}.xlsx")
    print(f"已生成 工资条_{row[0]}.xlsx：{row}")

print(f"共生成 {len(glob.glob('工资条_*.xlsx'))} 份工资条")

# ---- 3. 清理演示文件 ----
for f in glob.glob("工资条_*.xlsx") + ["payroll_287.xlsx"]:
    os.remove(f)

# ===== 练习题 =====
# 1. 在工资条里加一行“实发 = 基本 + 奖金”的 Excel 公式。
# 2. 改成生成“成绩单”：从第23章任意成绩数据出发，每个学生一张表。
# 3. 思考：如果要发 1000 人的工资条，逐个保存文件合理吗？
#    （引子：下一章的邮件自动化或压缩包更合适）
