# ===== 第451课：ETL与数据质量-ETL概述与管道骨架 =====
# 知识点：
#   - ETL = Extract（抽取）→ Transform（转换）→ Load（加载）
#   - 抽取：从 CSV/Excel/数据库/API 拿到原始数据
#   - 转换：清洗、类型转换、映射、派生字段、校验
#   - 加载：写入目标库，必须幂等（第447课）以便重跑
#   - 管道要有统计与拒绝记录：处理了多少、成功多少、丢弃多少、为什么
#   - 本课先搭骨架，后续逐课替换每一步的实现
from dataclasses import dataclass, field


@dataclass
class PipelineStats:
    extracted: int = 0
    transformed: int = 0
    rejected: int = 0
    loaded: int = 0
    errors: list[tuple] = field(default_factory=list)

    def summary(self) -> str:
        return (f"抽取 {self.extracted} 条 → 转换成功 {self.transformed} 条 / "
                f"拒绝 {self.rejected} 条 → 加载 {self.loaded} 条")


# ---------------- 三个阶段的“接口” ----------------
def extract() -> list[dict]:
    """本课用内存数据模拟；后续课换成 CSV/Excel/SQL/API。"""
    return [
        {"order_id": "A001", "amount": "99.5", "status": "paid", "updated_at": "2026-11-12 10:00:00"},
        {"order_id": "A002", "amount": "199", "status": "paid", "updated_at": "2026-11-12 10:05:00"},
        {"order_id": "A003", "amount": "bad", "status": "paid", "updated_at": "2026-11-12 10:10:00"},
        {"order_id": "A004", "amount": "50", "status": "refunded", "updated_at": "2026-11-12 10:20:00"},
    ]


def transform(records: list[dict]):
    """清洗 + 校验：返回 (合格记录, 拒绝记录[(原记录, 原因)])。"""
    good, rejected = [], []
    for r in records:
        try:
            amount = float(r["amount"])
            if amount <= 0:
                raise ValueError("金额必须为正")
            good.append({
                **r,
                "amount": amount,
                "status": r["status"].lower(),
                "updated_at": r["updated_at"],
            })
        except (ValueError, TypeError, KeyError) as exc:
            rejected.append((r, f"转换失败：{exc}"))
    return good, rejected


def load(records: list[dict]) -> int:
    """本课只打印；真实实现见第454课（UPSERT + 增量）。"""
    for r in records:
        print(f"    [加载] {r['order_id']} {r['amount']} {r['status']}")
    return len(records)


def run_pipeline() -> PipelineStats:
    stats = PipelineStats()
    raw = extract()
    stats.extracted = len(raw)

    good, rejected = transform(raw)
    stats.transformed = len(good)
    stats.rejected = len(rejected)
    stats.errors.extend(rejected)

    stats.loaded = load(good)
    return stats


print("== 运行 ETL 管道 ==")
stats = run_pipeline()
print("\n统计：", stats.summary())
if stats.errors:
    print("拒绝明细：")
    for record, reason in stats.errors:
        print(f"  {record.get('order_id', '?')}: {reason}")

# ---- 为什么要记录“拒绝”而不是静默丢弃 ----
print("\n== 设计原则 ==")
for item in [
    "拒绝记录必须可见：哪个订单、哪条规则、什么原因",
    "坏数据进入隔离区（quarantine），修好后可重放（第456课）",
    "每步都要幂等：重跑不产生重复（第454课）",
    "统计信息写入日志/报表，便于监控（第417课）",
    "失败要能断点续跑，而不是每次从头再来（第457课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 PipelineStats 增加耗时字段（每阶段耗时）。
# 2. 把三段函数换成可插拔的类（Protocol），为下一课做准备。
# 3. 思考：为什么“转换阶段丢数据”比“加载阶段丢数据”更安全？
