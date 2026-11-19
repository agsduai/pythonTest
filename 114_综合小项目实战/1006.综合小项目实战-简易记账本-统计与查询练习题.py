# ===== 第1006课：综合小项目实战-简易记账本——统计与查询 =====
# 知识点：
#   - 按类型分组统计：遍历记录，按条件累加
#   - 日期过滤：字符串 startswith 匹配年月
#   - 排序：sorted(key=lambda) 按金额排序
#   - top N：排序后取前 N 条
# 依赖：无（标准库）
import json
import os
from collections import defaultdict

LEDGER_FILE = "ledger.json"


def load_ledger():
    if not os.path.exists(LEDGER_FILE):
        return []
    with open(LEDGER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_records():
    if not os.path.exists(LEDGER_FILE):
        return []
    with open(LEDGER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def summarize_by_type(records):
    """按类型汇总金额。"""
    summary = defaultdict(float)
    for r in records:
        summary[r["type"]] += r["amount"]
    return dict(summary)


def filter_by_month(records, month_prefix):
    """按月份过滤：month_prefix 格式如 '2024-01'。"""
    return [r for r in records if r["time"].startswith(month_prefix)]


def top_expenses(records, n=3):
    """支出金额最大的前 n 笔。"""
    expenses = [r for r in records if r["type"] == "支出"]
    return sorted(expenses, key=lambda r: r["amount"], reverse=True)[:n]


def category_summary(records):
    """按说明关键词分类统计支出。"""
    categories = defaultdict(float)
    for r in records:
        if r["type"] == "支出":
            for keyword in ("买菜", "房租", "餐饮", "交通", "购物"):
                if keyword in r.get("description", ""):
                    categories[keyword] += r["amount"]
                    break
            else:
                categories["其他"] += r["amount"]
    return dict(categories)


# 使用示例
records = load_ledger()
if not records:
    records = [
        {"type": "收入", "amount": 5000, "description": "工资",
         "time": "2024-01-05 09:00"},
        {"type": "支出", "amount": 150, "description": "买菜",
         "time": "2024-01-06 18:00"},
        {"type": "支出", "amount": 800, "description": "房租",
         "time": "2024-01-06 19:00"},
        {"type": "支出", "amount": 200, "description": "餐饮",
         "time": "2024-01-10 12:00"},
        {"type": "收入", "amount": 200, "description": "兼职",
         "time": "2024-01-15 14:00"},
    ]

print("== 记账本统计 ==")

print("\n== 按类型汇总 ==")
summary = summarize_by_type(records)
for t, amount in summary.items():
    print(f"  {t}: {amount:.2f} 元")
balance = summary.get("收入", 0) - summary.get("支出", 0)
print(f"  余额: {balance:.2f} 元")

print("\n== 1 月支出明细 ==")
jan_records = filter_by_month(records, "2024-01")
for r in jan_records:
    if r["type"] == "支出":
        print(f"  {r['time']}: {r['description']} {r['amount']:.2f} 元")

print("\n== 支出 Top 3 ==")
top = top_expenses(records, 3)
for i, r in enumerate(top, 1):
    print(f"  {i}. {r['description']} {r['amount']:.2f} 元 ({r['time']})")

print("\n== 支出分类统计 ==")
cat_summary = category_summary(records)
for cat, amount in sorted(cat_summary.items(), key=lambda x: -x[1]):
    bar = "#" * int(amount / max(cat_summary.values()) * 20)
    print(f"  {cat:<6}{amount:>8.2f}  {bar}")

# ===== 练习题 =====
# 1. 实现「按周统计」：把记录按 ISO 周分组，统计每周支出。
# 2. 实现「预算检查」：设定月预算 2000 元，超出时打印警告。
# 3. 实现「导出 CSV」：把记录保存为 CSV 文件。
# 4. 思考：如果记录有 10 万条，哪些操作会变慢？如何优化？
