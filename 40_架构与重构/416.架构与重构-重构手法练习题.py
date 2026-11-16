# ===== 第416课：架构与重构-重构手法 =====
# 知识点：
#   - 重构前提：有测试保护（第411课），小步提交，每步可运行
#   - 六个常用手法：提取方法、重命名、引入参数对象、卫语句、
#     用多态/表驱动替换条件分支、拆分布尔参数
#   - 重构不改外部行为：用“前后结果一致”断言来证明
#   - 与第415课的区别：那课找问题，这课练动作
from dataclasses import dataclass


# ---------------- 1. 提取方法 + 重命名 ----------------
def calc(a, b):
    return a * b * 0.05


def calculate_monthly_interest(principal: float, annual_rate: float) -> float:
    """本金 × 年利率 × 1/12。"""
    return principal * annual_rate / 12


print("== 提取方法 + 重命名 ==")
print("  10000 元按 5% 年利率，月利息：", round(calculate_monthly_interest(10000, 0.05), 2))
print("  与旧函数等价：", calc(10000, 0.05) == calculate_monthly_interest(10000, 0.05))


# ---------------- 2. 引入参数对象 ----------------
@dataclass
class Email:
    to: str
    subject: str
    body: str


def send_email_bad(to, subject, body):
    return f"→{to} 主题:{subject} 正文:{body}"


def send_email_good(email: Email):
    return f"→{email.to} 主题:{email.subject} 正文:{email.body}"


print("\n== 参数对象 ==")
msg = Email("a@example.com", "周报", "本周完成……")
print(" ", send_email_good(msg))


# ---------------- 3. 卫语句：减少嵌套 ----------------
def get_discount_bad(user):
    if user is not None:
        if user.get("active"):
            if user.get("vip"):
                return 0.8
            else:
                return 0.95
    return 1.0


def get_discount_good(user):
    if user is None or not user.get("active"):
        return 1.0
    return 0.8 if user.get("vip") else 0.95


print("\n== 卫语句 ==")
for u in (None, {"active": False}, {"active": True}, {"active": True, "vip": True}):
    assert get_discount_bad(u) == get_discount_good(u)
print("  四个用例前后结果一致")


# ---------------- 4. 条件分支 → 表驱动 ----------------
def shipping_fee_bad(country):
    if country == "CN":
        return 10
    elif country == "US":
        return 25
    elif country == "JP":
        return 18
    else:
        return 50


SHIPPING_FEES = {"CN": 10, "US": 25, "JP": 18}
DEFAULT_FEE = 50


def shipping_fee_good(country):
    return SHIPPING_FEES.get(country, DEFAULT_FEE)


print("\n== 表驱动 ==")
print("  ", {c: shipping_fee_good(c) for c in ("CN", "US", "JP", "DE")})


# ---------------- 5. 条件分支 → 多态（策略） ----------------
class TaxPolicy:
    def tax(self, amount):
        raise NotImplementedError


class NoTax(TaxPolicy):
    def tax(self, amount):
        return 0


class VatPolicy(TaxPolicy):
    def __init__(self, rate):
        self.rate = rate

    def tax(self, amount):
        return amount * self.rate


def total_with_tax(amount, policy: TaxPolicy):
    return amount + policy.tax(amount)


print("\n== 多态替换条件 ==")
print("  无税：", total_with_tax(100, NoTax()))
print("  增值税 13%：", total_with_tax(100, VatPolicy(0.13)))


# ---------------- 6. 拆分布尔参数 ----------------
def render_bad(data, raw=False):
    return str(data) if raw else f"<p>{data}</p>"


def render_html(data):
    return f"<p>{data}</p>"


def render_raw(data):
    return str(data)


print("\n== 拆分布尔参数 ==")
print(" ", render_html("你好"), "|", render_raw("你好"))
print("  调用方一眼看懂意图，不再靠 True/False 记忆")

# 重构节奏：
#   1) 先写 characterization test（记录当前行为）
#   2) 每次只做一种手法
#   3) 跑测试，绿了再继续
#   4) 行为变了就是 bug，不是“顺手优化”

# ===== 练习题 =====
# 1. 把 VatPolicy 改成可配置的税率表，替换 if/elif。
# 2. 用参数对象重构一个“5 个以上参数”的函数。
# 3. 给本课每个重构手法各找一段旧课代码练一遍。
# 4. 思考：重构与“重写”的边界在哪里？
