# ===== 第171课：面向对象高级-案例-代码实现(登录) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 登录流程：输入会员号和密码 -> 查找会员 -> 校验密码 -> 记录当前用户
#   - 会员号不存在和密码错误给相同提示，避免泄露账号是否存在
#   - 登录成功后把会员对象保存到 self.current_member
#   - 未登录时借书、还书等操作应被拒绝
#   - logout 清除当前登录状态


class Member:
    """会员：保存账号信息，并提供密码校验。"""

    def __init__(self, member_id: str, name: str, password: str) -> None:
        self.member_id = member_id
        self.name = name
        self._password = password

    def check_password(self, password: str) -> bool:
        return self._password == password


class Library:
    """图书管理系统：负责会员登录与登录状态管理。"""

    def __init__(self) -> None:
        self.members: dict[str, Member] = {
            "M001": Member("M001", "小明", "123456"),
            "M002": Member("M002", "小红", "654321"),
        }
        self.current_member: Member | None = None   # 当前登录用户

    def login(self, member_id: str, password: str) -> bool:
        """登录成功返回 True，并记录 current_member。"""
        member = self.members.get(member_id)
        if member is None or not member.check_password(password):
            print("登录失败：会员号或密码错误")   # 不区分具体原因
            return False
        self.current_member = member
        print(f"登录成功，欢迎 {member.name}")
        return True

    def logout(self) -> None:
        """退出登录。"""
        if self.current_member is not None:
            print(f"{self.current_member.name} 已退出登录")
        self.current_member = None

    def is_login(self) -> bool:
        return self.current_member is not None

    def require_login(self) -> bool:
        """业务操作前检查登录状态。"""
        if not self.is_login():
            print("请先登录后再操作")
            return False
        return True


library = Library()
print("初始登录状态：", library.is_login())
library.login("M001", "wrong")          # 密码错误
library.login("M999", "123456")         # 会员号不存在
library.login("M001", "123456")         # 登录成功
print("当前用户：", library.current_member.name)
print("登录状态：", library.is_login())

library.logout()
print("退出后状态：", library.is_login())
library.require_login()                 # 未登录，提示先登录

# ===== 练习题 =====
# 1. 为 login 增加失败次数统计，连续失败 3 次后提示账号已锁定。
# 2. 增加 change_password(old, new) 方法，要求已登录且旧密码正确。
# 3. 思考：为什么“会员号不存在”和“密码错误”要返回相同的提示？
