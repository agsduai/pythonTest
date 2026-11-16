# ===== 第413课：架构与重构-贫血模型与领域模型 =====
# 知识点：
#   - 贫血模型：对象只有数据（getter/setter），所有规则堆在 Service 里
#   - 领域模型：对象自己维护不变量，业务方法就在对象上
#   - 贫血的问题：规则分散、任何入口都能把对象改成非法状态
#   - 领域模型的问题：对象与持久化耦合需注意（本课只谈内存模型）
#   - 判断标准：这条规则“离开对象还成立吗”？不成立就放进对象
from dataclasses import dataclass, field
from enum import Enum


# ---------------- 贫血版 ----------------
@dataclass
class AnemicOrder:
    items: list[tuple[str, float]] = field(default_factory=list)
    status: str = "created"


class OrderService:

    def pay(self, order: AnemicOrder):
        if order.status != "created":
            raise ValueError("状态不允许支付")
        if not order.items:
            raise ValueError("空订单不能支付")
        order.status = "paid"

    def add_item(self, order: AnemicOrder, name: str, price: float):
        if price <= 0:
            raise ValueError("价格必须为正")
        order.items.append((name, price))


print("== 贫血模型：规则在 Service 里 ==")
o = AnemicOrder()
svc = OrderService()
svc.add_item(o, "键盘", 199)
svc.pay(o)
print("  状态：", o.status)
print("  风险：外部直接 o.status = '已退款' 也能改，没人拦")


# ---------------- 领域模型版 ----------------
class OrderStatus(Enum):
    CREATED = "待支付"
    PAID = "已支付"
    CANCELLED = "已取消"


@dataclass
class Order:
    items: list[tuple[str, float]] = field(default_factory=list)
    status: OrderStatus = OrderStatus.CREATED

    def add_item(self, name: str, price: float):
        if self.status is not OrderStatus.CREATED:
            raise ValueError("只能在待支付状态添加商品")
        if price <= 0:
            raise ValueError("价格必须为正")
        self.items.append((name, price))

    def pay(self):
        if self.status is not OrderStatus.CREATED:
            raise ValueError(f"当前状态「{self.status.value}」不能支付")
        if not self.items:
            raise ValueError("空订单不能支付")
        self.status = OrderStatus.PAID

    def cancel(self):
        if self.status is OrderStatus.CANCELLED:
            raise ValueError("订单已取消")
        self.status = OrderStatus.CANCELLED

    @property
    def total(self) -> float:
        return sum(p for _, p in self.items)


print("\n== 领域模型：规则在对象自己身上 ==")
order = Order()
order.add_item("键盘", 199)
order.pay()
print("  状态：", order.status.value, "| 总额：", order.total)
for action in ("重复支付", "取消"):
    try:
        order.pay() if action == "重复支付" else order.cancel()
    except ValueError as exc:
        print(f"  {action}被拦截：{exc}")

# ---- 对比总结 ----
print("\n== 对比 ==")
print("  贫血：新增入口（HTTP/定时任务）时，容易漏掉规则校验")
print("  领域：规则只有一份，任何入口都必须走对象方法")
print("  现实：小项目贫血够用；核心业务（订单/支付/库存）建议领域模型")

# ===== 练习题 =====
# 1. 给 Order 增加 refund()：只有 PAID 才能退款，退款后状态为 CANCELLED。
# 2. 在贫血版里新增“批量支付”入口，故意漏掉空订单校验，展示风险。
# 3. 思考：领域模型对象如果直接从数据库构造，如何保证加载的数据合法？
