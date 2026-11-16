# ===== 第458课：ETL与数据质量-综合案例-电商日订单ETL =====
# 知识点：
#   - 综合运用：抽取（452）+ 转换（453）+ 质量规则（455/456）+ 幂等加载（454）
#   - 端到端流程：原始 CSV → 校验/清洗 → 隔离坏数据 → UPSERT 入库 → 生成报告
#   - 可重跑：同一份原始数据跑两次，目标表行数不变
#   - 交付物：dw_orders 表、quarantine.csv、etl_report.json/md
import csv
import json
import random
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

VALID_STATUS = {"paid", "refunded", "pending"}
VALID_CITY = {"北京", "上海", "广州", "深圳"}


# ---------------- 1. 生成原始数据（含脏数据） ----------------
def generate_raw(path: Path, n=120, seed=7):
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        order_id = f"ORD{i:04d}"
        amount = rng.randint(10, 2000)
        status = rng.choice(list(VALID_STATUS))
        city = rng.choice(list(VALID_CITY))
        created = f"2026-11-{rng.randint(1, 30):02d} {rng.randint(0, 23):02d}:00:00"

        # 注入脏数据
        r = rng.random()
        if r < 0.05:
            order_id = ""                       # 缺主键
        elif r < 0.10:
            amount = "abc"                      # 金额非法
        elif r < 0.15:
            status = "unknown"                  # 状态非法
        elif r < 0.18:
            city = "火星"                        # 城市非法
        elif r < 0.20:
            created = "2026-13-40"              # 日期非法
        if i % 17 == 0 and i > 0:
            rows[-1]["order_id"] = order_id     # 制造重复订单号
        rows.append({"order_id": order_id, "amount": amount, "status": status,
                     "city": city, "created_at": created})

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["order_id", "amount", "status",
                                               "city", "created_at"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


# ---------------- 2. 转换 + 质量规则 ----------------
def transform_row(raw: dict):
    """合格返回 (记录, None)，否则 (None, [错误...])。"""
    errors = []
    order_id = str(raw.get("order_id", "")).strip().upper()
    if not order_id:
        errors.append("order_id 为空")

    try:
        amount = float(str(raw.get("amount", "")).replace(",", ""))
        if amount <= 0:
            errors.append("amount 必须为正")
    except (TypeError, ValueError):
        errors.append(f"amount 非法：{raw.get('amount')!r}")
        amount = None

    status = str(raw.get("status", "")).strip()
    if status not in VALID_STATUS:
        errors.append(f"status 非法：{status!r}")

    city = str(raw.get("city", "")).strip()
    if city not in VALID_CITY:
        errors.append(f"city 非法：{city!r}")

    created = str(raw.get("created_at", "")).strip()
    try:
        created_dt = datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        errors.append(f"created_at 非法：{created!r}")
        created_dt = None

    if errors:
        return None, errors
    return {
        "order_id": order_id,
        "amount": round(amount, 2),
        "status": status,
        "city": city,
        "created_at": created_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "year_month": created_dt.strftime("%Y-%m"),
        "amount_tier": "大额" if amount >= 500 else "小额",
    }, None


# ---------------- 3. 主流程 ----------------
def run_etl(raw_csv: Path, db_path: Path, out_dir: Path):
    out_dir.mkdir(exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dw_orders (
            order_id TEXT PRIMARY KEY,
            amount REAL, status TEXT, city TEXT,
            created_at TEXT, year_month TEXT, amount_tier TEXT,
            loaded_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS etl_runs (
            run_at TEXT, total INTEGER, passed INTEGER, rejected INTEGER
        )
    """)
    conn.commit()

    # Extract
    with open(raw_csv, encoding="utf-8-sig", newline="") as f:
        raw_rows = list(csv.DictReader(f))

    # Transform + Validate
    good, bad = [], []
    for raw in raw_rows:
        record, errors = transform_row(raw)
        if errors:
            bad.append((raw, errors))
        else:
            good.append(record)

    # 去重（同一订单号保留最后一条）
    deduped = {}
    for r in good:
        deduped[r["order_id"]] = r
    duplicates = len(good) - len(deduped)
    good = list(deduped.values())

    # Load（UPSERT，可重跑）
    for r in good:
        conn.execute("""
            INSERT INTO dw_orders
            (order_id, amount, status, city, created_at, year_month, amount_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(order_id) DO UPDATE SET
                amount = excluded.amount,
                status = excluded.status,
                city = excluded.city,
                created_at = excluded.created_at,
                year_month = excluded.year_month,
                amount_tier = excluded.amount_tier,
                loaded_at = datetime('now')
        """, (r["order_id"], r["amount"], r["status"], r["city"],
              r["created_at"], r["year_month"], r["amount_tier"]))
    conn.commit()

    # 隔离坏数据
    quarantine = out_dir / "quarantine.csv"
    with open(quarantine, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(raw_rows[0].keys()) + ["errors"])
        writer.writeheader()
        for raw, errors in bad:
            writer.writerow({**raw, "errors": "；".join(errors)})

    # 报告
    total = len(raw_rows)
    passed = len(good)
    report = {
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "total": total,
        "passed": passed,
        "rejected": len(bad),
        "duplicates_removed": duplicates,
        "pass_rate": round(passed / total, 4) if total else 0,
        "dw_rows": conn.execute("SELECT COUNT(*) FROM dw_orders").fetchone()[0],
    }
    (out_dir / "etl_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "etl_report.md").write_text(
        "# 日订单 ETL 报告\n\n"
        + "\n".join(f"- {k}: {v}" for k, v in report.items()) + "\n",
        encoding="utf-8",
    )

    conn.execute("INSERT INTO etl_runs (run_at, total, passed, rejected) VALUES (?, ?, ?, ?)",
                 (report["run_at"], total, passed, len(bad)))
    conn.commit()

    # 汇总查询
    summary = conn.execute("""
        SELECT year_month, status, COUNT(*) AS cnt, ROUND(SUM(amount), 2) AS total
        FROM dw_orders GROUP BY year_month, status ORDER BY year_month, status
    """).fetchall()

    conn.close()
    return report, summary, quarantine


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    raw_csv = tmp / "raw_orders.csv"
    db_path = tmp / "warehouse.db"
    out_dir = tmp / "out"

    n = generate_raw(raw_csv)
    print(f"原始数据：{n} 条")

    print("\n== 第一次运行 ==")
    report, summary, quarantine = run_etl(raw_csv, db_path, out_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))

    print("\n== 汇总（月份 × 状态）==")
    for row in summary:
        print(f"  {row[0]} {row[1]:9s} {row[2]:3d} 单 {row[3]:10.2f} 元")

    print("\n== 第二次运行（验证幂等）==")
    report2, _, _ = run_etl(raw_csv, db_path, out_dir)
    print("  目标表行数：", report["dw_rows"], "→", report2["dw_rows"],
          "（不变即幂等）")
    print("  通过率：", f"{report['pass_rate']:.1%}")
    print("  隔离文件：", quarantine.name, f"（{len(quarantine.read_text(encoding='utf-8-sig').splitlines()) - 1} 条坏数据）")

    print("\n== 报告文件 ==")
    print((out_dir / "etl_report.md").read_text(encoding="utf-8"))

# ===== 练习题 =====
# 1. 给 ETL 增加“按城市分区统计”的报表。
# 2. 把重复订单处理改成“保留最新 created_at 的一条”。
# 3. 接第457课：断点续跑 + 失败重跑同一份文件。
# 4. 思考：如果源数据每天全量 100 万行，但只变 1 万行，怎么优化？
