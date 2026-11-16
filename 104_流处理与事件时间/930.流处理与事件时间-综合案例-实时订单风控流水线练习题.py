# ===== 第930课：流处理与事件时间-综合案例-实时订单风控流水线 =====
# 知识点：
#   - 综合本章：双时钟(924) + 水印(925) + 窗口(925) + 撤回(926) +
#     Join(927) + CEP(928) + 去重(929)
#   - 流水线拓扑：去重 → 水印推进 → 订单/支付流 Join → 窗口聚合 → CEP 告警
#   - 每个算子都是一个类：process(event) -> 输出 —— 可独立测试
#   - 端到端校验：最终聚合结果与「离线真值」对照
#   - 输出 ASCII 拓扑图与运行报告
# 依赖：无（标准库）
import random
from collections import defaultdict


# ---------- 算子 1：去重 ----------
class Dedup:
    def __init__(self):
        self.seen = set()

    def process(self, event):
        eid = (event["type"], event["oid"])
        if eid in self.seen:
            return None
        self.seen.add(eid)
        return event


# ---------- 算子 2：水印追踪 ----------
class Watermark:
    def __init__(self, lateness=3):
        self.lateness = lateness
        self.max_et = None

    def process(self, event):
        self.max_et = event["et"] if self.max_et is None \
            else max(self.max_et, event["et"])
        return self.max_et - self.lateness


# ---------- 算子 3：订单×支付 Join ----------
class OrderPaymentJoin:
    def __init__(self, timeout=8):
        self.timeout = timeout
        self.buffer = {"order": {}, "payment": {}}
        self.matched = []
        self.unpaid = []
        self.unordered = []

    def process(self, event):
        side = event["type"]
        key = event["oid"]
        et = event["et"]
        self.buffer[side][key] = (et, event)
        other = "payment" if side == "order" else "order"
        if key in self.buffer[other]:
            o = self.buffer["order"][key]
            p = self.buffer["payment"][key]
            gap = abs(o[0] - p[0])
            if gap <= self.timeout:
                self.matched.append((key, o[1]["amount"], p[1]["amount"], gap))
                self.buffer["order"].pop(key, None)
                self.buffer["payment"].pop(key, None)
                return ("matched", key)
        return None


# ---------- 算子 4：CEP 风控规则 ----------
class FraudRule:
    """同一用户连续 2 笔未支付订单（et 差 < 10）→ 告警。"""

    def __init__(self):
        self.unpaid_by_user = defaultdict(list)
        self.alerts = []

    def process(self, event):
        if event["type"] != "order" or event.get("unpaid") is not True:
            return None
        events = self.unpaid_by_user[event["uid"]]
        events.append(event["et"])
        events[:] = [e for e in events if event["et"] - e < 10]
        if len(events) >= 2:
            self.alerts.append((event["uid"], list(events)))
            self.unpaid_by_user[event["uid"]] = []
            return ("alert", event["uid"])
        return None


# ---------- 生成数据 ----------
rng = random.Random(116)
events = []
oid = 0
for et in range(0, 60, 5):
    for uid in ("u1", "u2", "u3"):
        oid += 1
        okey = f"o{oid}"
        events.append({"type": "order", "oid": okey, "uid": uid,
                       "et": et, "amount": rng.randint(50, 500)})
        # 大多数订单随后有支付；给 u3 留两笔连续未支付（触发风控）
        if not (uid == "u3" and et in (30, 35)):
            events.append({"type": "payment", "oid": okey, "uid": uid,
                           "et": et + rng.randint(1, 4),
                           "amount": 0})
        if rng.random() < 0.15:                   # 网络重传 → 重复事件
            events.append({"type": "order", "oid": okey, "uid": uid,
                           "et": et, "amount": events[-2]["amount"]})
events.sort(key=lambda e: e["et"])

print("== 输入流（订单 + 支付，含重复投递）==")
type_counts = defaultdict(int)
for e in events:
    type_counts[e["type"]] += 1
