# ===== 第1063课：异常处理进阶-自定义异常类 =====
# 知识点：
#   - 自定义异常：class XxxError(Exception)，继承 Exception 即可
#   - 命名以 Error 结尾；继承自 Exception 而不是 BaseException
#   - 可在 __init__ 里带附加信息（错误码、字段名），比普通异常更"有料"
#   - 业务项目用自定义异常分类：如 OrderError / PayError，上层按类分别处理

# 案例一：最简单的自定义异常
class InsufficientBalanceError(Exception):
    """余额不足异常。"""
    pass

def withdraw(balance, amount):
    if amount > balance:
        raise InsufficientBalanceError(f"需要 {amount} 元，余额只有 {balance} 元")
    return balance - amount

try:
    withdraw(100, 500)
except InsufficientBalanceError as e:
    print(f"自定义异常捕获：{e}")

# 案例二：带附加信息的异常
# 场景：表单校验要知道"哪个字段错了"
class ValidationError(Exception):
    def __init__(self, field, message):
        self.field = field        # 出错的字段名
        self.message = message    # 给人看的说明
        super().__init__(f"[{field}] {message}")

def validate_form(data):
    if "name" not in data:
        raise ValidationError("name", "姓名不能为空")
    if not str(data.get("age", "")).isdigit():
        raise ValidationError("age", "年龄必须是数字")

try:
    validate_form({"age": "abc"})
except ValidationError as e:
    print(f"捕获：{e}")
    print(f"出错字段：{e.field}，说明：{e.message}")  # 附加信息还能单独用

# 案例三：异常体系 —— 子类可被父类 except 捕获
class OrderError(Exception):
    """订单类异常基类。"""

class EmptyOrderError(OrderError):
    """空订单。"""

class PayTimeoutError(OrderError):
    """支付超时。"""

def handle_order(kind):
    if kind == "empty":
        raise EmptyOrderError("订单里没有商品")
    if kind == "timeout":
        raise PayTimeoutError("支付 30 分钟未完成")

for kind in ["empty", "timeout"]:
    try:
        handle_order(kind)
    except OrderError as e:  # 父类可以同时接住两种子类
        print(f"订单异常（{type(e).__name__}）：{e}")

# 案例四：分开处理 —— 子类各自 except
try:
    handle_order("timeout")
except EmptyOrderError:
    print("处理空订单：清空购物车")
except PayTimeoutError:
    print("处理支付超时：释放库存")

# ===== 练习题 =====
# 1. 定义 AgeError(Exception)，写 set_age(age)：不在 1~120 抛 AgeError("年龄非法: x")，用 try 捕获。
# 2. 定义带字段的 LoginError(Exception)：__init__ 接收 (code, message)，分别实现"密码错误 (401)"与"账号冻结 (403)"两种抛出，并在 except 里读取 code。
# 3. 设计异常体系 PayError 基类 + BalanceError / CardError 子类，写函数 pay(amount, card_ok)：余额不够抛 BalanceError、卡状态异常抛 CardError，用两个 except 分别处理。
