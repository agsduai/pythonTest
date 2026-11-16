# ===== 第521课：消息队列与事件驱动-事件溯源 =====
# 知识点：
#   - 事件溯源（Event Sourcing）：只存“发生了什么”，当前状态由事件重放得到
#   - 事件日志只追加（append-only），不可修改；修正靠追加补偿事件
#   - 状态 = reduce(events)；快照（snapshot）加速重建
#   - 好处：完整审计、可回放、可重建任意时点状态
#   - 代价：查询不便（需投影/读模型）、事件版本演进、存储增长
#   - 与第520课 Outbox 的区别：Outbox 是“可靠发事件”，事件溯源是“以事件为数据源”
#   - 与第512课拉链表：都在保留历史，但事件溯源记录“原因”，不是“结果”
import json


class EventStore:
    def __init__(self):
        self.events = []               # [{seq, type, data}]

    def append(self, event_type: str, data: dict):
        event = {"seq": len(self.events) + 1, "type": event_type, "data": data}
        self.events.append(event)
        return event

    def load(self, until=None):
        return self.events[:until] if until else list(self.events)


class BankAccount:
    """事件溯源版账户：状态由事件重放得到。"""

    def __init__(self, account_id: str, store: EventStore):
        self.account_id = account_id
        self.store = store
        self.balance = 0.0
        self.version = 0
        self.replay()

    def replay(self, until=None):
        self.balance = 0.0
        self.version = 0
        for event in self.store.load(until):
            if event["data"].get("account_id") != self.account_id:
                continue
            self._apply(event)
            self.version = event["seq"]

    def _apply(self, event):
        if event["type"] == "deposited":
            self.balance += event["data"]["amount"]
        elif event["type"] == "withdrawn":
            self.balance -= event["data"]["amount"]
        else:
            raise ValueError(f"未知事件：{event['type']}")

    # ---- 命令：校验后追加事件 ----
    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("存款必须为正")
        self.store.append("deposited", {"account_id": self.account_id, "amount": amount})
        self.replay()

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("取款必须为正")
        if amount > self.balance:
            raise ValueError(f"余额不足：{self.balance}")
        self.store.append("withdrawn", {"account_id": self.account_id, "amount": amount})
        self.replay()

    def state_at(self, seq):
        """重建任意历史时点。"""
        temp = BankAccount.__new__(BankAccount)
        temp.account_id = self.account_id
        temp.store = self.store
        temp.replay(until=seq)
        return temp.balance


store = EventStore()
account = BankAccount("A100", store)

print("== 执行命令 ==")
account.deposit(100)
account.withdraw(30)
account.deposit(50)
account.withdraw(20)

print("\n== 事件日志 ==")
for e in store.events:
    print(f"  #{e['seq']} {e['type']:10s} {e['data']}")

print(f"\n当前余额：{account.balance} 元（version={account.version}）")

print("\n== 历史时点重建 ==")
for seq in (1, 2, 3, 4):
    print(f"  第 {seq} 个事件后余额：{account.state_at(seq)} 元")

# ---- 非法命令不产生事件 ----
print("\n== 非法命令 ==")
try:
    account.withdraw(1000)
except ValueError as exc:
    print("  拦截：", exc)
print("  事件数仍为：", len(store.events), "（失败命令不落日志）")

# ---- 补偿事件而不是修改历史 ----
print("\n== 修正：追加补偿事件 ==")
account.deposit(5)                    # 假设发现少记了 5 元
print("  最新余额：", account.balance)
print("  历史事件不可改，只追加；审计链完整")

# ---- 快照优化 ----
print("\n== 快照（加速重建）==")
class SnapshotStore:
    def __init__(self):
        self.snapshots = {}

    def save(self, account_id, seq, balance):
        self.snapshots[seq] = {"account_id": account_id, "balance": balance}
        print(f"  [快照] seq={seq} 余额={balance}")

    def latest_before(self, seq):
        candidates = [s for s in self.snapshots if s <= seq]
        return max(candidates) if candidates else None


snapshots = SnapshotStore()
snapshots.save("A100", 3, 120.0)
snap = snapshots.latest_before(4)
print(f"  重建 seq=4 时：从快照 {snap} 开始，只需重放 {4 - snap} 个事件")

# ---- 投影（读模型）----
print("\n== 投影：给查询用的读模型 ==")
projection = {"A100": {"deposits": 0, "withdrawals": 0}}
for e in store.events:
    if e["data"].get("account_id") != "A100":
        continue
    if e["type"] == "deposited":
        projection["A100"]["deposits"] += e["data"]["amount"]
    else:
        projection["A100"]["withdrawals"] += e["data"]["amount"]
print("  ", projection)
print("  读模型可以按查询需求重建（聚合、索引、宽表）")

# ---- 适用性 ----
print("\n== 适用与不适用 ==")
for item in [
    "适合：金融账务、订单状态、库存流水等需要完整审计的场景",
    "适合：需要回放/重建任意时点、需要事件驱动下游",
    "不适合：简单 CRUD、强实时复杂查询（要额外投影）",
    "难点：事件 schema 演进、快照策略、隐私数据删除",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 增加 transferred 事件（转出+转入），保证原子性。
# 2. 实现“每个账户每 10 个事件自动快照”。
# 3. 写投影：每日净流入金额。
# 4. 思考：事件溯源中“删除用户数据”为什么比普通表难？
