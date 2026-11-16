# ===== 第456课：ETL与数据质量-质量报告与隔离坏数据 =====
# 知识点：
#   - 隔离区（quarantine）：坏数据单独存放，不阻断好数据入库
#   - 报告三件套：总行数/合格数/拒绝数、通过率、每类错误数量
#   - 坏数据 CSV 要带“错误原因”列，方便业务方修复后重放
#   - 报告输出 JSON（给程序）与 Markdown（给人）
#   - 通过率阈值可接告警：低于 95% 就通知（第417课）
import csv
import json
import tempfile
from datetime import datetime
from pathlib import Path

# 复用第455课的思路，本课用更紧凑的实现
REQUIRED = ["order_id", "amount", "status", "city"]
VALID_STATUS = {"paid", "refunded", "pending"}
VALID_CITY = {"北京", "上海", "广州", "深圳"}


def check_record(record: dict) -> list[str]:
    errors = []
    for field in REQUIRED:
        if not str(record.get(field, "")).strip():
            errors.append(f"{field} 不能为空")
    try:
        amount = float(record.get("amount"))
        if amount <= 0:
            errors.append("amount 必须为正")
    except (TypeError, ValueError):
        errors.append(f"amount 不是数字：{record.get('amount')!r}")
    if record.get("status") not in VALID_STATUS:
        errors.append(f"status 非法：{record.get('status')!r}")
    if record.get("city") not in VALID_CITY:
        errors.append(f"city 非法：{record.get('city')!r}")
    return errors


def split_quality(records: list[dict]):
    good, bad = [], []
    for record in records:
        errors = check_record(record)
        if errors:
            bad.append((record, errors))
        else:
            good.append(record)
    return good, bad


RAW = [
    {"order_id": "A001", "amount": "99.5", "status": "paid", "city": "北京"},
    {"order_id": "A002", "amount": "-1", "status": "paid", "city": "上海"},
    {"order_id": "", "amount": "50", "status": "pending", "city": "广州"},
    {"order_id": "A004", "amount": "abc", "status": "paid", "city": "深圳"},
    {"order_id": "A005", "amount": "200", "status": "unknown", "city": "杭州"},
    {"order_id": "A006", "amount": "300", "status": "refunded", "city": "北京"},
    {"order_id": "A007", "amount": "80", "status": "paid", "city": "上海"},
    {"order_id": "A008", "amount": "0", "status": "paid", "city": "广州"},
]

good, bad = split_quality(RAW)
total = len(RAW)
pass_rate = len(good) / total if total else 0.0

# ---- 错误分类统计 ----
error_counts = {}
for _, errors in bad:
    for error in errors:
        key = error.split("：")[0].split(" 不")[0]
        error_counts[key] = error_counts.get(key, 0) + 1

report = {
    "generated_at": datetime.now().isoformat(timespec="seconds"),
    "total": total,
    "passed": len(good),
    "rejected": len(bad),
    "pass_rate": round(pass_rate, 4),
    "error_counts": error_counts,
    "threshold": 0.95,
    "alert": pass_rate < 0.95,
}

print("== 数据质量报告 ==")
print(f"  总行数 {total} | 合格 {len(good)} | 拒绝 {len(bad)} | 通过率 {pass_rate:.1%}")
print(f"  告警（<95%）：{'是' if report['alert'] else '否'}")
print("  错误分布：", error_counts)

# ---- 写隔离文件 + JSON 报告 + Markdown 报告 ----
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    quarantine_path = tmp / "quarantine.csv"
    report_path = tmp / "quality_report.json"
    md_path = tmp / "quality_report.md"

    # 隔离 CSV：原始字段 + 错误原因
    fieldnames = ["order_id", "amount", "status", "city", "errors"]
    with open(quarantine_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record, errors in bad:
            writer.writerow({**record, "errors": "；".join(errors)})

    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# 数据质量报告",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总行数：{report['total']}",
        f"- 合格：{report['passed']}",
        f"- 拒绝：{report['rejected']}",
        f"- 通过率：{report['pass_rate']:.2%}",
        f"- 是否告警：{'是' if report['alert'] else '否'}",
        "",
        "## 错误分布",
        "",
        "| 错误类型 | 次数 |",
        "|----------|------|",
    ]
    for key, count in error_counts.items():
        md_lines.append(f"| {key} | {count} |")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print("\n== 隔离文件（前 3 行）==")
    print("\n".join(quarantine_path.read_text(encoding="utf-8-sig").splitlines()[:4]))

    print("\n== Markdown 报告 ==")
    print(md_path.read_text(encoding="utf-8"))

    print("== 文件清单 ==")
    for p in (quarantine_path, report_path, md_path):
        print(f"  {p.name}: {p.stat().st_size} 字节")

# ---- 修复后重放流程 ----
print("== 修复后重放流程 ==")
for step in [
    "1. 业务方按 quarantine.csv 的错误列修复数据",
    "2. 重放时只读隔离文件，走同一套校验",
    "3. 合格数据入库，仍不合格的保留在隔离区",
    "4. 重放必须幂等（第454课 UPSERT）",
]:
    print("  ", step)

# ===== 练习题 =====
# 1. 给报告增加“按城市统计通过率”。
# 2. 把阈值改成参数，并通过命令行传入。
# 3. 写 replay_quarantine(path) 函数：重新校验并输出仍失败的行。
# 4. 思考：为什么不能把坏数据直接丢掉，而是必须隔离？
