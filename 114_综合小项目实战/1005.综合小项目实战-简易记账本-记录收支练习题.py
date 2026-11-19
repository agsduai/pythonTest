# ===== 第1005课：综合小项目实战-简易记账本——记录收支 =====
# 知识点：
#   - 列表存多条记录：每条记录是一个字典 {类型, 金额, 说明}
#   - 金额必须为正数，收入和支出分开记
#   - 数据持久化：JSON 文件保存所有记录
#   - 日期自动记录：datetime.now() 记住每笔发生时间
# 依赖：无（标准库）
import json
import os
from datetime import datetime

LEDGER_FILE = "ledger.json"


def load_ledger():
    if not os.path.exists(LEDGER_FILE):
        return []
    with open(LEDGER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_ledger(records):
    with open(LEDGER_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def add_record(records, record_type, amount, description):
    """添加一条记录。record_type: "收入" 或 "支出"。"""
    if record_type not in ("收入", "支出"):
        return False, "类型必须是「收入」或「支出」"
    if not isinstance(amount, (int, float)) or amount <= 0:
        return False, "金额必须为正数"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    records.append({
        "type": record_type,
        "amount": amount,
        "description": description,
        "time": now,
    })
    save_ledger(records)
    return True, f"已记录{record_type} {amount} 元：{description}"


def show_records(records):
    """打印所有记录。"""
    if not records:
        print("  暂无记录")
        return
    print(f"  {'序号':<4}{'类型':<6}{'金额':>10}{'说明':<20}{'时间'}")
    print(f"  {'-' * 55}")
    for i, r in enumerate(records, 1):
        print(f"  {i:<4}{r['type']:<6}{r['amount']:>10.2f}"
              f"{r['description']:<20}{r['time']}")


def get_balance(records):
    """计算当前余额：所有收入 - 所有支出。"""
    income = sum(r["amount"] for r in records if r["type"] == "收入")
    expense = sum(r["amount"] for r in records if r["type"] == "支出")
    return income - expense


# 使用示例
records = load_ledger()
print("== 简易记账本 ==")

ok, msg = add_record(records, "收入", 5000, "工资")
print(f"  {msg}")
ok, msg = add_record(records, "支出", 150, "买菜")
print(f"  {msg}")
ok, msg = add_record(records, "支出", 800, "房租")
print(f"  {msg}")
ok, msg = add_record(records, "收入", 200, "兼职")
print(f"  {msg}")

print(f"\n== 全部记录 ==")
show_records(records)
balance = get_balance(records)
print(f"\n  当前余额: {balance:.2f} 元")

# ===== 练习题 =====
# 1. 实现 filter_by_type(records, type)：只显示「收入」或「支出」的记录。
# 2. 实现 get_month_total(records, month)：统计某月份的总支出。
# 3. 增加分类字段（餐饮/交通/购物等），按分类统计支出。
# 4. 思考：为什么要把「收入」和「支出」分开记录而不是用一个正负号？