print(f"  事件总数 {len(events)}: {dict(type_counts)}")
print("  u3 在 et=30/35 各有一笔未支付订单 → 应触发风控告警")

print("\n== 流水线拓扑 ==")
print("""
  事件流 → [Dedup 去重] → [Watermark 推进] ─┬→ [OrderPaymentJoin] → 匹配/未支付
                                            └──────────────→ [FraudRule CEP] → 告警
""")

# ---------- 运行流水线 ----------
dedup = Dedup()
wm = Watermark(lateness=3)
join = OrderPaymentJoin(timeout=8)
rule = FraudRule()
alert_log = []
unpaid_detected = []

for e in events:
    e2 = dedup.process(e)
    if e2 is None:
        continue
    wm.process(e2)
    join.process(e2)

# 流结束后：仍留在 Join 缓冲里的订单 = 未支付 → 喂给 CEP 风控
for e in events:
    if e["type"] == "order" and e["oid"] in join.buffer["order"]:
        e["unpaid"] = True
        unpaid_detected.append(e)
        alert = rule.process(e)
        if alert:
            alert_log.append(alert)

print("\n== 运行结果 ==")
print(f"  唯一事件进入流水线 = {len(dedup.seen)} 个（重复投递已在去重层丢弃）")
print(f"  订单-支付匹配成功 = {len(join.matched)} 对")
for key, amount, pay, gap in join.matched[:6]:
    print(f"    {key}: 订单 {amount} 元 / 支付 {gap}s 后到账")
print(f"  ... 共 {len(join.matched)} 对")
print(f"  未支付订单（进入风控）= {len(unpaid_detected)} 笔")
for e in unpaid_detected:
    print(f"    {e['oid']} (用户 {e['uid']}, et={e['et']}, {e['amount']} 元)")
print(f"  风控告警 = {len(alert_log)} 条")
for uid, ets in alert_log:
    print(f"    用户 {uid}: 连续未支付 at {ets}")

print("\n== 端到端校验 ==")
truth_unpaid = {e["oid"] for e in events
                if e["type"] == "order"
                and not any(p["oid"] == e["oid"]
                            for p in events if p["type"] == "payment")}
detected = {e["oid"] for e in unpaid_detected}
print(f"  离线真值未支付订单: {sorted(truth_unpaid)}")
print(f"  流水线检出:        {sorted(detected)}")
print(f"  一致: {truth_unpaid == detected}")
dupes = len(events) - len(dedup.seen)
print(f"  去重生效: {dupes} 个重复投递被丢弃（不影响匹配与告警）")

print("\n== 窗口视角：每 10 秒的成交额 ==")
win_amount = defaultdict(int)
for key, amount, pay, gap in join.matched:
    order_et = next(e["et"] for e in events
                    if e["type"] == "order" and e["oid"] == key)
    win_amount[order_et // 10 * 10] += amount
print(f"  {'窗口起点':>10}{'成交额':>10}")
for start in sorted(win_amount):
    print(f"  {start:>10}{win_amount[start]:>10}  "
          f"{'#' * int(win_amount[start] / max(win_amount.values()) * 40)}")

print("\n== 本章全景 ==")
for line in (
    "  事件时间/处理时间 → 水印 → 窗口 → Join → CEP → 去重 → 幂等",
    "  每个环节都在解决同一个矛盾：无限流 vs 有限的计算与内存",
    "  watermark 是『时间维度的检查点』，去重是『内容维度的检查点』",
    "  生产系统（Flink/Kafka Streams）把这些原语产品化，本章是它们的骨架",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给流水线加「滑动窗口成交额」算子（925 课），对比滚动窗口结果。
# 2. 实现「撤回」：迟到支付到达已判 unpaid 的订单时，撤回告警。
# 3. 加「每用户并行度」：按 uid 分组后各自独立运行 Join/CEP，对比结果。
# 4. 思考：如果把全部算子换成「批处理」（数据到齐后再算），哪些环节可以
#    简化？哪些业务价值会丢失？
