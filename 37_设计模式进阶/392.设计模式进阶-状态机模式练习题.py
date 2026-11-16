# ===== 第392课：设计模式进阶-状态机模式 =====
# 知识点：
#   - 状态机：对象的行为取决于当前状态；状态只能按“允许的迁移”变化
#   - 用枚举 + 迁移表，把散落各处的 if/elif 收敛成一张可读的规则表
#   - 非法迁移立即报错 —— 比“允许一切、事后收拾”安全得多
#   - 场景：订单、工单、审批、连接池、游戏角色
from enum import Enum


class OrderState(Enum):
    CREATED = "待支付"
    PAID = "已支付"
    SHIPPED = "已发货"
    COMPLETED = "已完成"
    CANCELLED = "已取消"


# 迁移表：当前状态 → {动作: 下一个状态}
TRANSITIONS: dict[OrderState, dict[str, OrderState]] = {
    OrderState.CREATED: {
        "pay": OrderState.PAID,
        "cancel": OrderState.CANCELLED,
    },
    OrderState.PAID: {
        "ship": OrderState.SHIPPED,
        "refund": OrderState.CANCELLED,
    },
    OrderState.SHIPPED: {
        "confirm": OrderState.COMPLETED,
    },
    OrderState.COMPLETED: {},          # 终态
    OrderState.CANCELLED: {},          # 终态
}


class InvalidTransition(Exception):
    pass


class Order:

    def __init__(self, order_id: str):
        self.order_id = order_id
        self.state = OrderState.CREATED
        self.history: list[str] = [f"创建订单（{self.state.value}）"]

    def do(self, action: str) -> OrderState:
        allowed = TRANSITIONS[self.state]
        if action not in allowed:
            raise InvalidTransition(
                f"订单 {self.order_id} 状态为「{self.state.value}」，"
                f"不允许执行「{action}」。可用动作：{list(allowed) or '无（终态）'}"
            )
        old = self.state
        self.state = allowed[action]
        self.history.append(f"{old.value} --{action}--> {self.state.value}")
        return self.state

    def available_actions(self) -> list[str]:
        return list(TRANSITIONS[self.state])

    def __repr__(self):
        return f"Order({self.order_id}, {self.state.value})"


# ---- 正常流程 ----
print("== 正常流程 ==")
o = Order("A001")
for action in ("pay", "ship", "confirm"):
    o.do(action)
    print(f"  {action:8s} → {o.state.value}")

print("\n状态历史：")
for line in o.history:
    print("  ", line)
print("终态可用动作：", o.available_actions())

# ---- 非法迁移 ----
print("\n== 非法迁移 ==")
o2 = Order("A002")
o2.do("pay")
try:
    o2.do("confirm")               # 未发货不能确认收货
except InvalidTransition as exc:
    print("  拦截：", exc)

# ---- 取消分支 ----
print("\n== 取消分支 ==")
o3 = Order("A003")
o3.do("cancel")
print("  状态：", o3.state.value)
try:
    o3.do("pay")
except InvalidTransition as exc:
    print("  终止态不能再支付：", exc)

# ---- 状态统计（便于监控）----
print("\n== 状态分布统计 ==")
orders = [Order("A004"), Order("A005"), Order("A006")]
orders[0].do("pay")
orders[1].do("cancel")
counts = {}
for order in orders:
    counts[order.state.value] = counts.get(order.state.value, 0) + 1
print("  ", counts)

# ===== 练习题 =====
# 1. 给 PAID 状态增加 "timeout" 动作，迁移到 CANCELLED（超时未发货）。
# 2. 增加状态 “退款中”，设计 PAID → REFUNDING → CANCELLED/PAID 的迁移。
# 3. 把迁移表改成“外部配置 JSON”，启动时加载（结合第398课）。
# 4. 思考：状态机与第349课 Enum 单独使用的区别在哪？
