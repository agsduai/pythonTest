# ===== 第674课：有限状态机与工作流-综合案例-订单履约工作流 =====
# 知识点：
#   - 综合串起本章：转移表 FSM + 守卫/动作 + 层次状态 + 事件溯源 + Saga 补偿 + 规则引擎
#   - 订单履约链路：待支付 -> 已支付 -> 仓库拣货/支付核验并行 -> 发货 -> 签收 -> 完成
#   - 异常分支：超时未支付自动取消、风控拒单、缺货触发退款补偿
#   - 全部状态变化以「事件」追加，可重放、可时间旅行、可审计
#   - 可注入时钟与执行器，无真实 sleep / 无外部依赖 / 离线可运行
#   - 分层：Rule(准入) -> FSM(状态) -> EventLog(持久化) -> Saga(补偿) -> Report(投影)
# 依赖：无（标准库）
import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

PENDING, PAID, PICKING, SHIPPED, RECEIVED, DONE, CANCELLED, REFUNDING = (
    "待支付", "已支付", "拣货中", "已发货", "已签收", "已完成", "已取消", "退款中")


@dataclass
class Clock:
    now: float = 0.0
    def advance(self, d): self.now += d


@dataclass
class Event:
    seq: int
    type: str
    at: float
    payload: dict = field(default_factory=dict)


@dataclass
class Order:
    state: str = PENDING
    amount: int = 0
    stock_reserved: bool = False
    paid: bool = False
    version: int = 0


# ---- 规则引擎（准入） ----
def risk_check(facts):
    if facts.get("risk") == "high":
        return "拒绝：风控命中"
    if facts["amount"] > 50000:
        return "拒绝：超单笔限额"
    return "通过"

# ---- FSM 转移表：(state, event) -> (target, guard, action, desc) ----
def pay(o, p, clock):
    o.paid = True
    return "扣款成功"

def reserve(o, p, clock):
    if p.get("out_of_stock"):
        return "缺货"
    o.stock_reserved = True
    return "库存已预留"

def refund(o, p, clock):
    o.paid = False
    o.stock_reserved = False
    return "已退款并释放库存"


def build_table():
    return {
        (PENDING, "支付"): (PAID, None, pay, "支付完成"),
        (PENDING, "超时"): (CANCELLED, None, None, "超时未支付自动取消"),
        (PENDING, "风控拒绝"): (CANCELLED, None, None, "风控拒单"),
        (PAID, "开始拣货"): (PICKING, None, reserve, "进入拣货"),
        (PAID, "申请退款"): (REFUNDING, None, refund, "未发货退款"),
        (PICKING, "缺货"): (REFUNDING, None, refund, "缺货触发补偿"),
        (PICKING, "发货"): (SHIPPED, lambda o, p: o.stock_reserved, None, "出库发货"),
        (SHIPPED, "签收"): (RECEIVED, None, None, "客户签收"),
        (RECEIVED, "确认完成"): (DONE, None, None, "订单完成"),
        (REFUNDING, "退款完成"): (CANCELLED, None, None, "流程终止"),
    }


class OrderWorkflow:
    def __init__(self, order=None, clock=None):
        self.order = order or Order()
        self.clock = clock or Clock()
        self.events = []
        self.table = build_table()
        self.seq = 0

    def _emit(self, type_, payload=None):
        self.seq += 1
        self.events.append(Event(self.seq, type_, self.clock.now, payload or {}))

    def send(self, event, **payload):
        key = (self.order.state, event)
        if key not in self.table:
            self._emit("非法事件", {"event": event, "state": self.order.state})
            return False
        target, guard, action, desc = self.table[key]
        if guard and not guard(self.order, payload):
            self._emit("守卫拒绝", {"event": event})
            return False
        detail = action(self.order, payload, self.clock) if action else ""
        old = self.order.state
        self.order.state = target
        self.order.version += 1
        self._emit(desc, {"from": old, "to": target, "detail": detail})
        return True

    def replay(self, upto=None):
        """从事件日志重建「状态时间线」，验证可追溯。"""
        timeline = []
        for e in self.events[:upto]:
            if "to" in e.payload:
                timeline.append((e.at, e.type, e.payload["to"]))
        return timeline

    def report(self):
        return {"state": self.order.state, "version": self.order.version,
                "paid": self.order.paid, "stock_reserved": self.order.stock_reserved,
                "event_count": len(self.events)}


