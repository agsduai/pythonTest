# ===== 第1062课：异常处理进阶-raise主动抛出异常 =====
# 知识点：
#   - raise 异常类("信息")：主动抛错，把"不合法的业务情况"上报给调用方
#   - 常用类型：ValueError（值不对）、TypeError（类型不对）、RuntimeError（状态不对）
#   - raise 后函数立即中断，调用方用 try 接住
#   - "让错误尽早暴露"：入口校验不合格就 raise，比返回 None 更明确

# 案例一：参数校验 —— 不合法直接抛
def set_volume(level):
    if not isinstance(level, int):
        raise TypeError(f"音量必须是整数，收到 {type(level).__name__}")
    if not 0 <= level <= 100:
        raise ValueError(f"音量必须在 0~100，收到 {level}")
    print(f"音量已设为 {level}")

set_volume(50)
try:
    set_volume(150)
except ValueError as e:
    print(f"拦截：{e}")
try:
    set_volume("80")
except TypeError as e:
    print(f"拦截：{e}")

# 案例二：业务规则异常
# 场景：账户余额不足属于业务错误
class Account:
    def __init__(self, balance):
        self.balance = balance

    def withdraw(self, amount):
        if amount > self.balance:
            raise RuntimeError(f"余额不足：需要 {amount}，只有 {self.balance}")
        self.balance -= amount
        print(f"取出 {amount}，剩余 {self.balance}")

acc = Account(100)
acc.withdraw(30)
try:
    acc.withdraw(500)
except RuntimeError as e:
    print(f"银行拒绝：{e}")

# 案例三：raise 的"快速失败"价值
# 对比两种设计：返回错误码 vs 抛异常
def parse_age_bad(text):
    if text.isdigit():  # text 为 None 会直接崩，因为 None 没有 isdigit
        return int(text)
    return -1  # -1 是合法值吗？调用方容易误用

def parse_age_good(text):
    if text is None or not text.isdigit():
        raise ValueError(f"非法年龄输入：{text!r}")
    return int(text)

try:
    parse_age_good(None)
except ValueError as e:
    print(f"快速失败：{e}")

# 案例四：raise 重新抛出 —— 记录后不吞掉
# except 里只写 raise 会原样再抛，让上层继续处理
def middle_layer():
    try:
        risky = 1 / 0
        return risky
    except ZeroDivisionError:
        print("中间层：记录日志，然后继续向上抛")
        raise  # 重新抛出同一个异常

try:
    middle_layer()
except ZeroDivisionError:
    print("最上层：最终处理")

# ===== 练习题 =====
# 1. 写函数 check_username(name)：长度 <3 抛 ValueError("用户名太短")，含空格抛 ValueError("不能含空格")，合法打印"通过"；测三种输入。
# 2. 写函数 divide(a, b)：b 为 0 时 raise ZeroDivisionError("除数不能为 0")，调用方 try 捕获打印友好提示。
# 3. 三层结构练习：底层 raise ValueError -> 中间层 except 后打印再 raise -> 最上层 except 打印"最终处理"，验证三层的执行顺序。
