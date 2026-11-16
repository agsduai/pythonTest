# ===== 第418课：架构与重构-综合案例-重构遗留订单系统 =====
# 知识点：
#   - 综合运用：代码异味（415）+ 重构手法（416）+ 分层（412）+ 领域模型（413）
#   - 遗留代码改造第一步：characterization test（先锁定现有行为）
#   - 第二步：小步重构，每步跑测试，行为不变
#   - 第三步：补上新规则的测试，再改行为
#   - 本课保留旧函数作为“行为基准”，用断言证明新实现等价
import unittest
from dataclasses import dataclass, field


# ---------------- 遗留代码（不要改它）----------------
def calc_legacy(items, is_vip, coupon):
    total = 0
    for name, price, qty in items:
        total += price * qty
    if is_vip:
        total *= 0.9
    if coupon:
        total -= coupon
    if total < 0:
        total = 0
    if total >= 200:
        shipping = 0
    else:
        shipping = 10
    return round(total + shipping, 2)


# ---------------- 重构后：领域模型 + 分层 ----------------
@dataclass
class Item:
    name: str
    price: float
    qty: int

    def __post_init__(self):
        if self.price < 0:
            raise ValueError("价格不能为负")
        if self.qty <= 0:
            raise ValueError("数量必须为正")

    @property
    def subtotal(self) -> float:
        return self.price * self.qty


@dataclass
class Customer:
    name: str
    vip: bool = False


@dataclass
class Order:
    items: list[Item] = field(default_factory=list)

    def add(self, item: Item) -> "Order":
        self.items.append(item)
        return self

    @property
    def subtotal(self) -> float:
        return sum(i.subtotal for i in self.items)


# ---- 折扣策略：可扩展、可测试、可单独复用 ----
class DiscountPolicy:
    def apply(self, amount: float, customer: Customer) -> float:
        return amount


class VipDiscount(DiscountPolicy):
    RATE = 0.9

    def apply(self, amount, customer):
        return amount * self.RATE if customer.vip else amount


class CouponDiscount(DiscountPolicy):
    def __init__(self, amount: float):
        if amount < 0:
            raise ValueError("优惠券金额不能为负")
        self.amount = amount

    def apply(self, amount, customer):
        return max(0.0, amount - self.amount)


class ShippingPolicy:
    THRESHOLD = 200
    FEE = 10

    def fee(self, amount: float) -> float:
        return 0.0 if amount >= self.THRESHOLD else self.FEE


# ---- 定价服务：组合策略，流程清晰 ----
class PricingService:

    def __init__(self, discounts: list[DiscountPolicy] | None = None,
                 shipping: ShippingPolicy | None = None):
        self.discounts = discounts or []
        self.shipping = shipping or ShippingPolicy()

    def final_price(self, order: Order, customer: Customer) -> float:
        amount = order.subtotal
        for policy in self.discounts:
            amount = policy.apply(amount, customer)
        return round(amount + self.shipping.fee(amount), 2)


# ---------------- characterization test：证明重构不改行为 ----------------
class TestRefactorEquivalence(unittest.TestCase):

    CASES = [
        ([("键盘", 99, 2)], True, 10),        # 198*0.9-10=168.2 → +10 运费
        ([("鼠标", 50, 1)], False, 0),        # 50 → +10
        ([("显示器", 500, 1)], False, 0),     # 500 包邮
        ([("A", 10, 1), ("B", 20, 2)], True, 100),   # 50*0.9-100 → 0 → +10
        ([], False, 0),                       # 空订单：0 + 10
    ]

    def test_new_matches_legacy(self):
        for items, vip, coupon in self.CASES:
            order = Order()
            for name, price, qty in items:
                order.add(Item(name, price, qty))
            customer = Customer("测试", vip)
            new = PricingService(
                [VipDiscount(), CouponDiscount(coupon)]
            ).final_price(order, customer)
            old = calc_legacy(items, vip, coupon)
            self.assertEqual(new, old, f"用例不一致：{items}, vip={vip}, coupon={coupon}")


# ---------------- 重构后的附加价值：新规则易加、易测 ----------------
class TestNewBehavior(unittest.TestCase):

    def test_invalid_item_rejected(self):
        with self.assertRaises(ValueError):
            Item("坏商品", -1, 1)
        with self.assertRaises(ValueError):
            Item("坏数量", 10, 0)

    def test_coupon_cannot_go_negative(self):
        order = Order().add(Item("小件", 30, 1))
        price = PricingService([CouponDiscount(100)]).final_price(order, Customer("x"))
        self.assertEqual(price, 10.0)          # 0 + 运费 10

    def test_add_new_policy_without_touching_service(self):
        class FestivalDiscount(DiscountPolicy):
            def apply(self, amount, customer):
                return amount * 0.8

        order = Order().add(Item("礼物", 300, 1))
        price = PricingService([FestivalDiscount()]).final_price(order, Customer("x"))
        self.assertEqual(price, 240.0)         # 300*0.8，包邮

    def test_vip_and_coupon_stack(self):
        order = Order().add(Item("套装", 200, 1))
        price = PricingService(
            [VipDiscount(), CouponDiscount(20)]
        ).final_price(order, Customer("vip", vip=True))
        self.assertEqual(price, 160.0)         # 200*0.9-20=160，包邮


if __name__ == "__main__":
    print("== 新旧实现对比（5 个用例）==")
    for items, vip, coupon in TestRefactorEquivalence.CASES:
        order = Order()
        for name, price, qty in items:
            order.add(Item(name, price, qty))
        new = PricingService(
            [VipDiscount(), CouponDiscount(coupon)]
        ).final_price(order, Customer("x", vip))
        print(f"  {str(items):38s} vip={vip!s:5s} coupon={coupon:3d} "
              f"→ 旧 {calc_legacy(items, vip, coupon):7.2f} | 新 {new:7.2f}")

    print("\n===== 运行测试 =====")
    unittest.main(exit=False, verbosity=2)

# ===== 练习题 =====
# 1. 增加“满 300 减 50”策略，并补一条测试（不改 PricingService）。
# 2. 把 ShippingPolicy 改成可配置（阈值/费用来自第403课配置中心）。
# 3. 给 Order 增加 remove_item(name)，并测试空订单定价。
# 4. 思考：如果没有 characterization test，重构最怕什么？
