# ===== 第160课：面向对象高级-封装 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 封装：把数据和对数据的操作包装在类内部，只暴露必要接口
#   - 私有属性以双下划线开头（如 __balance），类外不能直接访问
#   - 保护属性以单下划线开头（如 _owner），是约定，不建议外部直接改
#   - @property 提供受控访问，@属性名.setter 在赋值时做校验
#   - 封装的目的：保护数据安全、隐藏实现细节、方便后续维护


class BankAccount:
    """银行账户：余额私有，只能通过公开方法读写。"""

    def __init__(self, owner: str, balance: float = 0.0) -> None:
        self._owner = owner          # 保护属性
        self.__balance = balance     # 私有属性

    @property
    def balance(self) -> float:
        """只读属性：外部读取余额。"""
        return self.__balance

    @balance.setter
    def balance(self, value: float) -> None:
        """赋值时校验，防止余额变成负数。"""
        if value < 0:
            raise ValueError("余额不能为负数")
        self.__balance = value

    def deposit(self, amount: float) -> None:
        """存款：金额必须大于 0。"""
        if amount <= 0:
            raise ValueError("存款金额必须大于 0")
        self.__balance += amount

    def withdraw(self, amount: float) -> bool:
        """取款：余额不足返回 False，且不扣款。"""
        if amount <= 0:
            raise ValueError("取款金额必须大于 0")
        if amount > self.__balance:
            return False
        self.__balance -= amount
        return True

    def __str__(self) -> str:
        return f"账户[{self._owner}] 余额：{self.__balance:.2f}"


account = BankAccount("张三", 100.0)
account.deposit(50)                          # 通过方法存款
print(account)

print("取款 200：", account.withdraw(200))    # 余额不足，返回 False
print("取款 80：", account.withdraw(80))
account.balance = 500                        # 通过 setter 修改余额
print(account)

try:
    account.balance = -1                     # 触发 setter 校验
except ValueError as error:
    print("赋值失败：", error)

try:
    print(account.__balance)                 # 私有属性不能直接访问
except AttributeError as error:
    print("访问私有属性失败：", error)

# ===== 练习题 =====
# 1. 定义 Student 类，成绩私有，用 property/setter 校验 0~100。
# 2. 为 BankAccount 增加 transfer 方法，余额不足时拒绝转账。
# 3. 说明封装的好处，以及单下划线和双下划线的区别。