print("== 场景 1：正常履约 ==")
w = OrderWorkflow(Order(amount=899), Clock())
seq = [("支付", {}), ("开始拣货", {}), ("发货", {}), ("签收", {}), ("确认完成", {})]
for ev, p in seq:
    w.clock.advance(1)
    ok = w.send(ev, **p)
    print(f"  {ev:<8} -> {w.order.state:<6} 接受={ok}")
print("  终态:", w.report())

print("\n== 场景 2：风控拒单（规则前置）==")
w2 = OrderWorkflow(Order(amount=999999), Clock())
print("  准入判定:", risk_check({"risk": "low", "amount": 999999}))
w2.send("风控拒绝")
print("  终态:", w2.report())

print("\n== 场景 3：超时未支付 ==")
w3 = OrderWorkflow(Order(amount=100), Clock())
w3.clock.advance(1800)
w3.send("超时")
print("  终态:", w3.report())

print("\n== 场景 4：缺货 -> Saga 补偿退款 ==")
w4 = OrderWorkflow(Order(amount=299), Clock())
for ev, p in (("支付", {}), ("开始拣货", {"out_of_stock": True}), ("缺货", {}), ("退款完成", {})):
    w4.send(ev, **p)
print("  终态:", w4.report())
print(f"  已退款={not w4.order.paid}  库存已释放={not w4.order.stock_reserved}")

print("\n== 事件溯源：时间线可重放 ==")
for at, name, state in w.replay():
    print(f"  t={at:>4.0f}  {name:<12} -> {state}")
print("  重放到第 3 条:", [s for _, _, s in w.replay(upto=3)])

print("\n== 非法转移被记录而不是崩溃 ==")
w5 = OrderWorkflow(Order(amount=10), Clock())
w5.send("签收")     # 待支付直接签收，非法
print("  ", w5.events[-1].type, w5.events[-1].payload)
print("  终态仍是:", w5.order.state)

print("\n== 持久化事件日志 ==")
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "order_events.json"
    data = [{"seq": e.seq, "type": e.type, "at": e.at, "payload": e.payload}
            for e in w.events]
    p.write_text(json.dumps(data, ensure_ascii=False), "utf-8")
    loaded = json.loads(p.read_text("utf-8"))
    print(f"  {p.name}: {p.stat().st_size} 字节，{len(loaded)} 条事件")
    print("  末条:", loaded[-1]["type"], loaded[-1]["payload"])
    print("  事件只追加、带 seq 与时间戳，可直接进审计系统/Outbox（第53章）")

print("\n== 分层回顾 ==")
for line in [
    "  规则层  : risk_check 做准入，拒绝则不进入 FSM（第673课）",
    "  状态层  : 转移表 + 守卫 + 动作，非法事件可观测（第667/668课）",
    "  溯源层  : 每次变化记不可变事件，可重放/时间旅行（第671课）",
    "  补偿层  : 缺货/退款走 Saga 逆操作，回到一致终态（第672课）",
    "  投影层  : report() 从当前状态出报表，不污染事件日志",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加「已发货后 7 天自动确认完成」的定时任务（第68章）驱动。
# 2. 实现并行分支：拣货与发票开具 AND 汇聚后才允许发货（第670课）。
# 3. 给事件加 event_id 幂等去重，验证重复投递支付事件不会重复扣款。
# 4. 思考：为什么「状态」与「事件」要同时保留，只留其一各有什么问题？
