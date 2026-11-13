# ===== 第172课：面向对象高级-案例-代码实现(运行与测试) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 把书籍、会员、登录、借还书组合成完整系统
#   - Library 统一管理数据，外部只调用 login/borrow/return_book
#   - 用 assert 编写自动化测试，覆盖正常和异常场景
#   - 测试覆盖：未登录、密码错误、重复借阅、归还、退出
#   - 所有断言通过，说明核心业务逻辑正确

class Book:
    """书籍：管理库存。"""
    def __init__(self, book_id: str, title: str, total: int = 1) -> None:
        self.book_id = book_id
        self.title = title
        self.total = total
        self.available = total
    def borrow(self) -> bool:
        if self.available <= 0: return False
        self.available -= 1
        return True
    def give_back(self) -> None:
        if self.available < self.total:
            self.available += 1


class Member:
    """会员：维护借阅记录和借阅上限。"""
    def __init__(self, member_id: str, name: str, password: str,
                 limit: int = 3) -> None:
        self.member_id = member_id
        self.name = name
        self._password = password
        self.limit = limit
        self.borrowed: list[str] = []
    def check_password(self, password: str) -> bool:
        return self._password == password
    def borrow(self, book: Book) -> bool:
        if len(self.borrowed) >= self.limit: return False
        if book.book_id in self.borrowed: return False
        if not book.borrow(): return False
        self.borrowed.append(book.book_id)
        return True
    def give_back(self, book: Book) -> bool:
        if book.book_id not in self.borrowed: return False
        self.borrowed.remove(book.book_id)
        book.give_back()
        return True


class Library:
    """系统入口：组合书籍、会员和登录状态。"""
    def __init__(self) -> None:
        self.books = {"B001": Book("B001", "Python 入门", 1),
                      "B002": Book("B002", "算法基础", 1)}
        self.members = {"M001": Member("M001", "小明", "123456")}
        self.current_member: Member | None = None
    def login(self, member_id: str, password: str) -> bool:
        member = self.members.get(member_id)
        if member is None or not member.check_password(password):
            return False
        self.current_member = member
        return True
    def borrow(self, book_id: str) -> bool:
        if self.current_member is None or book_id not in self.books:
            return False
        return self.current_member.borrow(self.books[book_id])
    def return_book(self, book_id: str) -> bool:
        if self.current_member is None or book_id not in self.books:
            return False
        return self.current_member.give_back(self.books[book_id])
    def logout(self) -> None:
        self.current_member = None


def test_library() -> None:
    library = Library()
    assert library.borrow("B001") is False          # 未登录不能借
    assert library.login("M001", "wrong") is False   # 密码错误
    assert library.login("M001", "123456") is True
    assert library.borrow("B001") is True
    assert library.borrow("B001") is False           # 已借过，不能重复借
    assert library.return_book("B001") is True
    assert library.borrow("B001") is True
    library.logout()
    assert library.borrow("B001") is False           # 退出后不能借
    print("全部测试通过！")

if __name__ == "__main__":
    test_library()

# ===== 练习题 =====
# 1. 给 Library 增加一本库存为 2 的书，验证两个会员可以分别借到同一本书。
# 2. 创建 limit=1 的会员，验证借到第 2 本时返回 False。
# 3. 未借阅的书执行归还，验证 return_book 返回 False。
