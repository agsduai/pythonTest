# ===== 第169课：面向对象高级-案例-代码实现(抽象类-ABC) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 抽象类：不能被实例化，只能被继承的类
#   - 使用 abc 模块的 ABC 作为父类
#   - @abstractmethod 声明抽象方法，子类必须全部实现
#   - 抽象类可以同时包含抽象方法和普通方法
#   - 子类未实现全部抽象方法时，实例化会抛出 TypeError


from abc import ABC, abstractmethod


class BaseMember(ABC):
    """会员抽象基类：规定所有会员都必须提供借阅上限和类型名称。"""

    def __init__(self, member_id: str, name: str, password: str) -> None:
        self.member_id = member_id
        self.name = name
        self._password = password
        self.borrowed_books: list[str] = []

    @abstractmethod
    def borrow_limit(self) -> int:
        """返回最大借书数量，子类必须实现。"""

    @abstractmethod
    def role_name(self) -> str:
        """返回会员类型名称，子类必须实现。"""

    def can_borrow(self) -> bool:
        """普通方法：基于抽象方法 borrow_limit 判断能否借书。"""
        return len(self.borrowed_books) < self.borrow_limit()


class NormalMember(BaseMember):
    """普通会员：最多借 3 本。"""

    def borrow_limit(self) -> int:
        return 3

    def role_name(self) -> str:
        return "普通会员"


class VipMember(BaseMember):
    """VIP 会员：最多借 6 本。"""

    def borrow_limit(self) -> int:
        return 6

    def role_name(self) -> str:
        return "VIP会员"


try:
    BaseMember("M000", "测试", "000000")     # 抽象类不能直接实例化
except TypeError as error:
    print("实例化抽象类失败：", error)

members = [
    NormalMember("M001", "小明", "123456"),
    VipMember("M002", "小红", "654321"),
]
for member in members:
    print(f"{member.member_id} {member.name} 类型：{member.role_name()} "
          f"上限：{member.borrow_limit()} 本 当前可借：{member.can_borrow()}")

# ===== 练习题 =====
# 1. 定义 AdminMember 继承 BaseMember，借阅上限为 10 本，
#    类型名称为“管理员”，创建对象并打印信息。
# 2. 给 BaseMember 增加抽象方法 reset_password(new_password)，
#    并在 NormalMember 和 VipMember 中实现。
# 3. 说明抽象类与普通父类的区别，以及抽象类在案例中的作用。
