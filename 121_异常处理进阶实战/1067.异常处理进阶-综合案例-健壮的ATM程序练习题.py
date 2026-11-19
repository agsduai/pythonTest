# ===== 第1067课：异常处理进阶-综合案例-健壮的ATM程序 =====
# 知识点：
#   - 综合运用：自定义异常 + 校验 raise + try/except + 重试循环
#   - 程序健壮性 = 任何非法输入都不崩溃，且用户知道错在哪
#   - 异常分类处理：TypeError / ValueError / 自定义业务异常各自有文案
#   - 主循环 + 每步校验，是命令行程序的标准骨架

# 案例一：定义业务异常
class AtmError(Exception):
    """ATM 业务异常基类。"""

class CardLockedError(AtmError):
    """连续输错密码，卡被锁。"""

class InsufficientFundsError(AtmError):
    """余额不足。"""

# 案例二：核心操作 —— 校验失败就抛对应异常
class Atm:
    MAX_RETRY = 3

    def __init__(self, pin, balance):
        self.pin = pin
        self.balance = balance
        self.retry = 0
        self.locked = False

    def check_pin(self, pin):
        if self.locked:
            raise CardLockedError("卡片已锁定，请联系银行")
        if pin != self.pin:
            self.retry += 1
            if self.retry >= self.MAX_RETRY:
                self.locked = True
                raise CardLockedError("连续 3 次输错，卡片被锁定")
            raise ValueError(f"密码错误，还剩 {self.MAX_RETRY - self.retry} 次机会")
        self.retry = 0  # 输对了重置次数
        print("密码正确")

    def withdraw(self, amount):
        if not isinstance(amount, (int, float)):
            raise TypeError("金额必须是数字")
        if amount <= 0:
            raise ValueError("取款金额必须为正数")
        if amount > self.balance:
            raise InsufficientFundsError(f"余额只有 {self.balance} 元")
        self.balance -= amount
        print(f"取款 {amount} 元成功，余额 {self.balance} 元")

# 案例三：带重试的密码验证（模拟三次输入）
atm = Atm("1234", 500)
attempts = ["1111", "2222", "1234"]  # 错、错、对
for pwd in attempts:
    try:
        atm.check_pin(pwd)
        break
    except (ValueError, CardLockedError) as e:
        print(f"提示：{e}")
if atm.locked:
    print("流程终止：卡片锁定")
else:
    print("进入主界面")

# 案例四：取款全流程防御（含非法输入）
def try_withdraw(atm, raw):
    try:
        amount = float(raw)  # 用户输入先转数字
    except ValueError:
        print(f"'{raw}' 不是合法金额")
        return
    try:
        atm.withdraw(amount)
    except (TypeError, ValueError, InsufficientFundsError) as e:
        print(f"取款失败：{e}")

try_withdraw(atm, "200")   # 成功
try_withdraw(atm, "abc")   # 非法金额
try_withdraw(atm, "-50")   # 负数
try_withdraw(atm, "9999")  # 余额不足
print(f"最终余额：{atm.balance} 元")

# 案例五：锁定演示
atm2 = Atm("8888", 100)
for pwd in ["1", "2", "3", "4"]:
    try:
        atm2.check_pin(pwd)
    except (ValueError, CardLockedError) as e:
        print(f"提示：{e}")
        if atm2.locked:
            break

# ===== 练习题 =====
# 1. 给 Atm 加 deposit(amount) 方法：负数/非数字分别抛 ValueError/TypeError，成功打印新余额，用 try 捕获测试三种输入。
# 2. 写函数 safe_input_amount(prompt)：模拟输入列表 ["100", "abc", "-5"] 依次处理，只有合法正数才返回，全部非法返回 None。
# 3. 综合挑战：把 Atm 改成"主循环菜单"（用预置指令列表模拟输入：查询/取款/退出），任何异常都打印提示继续循环，输入退出才结束。
