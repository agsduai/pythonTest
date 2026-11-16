# ===== 第415课：架构与重构-常见代码异味 =====
# 知识点：
#   - 代码异味：能跑但“闻起来不对”的信号，提示未来维护成本高
#   - 常见六种：长函数、魔法数字、重复代码、基本类型偏执、特性依恋、深层嵌套
#   - 处理顺序：先补测试 → 小步重构 → 每次保持可运行（第416课）
#   - 异味不是 bug，但会持续制造 bug

# ---------------- 1. 长函数 → 提取方法 ----------------
def process_order_bad(items, vip, coupon):
    total = 0
    for name, price, qty in items:
        total += price * qty
    if vip:
        total *= 0.9
    if coupon:
        total -= coupon
    if total < 0:
        total = 0
    shipping = 0 if total >= 200 else 10
    return round(total + shipping, 2)


def _subtotal(items):
    return sum(price * qty for _, price, qty in items)


def _apply_discounts(total, vip, coupon):
    if vip:
        total *= 0.9
    return max(0, total - coupon)


def _shipping(total):
    return 0 if total >= 200 else 10


def process_order_good(items, vip, coupon):
    total = _apply_discounts(_subtotal(items), vip, coupon)
    return round(total + _shipping(total), 2)


print("== 长函数 ==")
print("  两者结果一致：", process_order_bad([("键盘", 99, 2)], True, 10)
      == process_order_good([("键盘", 99, 2)], True, 10))


# ---------------- 2. 魔法数字 → 命名常量 ----------------
VIP_DISCOUNT = 0.9
FREE_SHIPPING_THRESHOLD = 200
SHIPPING_FEE = 10


def final_price_bad(total, vip):
    return round(total * (0.9 if vip else 1) + (0 if total >= 200 else 10), 2)


def final_price_good(total, vip):
    price = total * (VIP_DISCOUNT if vip else 1)
    return round(price + (0 if price >= FREE_SHIPPING_THRESHOLD else SHIPPING_FEE), 2)


print("\n== 魔法数字 ==")
print("  198 元 VIP：", final_price_good(198, True), "（打 9 折后包邮门槛变了，好改多了）")


# ---------------- 3. 重复代码 → 抽公共函数 ----------------
def report_sales_bad(rows):
    total = 0
    for r in rows:
        total += r["amount"]
    return f"销售额 {total}"


def report_refund_bad(rows):
    total = 0
    for r in rows:
        total += r["amount"]
    return f"退款额 {total}"


def _sum_amount(rows):
    return sum(r["amount"] for r in rows)


def report_sales(rows):
    return f"销售额 {_sum_amount(rows)}"


def report_refund(rows):
    return f"退款额 {_sum_amount(rows)}"


print("\n== 重复代码 ==")
print(" ", report_sales([{"amount": 100}, {"amount": 50}]),
      "|", report_refund([{"amount": 30}]))


# ---------------- 4. 基本类型偏执 → 值对象 ----------------
class Phone:
    def __init__(self, raw: str):
        digits = "".join(ch for ch in raw if ch.isdigit())
        if len(digits) != 11 or not digits.startswith("1"):
            raise ValueError(f"非法手机号：{raw}")
        self.number = digits

    def masked(self):
        return self.number[:3] + "****" + self.number[-4:]


print("\n== 基本类型偏执 ==")
phone = Phone("138-1234-5678")
print("  规范化后：", phone.masked())
try:
    Phone("123")
except ValueError as exc:
    print("  拦截：", exc)


# ---------------- 5. 特性依恋 → 把方法移到数据旁边 ----------------
class Order:
    def __init__(self, items):
        self.items = items

    @property
    def total(self):
        return sum(p * q for _, p, q in self.items)


def print_total_bad(order):
    return f"合计 {sum(p * q for _, p, q in order.items)}"    # 老在算别人家的数据


def print_total_good(order: Order):
    return f"合计 {order.total}"                                # 用对象自己的属性


print("\n== 特性依恋 ==")
o = Order([("鼠标", 99, 2)])
print(" ", print_total_good(o))


# ---------------- 6. 深层嵌套 → 卫语句 ----------------
def classify_bad(score):
    if score is not None:
        if isinstance(score, (int, float)):
            if 0 <= score <= 100:
                if score >= 60:
                    return "及格"
                else:
                    return "不及格"
            else:
                return "分数越界"
        else:
            return "类型错误"
    else:
        return "空值"


def classify_good(score):
    if score is None:
        return "空值"
    if not isinstance(score, (int, float)):
        return "类型错误"
    if not (0 <= score <= 100):
        return "分数越界"
    return "及格" if score >= 60 else "不及格"


print("\n== 深层嵌套 ==")
for v in (90, 50, 120, None, "A"):
    print(f"  {v!r:6} → {classify_good(v)}")

# 自查清单：函数超过 50 行？同一个数字出现 3 次？复制粘贴两次以上？
#         凡事先写测试再动手。

# ===== 练习题 =====
# 1. 在 415 的 process_order_good 上再提取“计算运费”为独立策略。
# 2. 给 Phone 增加 equals/hash，使其可作 dict 键。
# 3. 找一段你写过的深层嵌套，用卫语句重写。
# 4. 思考：为什么“重复代码”比“错误抽象”危害小？（三次法则）
