# ===== 第352课：OOP进阶-综合案例-银行账户模型 =====
# 知识点：
#   - 综合运用：Enum 状态机（349）+ __slots__（346）+ property 校验（345）
#     + 特殊方法（350）
#   - 设计要点：非法状态“进不来”，而不是进了再检查
#   - 余额只能通过业务方法变更，字段本身对外只读
from enum import Enum, auto


class Status(Enum):
    ACTIVE = auto()
    FROZEN = auto()
    CLOSED = auto()


class AccountError(Exception): ...
class FrozenAccount(AccountError): ...
class InsufficientFunds(AccountError): ...
class ClosedAccount(AccountError): ...


class Account:

    __slots__ = ("_owner", "_balance", "_status")

    def __init__(self, owner, balance=0):
        if balance < 0:
            raise ValueError("开户余额不能为负")
        self._owner = owner
        self._balance = balance
        self._status = Status.ACTIVE

    @property
    def owner(self):                        # 只读：开户后不可改名
        return self._owner

    @property
    def balance(self):                      # 只读：改余额必须走业务方法
        return self._balance

    @property
    def status(self):
        return self._status

    def _ensure_active(self):
        if self._status is Status.CLOSED:
            raise ClosedAccount("账户已注销")
        if self._status is Status.FROZEN:
            raise FrozenAccount("账户已冻结")

    def deposit(self, amount):
        self._ensure_active()
        if amount <= 0:
            raise ValueError("存款必须为正数")
        self._balance += amount
        return self._balance

    def withdraw(self, amount):
        self._ensure_active()
        if amount <= 0:
            raise ValueError("取款必须为正数")
        if amount > self._balance:
            raise InsufficientFunds(f"余额 {self._balance} 不足 {amount}")
        self._balance -= amount
        return self._balance

    def freeze(self):
        self._ensure_active()
        self._status = Status.FROZEN

    def __repr__(self):
        return f"Account({self._owner!r}, {self._balance}, {self._status.name})"

    def __eq__(self, other):
        return isinstance(other, Account) and self._owner == other._owner


# ---- 使用演示 ----
a = Account("小明", 100)
b = Account("小红")

a.deposit(50)
print(a, "| 转账前 B 余额：", b.balance)

try:
    a.withdraw(999)
except InsufficientFunds as exc:
    print("拦截：", exc)

a.freeze()
try:
    a.deposit(10)
except FrozenAccount as exc:
    print("拦截：", exc)

print("等值判断：", Account("小明") == Account("小明"))

# ===== 练习题 =====
# 1. 增加 transfer_to(other, amount)：同时校验双方状态与余额。
# 2. 把“余额低于 10 冻结”做成自动规则（deposit/withdraw 后检查）。
# 3. 思考：用 frozen dataclass 能实现本模型吗？卡在哪？（余额要变 → 不宜 frozen）
