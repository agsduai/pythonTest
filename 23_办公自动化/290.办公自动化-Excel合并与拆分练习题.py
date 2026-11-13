# ===== 第290课：办公自动化-Excel合并与拆分 =====
# 知识点：
#   - 合并：多个文件/多个 sheet → 一张总表
#   - 拆分：按某列的值分组 → 每组一个 sheet
#   - 这两个动作是“多部门报表回收/下发”的标准姿势
# 依赖：pip install openpyxl

import glob
import os

from openpyxl import Workbook, load_workbook

# ---- 1. 模拟三个部门各自报上来的表 ----
sample = {
    "技术部": [("小明", 15000)],
    "市场部": [("小红", 12000), ("小刚", 9000)],
    "人事部": [("小丽", 8000)],
}
for dept, rows in sample.items():
    wb = Workbook()
    ws = wb.active
    ws.title = dept
    ws.append(["姓名", "工资"])
    for r in rows:
        ws.append(r)
    wb.save(f"dept_{dept}.xlsx")
print("已生成 3 张部门分表")

# ---- 2. 合并：遍历文件 → 追加进总表 ----
merged = Workbook()
mws = merged.active
mws.title = "全员"
mws.append(["部门", "姓名", "工资"])
for path in glob.glob("dept_*.xlsx"):
    ws = load_workbook(path).active
    for row in ws.iter_rows(min_row=2, values_only=True):
        mws.append([ws.title, *row])
merged.save("all_290.xlsx")
print("合并后总表：", [c.value for c in mws[1]], "共", mws.max_row - 1, "人")

# ---- 3. 拆分：按部门列分组 → 各建一个 sheet ----
wb = load_workbook("all_290.xlsx")
groups = {}
for row in wb["全员"].iter_rows(min_row=2, values_only=True):
    groups.setdefault(row[0], []).append(row)

for dept, rows in groups.items():
    ws = wb.create_sheet(dept)
    ws.append(["部门", "姓名", "工资"])
    for r in rows:
        ws.append(list(r))
wb.save("all_290.xlsx")
print("拆分后 sheet：", wb.sheetnames)

for f in glob.glob("dept_*.xlsx") + ["all_290.xlsx"]:
    os.remove(f)

# ===== 练习题 =====
# 1. 合并时增加“来源文件名”列，方便追溯数据出自谁手。
# 2. 拆分时同时输出每个部门的独立 .xlsx 文件（而不是 sheet）。
# 3. 思考：部门表头不一致（列顺序不同）时，合并要先做什么？
