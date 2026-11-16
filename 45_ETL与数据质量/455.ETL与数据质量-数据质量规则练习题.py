# ===== 第455课：ETL与数据质量-数据质量规则 =====
# 知识点：
#   - 数据质量规则：把“什么样的数据算合格”写成可执行代码
#   - 五类常用规则：非空、唯一、范围、格式、参照完整性
#   - 规则返回“错误信息或 None”，便于汇总每个字段的所有问题
#   - 一次校验收集全部问题，不要遇到第一个错就中断
#   - 规则要能配置、能单测、能复用到不同数据集
import re
from dataclasses import dataclass


@dataclass
class Issue:
    row: int
    field: str
    rule: str
    message: str


# ---------------- 规则工厂 ----------------
def required(field: str):
    def check(record: dict) -> str | None:
        value = record.get(field)
        if value is None or str(value).strip() == "":
            return f"{field} 不能为空"
        return None
    check.rule_name = f"required({field})"
    check.field = field
    return check


def unique(field: str):
    seen = set()

    def check(record: dict) -> str | None:
        value = record.get(field)
        key = str(value)
        if key in seen:
            return f"{field}={value!r} 重复"
        seen.add(key)
        return None
    check.rule_name = f"unique({field})"
    check.field = field
    check.reset = seen.clear          # 便于重复使用
    return check


def number_range(field: str, low: float, high: float):
    def check(record: dict) -> str | None:
        try:
            value = float(record.get(field))
        except (TypeError, ValueError):
            return f"{field} 不是数字：{record.get(field)!r}"
        if not (low <= value <= high):
            return f"{field}={value} 超出 [{low}, {high}]"
        return None
    check.rule_name = f"range({field},{low},{high})"
    check.field = field
    return check


def pattern(field: str, regex: str, hint: str = ""):
    compiled = re.compile(regex)

    def check(record: dict) -> str | None:
        value = str(record.get(field, ""))
        if not compiled.fullmatch(value):
            return f"{field}={value!r} 格式不符" + (f"（{hint}）" if hint else "")
        return None
    check.rule_name = f"pattern({field})"
    check.field = field
    return check


def in_set(field: str, allowed: set):
    def check(record: dict) -> str | None:
        value = record.get(field)
        if value not in allowed:
            return f"{field}={value!r} 不在允许值 {sorted(allowed)} 中"
        return None
    check.rule_name = f"in_set({field})"
    check.field = field
    return check


def matches_other(field: str, other: str):
    def check(record: dict) -> str | None:
        if record.get(field) != record.get(other):
            return f"{field} 与 {other} 不一致"
        return None
    check.rule_name = f"matches_other({field},{other})"
    check.field = field
    return check


# ---------------- 校验执行 ----------------
def validate(records: list[dict], rules: list) -> list[Issue]:
    issues = []
    for row_no, record in enumerate(records):
        for rule in rules:
            error = rule(record)
            if error:
                issues.append(Issue(row_no, rule.field, rule.rule_name, error))
    return issues


# ---------------- 演示 ----------------
CITIES = {"北京", "上海", "广州", "深圳"}
RULES = [
    required("order_id"),
    unique("order_id"),
    number_range("amount", 0.01, 100000),
    in_set("status", {"paid", "refunded", "pending"}),
    pattern("phone", r"1[3-9]\d{9}", "11 位手机号"),
    in_set("city", CITIES),
]

RECORDS = [
    {"order_id": "A001", "amount": 99.5, "status": "paid", "phone": "13812345678", "city": "北京"},
    {"order_id": "A002", "amount": -1, "status": "paid", "phone": "13812345678", "city": "上海"},
    {"order_id": "A002", "amount": 50, "status": "unknown", "phone": "123", "city": "火星"},
    {"order_id": "", "amount": "abc", "status": "pending", "phone": "", "city": "广州"},
    {"order_id": "A005", "amount": 200, "status": "paid", "phone": "15900001111", "city": "深圳"},
]

issues = validate(RECORDS, RULES)

print("== 校验结果 ==")
print(f"共 {len(RECORDS)} 行，发现 {len(issues)} 个问题\n")
for issue in issues:
    print(f"  行{issue.row} [{issue.rule}] {issue.message}")

# ---- 按行汇总：哪些行完全合格 ----
print("\n== 按行汇总 ==")
bad_rows = {issue.row for issue in issues}
for i, record in enumerate(RECORDS):
    status = "✗ 有问题" if i in bad_rows else "✓ 合格"
    print(f"  行{i} {record.get('order_id') or '<空>':6s} {status}")

# ---- 按规则统计：哪条规则命中最多 ----
print("\n== 规则命中统计 ==")
counts = {}
for issue in issues:
    counts[issue.rule] = counts.get(issue.rule, 0) + 1
for rule, count in sorted(counts.items(), key=lambda kv: -kv[1]):
    print(f"  {rule}: {count} 次")

# ---- 规则可复用：换一批数据前重置 unique ----
print("\n== 规则复用 ==")
for rule in RULES:
    if hasattr(rule, "reset"):
        rule.reset()
new_issues = validate(RECORDS[:2], RULES)
print("  新批次问题数：", len(new_issues), "（unique 状态已重置）")

# ---- 规则配置化（示意）----
print("\n== 规则可配置 ==")
CONFIG = [
    ("required", "order_id"),
    ("range", "amount", 0.01, 100000),
    ("in_set", "status", ["paid", "refunded", "pending"]),
]
print("  配置示例：", CONFIG)
print("  生产项目可把规则写成 JSON/YAML，由同一个执行器加载")

# ===== 练习题 =====
# 1. 增加“日期不早于 2020-01-01”的规则。
# 2. 增加“跨字段规则”：refunded 状态的金额必须为负（或单独字段）。
# 3. 把规则命中结果输出为 CSV 报告（第284课）。
# 4. 思考：规则太严会拒绝正常数据，太松会放坏数据进来，怎么平衡？
