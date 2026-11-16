# ===== 第453课：ETL与数据质量-转换清洗与派生字段 =====
# 知识点：
#   - 转换层职责：类型转换、去空白、统一大小写、映射编码、派生字段
#   - 原始数据常见问题：字符串数字、日期格式混乱、状态值不统一、空值
#   - 派生字段：year_month、amount_tier、is_large_order —— 让下游好查
#   - 失败要“带原因拒绝”，不能静默丢；拒绝记录交给隔离区（第456课）
#   - 转换函数应可单测、无副作用、不碰数据库
from datetime import datetime


STATUS_MAP = {
    "paid": "已支付", "PAID": "已支付", "1": "已支付",
    "refunded": "已退款", "REFUNDED": "已退款", "2": "已退款",
    "pending": "待支付", "PENDING": "待支付", "0": "待支付",
}


def parse_amount(value) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        amount = float(value)
    else:
        text = str(value).strip().replace(",", "").replace("￥", "")
        amount = float(text)
    if amount <= 0:
        raise ValueError("金额必须为正")
    return round(amount, 2)


def parse_date(value) -> str:
    """支持多种常见格式，统一成 YYYY-MM-DD HH:MM:SS。"""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    raise ValueError(f"无法识别的日期：{value!r}")


def transform_record(raw: dict) -> dict:
    """单条转换：失败直接抛异常，由上层收集原因。"""
    order_id = str(raw.get("order_id", "")).strip().upper()
    if not order_id:
        raise ValueError("order_id 为空")

    status_raw = str(raw.get("status", "")).strip()
    if status_raw not in STATUS_MAP:
        raise ValueError(f"未知状态：{status_raw!r}")

    amount = parse_amount(raw.get("amount"))
    created_at = parse_date(raw.get("created_at"))

    return {
        "order_id": order_id,
        "status": STATUS_MAP[status_raw],
        "amount": amount,
        "created_at": created_at,
        "year_month": created_at[:7],                     # 派生：按月聚合
        "amount_tier": "大额" if amount >= 500 else ("中额" if amount >= 100 else "小额"),
        "is_refunded": STATUS_MAP[status_raw] == "已退款",
    }


def transform_batch(rows: list[dict]):
    good, rejected = [], []
    for raw in rows:
        try:
            good.append(transform_record(raw))
        except (ValueError, TypeError) as exc:
            rejected.append((raw, str(exc)))
    return good, rejected


# ---------------- 演示：一批“脏”数据 ----------------
RAW = [
    {"order_id": " a001 ", "status": "paid", "amount": "1,299.50", "created_at": "2026-11-12"},
    {"order_id": "A002", "status": "PAID", "amount": 99, "created_at": "2026/11/12 08:30:00"},
    {"order_id": "A003", "status": "refunded", "amount": "￥58.8", "created_at": "11/13/2026"},
    {"order_id": "", "status": "paid", "amount": 10, "created_at": "2026-11-12"},          # 缺 id
    {"order_id": "A005", "status": "unknown", "amount": 20, "created_at": "2026-11-12"},   # 状态未知
    {"order_id": "A006", "status": "paid", "amount": "abc", "created_at": "2026-11-12"},   # 金额非法
    {"order_id": "A007", "status": "paid", "amount": -5, "created_at": "2026-11-12"},      # 负数
    {"order_id": "A008", "status": "pending", "amount": 300, "created_at": "not-a-date"},  # 日期非法
]

print("== 转换结果 ==")
good, rejected = transform_batch(RAW)
print(f"成功 {len(good)} 条，拒绝 {len(rejected)} 条\n")
for r in good:
    print(f"  {r['order_id']:5s} {r['status']:3s} {r['amount']:8.2f} "
          f"{r['created_at']} | {r['year_month']} | {r['amount_tier']}")

print("\n== 拒绝明细 ==")
for raw, reason in rejected:
    print(f"  {raw.get('order_id', '<空>')!r}: {reason}")

# ---- 派生字段的用途 ----
print("\n== 派生字段用途 ==")
by_month = {}
for r in good:
    by_month.setdefault(r["year_month"], 0)
    by_month[r["year_month"]] += r["amount"]
print("  按月汇总：", by_month)
tiers = {}
for r in good:
    tiers[r["amount_tier"]] = tiers.get(r["amount_tier"], 0) + 1
print("  金额分档：", tiers)

# ---- 转换层测试示例（第212课）----
import unittest


class TestTransform(unittest.TestCase):
    def test_amount_formats(self):
        self.assertEqual(parse_amount("1,299.50"), 1299.5)
        self.assertEqual(parse_amount("￥58.8"), 58.8)

    def test_date_formats(self):
        self.assertEqual(parse_date("2026/11/12"), "2026-11-12 00:00:00")
        self.assertEqual(parse_date("11/13/2026"), "2026-11-13 00:00:00")

    def test_invalid(self):
        with self.assertRaises(ValueError):
            parse_amount(-1)
        with self.assertRaises(ValueError):
            parse_date("bad")


print("\n== 单元测试 ==")
unittest.main(exit=False, verbosity=1)

# ===== 练习题 =====
# 1. 增加字段“渠道”：把 web/app/小程序 统一成英文枚举。
# 2. parse_date 增加 ISO 8601 带时区的格式（2026-11-12T10:00:00+08:00）。
# 3. 用 pandas 重写 transform_batch，对比代码量与性能。
# 4. 思考：为什么转换函数不要直接写数据库？
