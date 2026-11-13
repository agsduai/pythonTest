# ===== 第284课：办公自动化-CSV报表进阶 =====
# 知识点：
#   - csv.DictReader / DictWriter：按列名读写，比下标可读
#   - 编码用 utf-8-sig：Excel 双击打开中文不乱码
#   - newline=""：csv 模块的固定要求，防止空行
#   - 读 → 统计 → 写回：报表自动化的最小闭环（复习第191课流式思路）

import csv
import os
from collections import Counter

# ---- 1. 准备一份“销售明细” ----
rows = [
    {"日期": "2026-11-01", "商品": "键盘", "数量": "2", "金额": "398"},
    {"日期": "2026-11-01", "商品": "鼠标", "数量": "1", "金额": "99"},
    {"日期": "2026-11-02", "商品": "键盘", "数量": "3", "金额": "597"},
    {"日期": "2026-11-02", "商品": "显示器", "数量": "1", "金额": "1299"},
]
with open("sales_284.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["日期", "商品", "数量", "金额"])
    writer.writeheader()
    writer.writerows(rows)

# ---- 2. 逐行统计 ----
total_by_product = Counter()
record_count = 0
with open("sales_284.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        total_by_product[row["商品"]] += int(row["金额"])
        record_count += 1

print(f"共 {record_count} 条记录")

# ---- 3. 汇总写回新表 ----
with open("summary_284.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["商品", "销售额"])
    for product, total in total_by_product.most_common():
        writer.writerow([product, total])

print("--- 汇总表内容 ---")
print(open("summary_284.csv", encoding="utf-8-sig").read())

os.remove("sales_284.csv")
os.remove("summary_284.csv")

# ===== 练习题 =====
# 1. 在明细里增加“负责人”列，统计每人的销售总额。
# 2. 编写函数 merge_csv(file_list, out)：把多个同结构 CSV 合并成一个。
# 3. 让统计只包含“2026-11-02”之后的数据（提示：日期字符串可直接比较）。
# 4. 思考：utf-8 与 utf-8-sig 的差别是什么？谁读谁会有问题？
