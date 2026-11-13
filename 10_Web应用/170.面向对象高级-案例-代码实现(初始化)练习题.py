# ===== 第170课：面向对象高级-案例-代码实现(初始化) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 初始化：对象创建时准备好系统运行所需的数据
#   - Library.__init__ 中创建容器，并调用 _init_books / _init_members
#   - 书籍用字典保存，key 为编号，按编号查找效率高
#   - 会员同样用字典保存，便于后续按会员号登录
#   - 初始化数据与业务逻辑分离，方便以后改成读文件或数据库


class Book:
    """简化版书籍：编号、书名、总库存、可借数量。"""

    def __init__(self, book_id: str, title: str, total: int) -> None:
        self.book_id = book_id
        self.title = title
        self.total = total
        self.available = total

    def __str__(self) -> str:
        return f"[{self.book_id}] {self.title} 可借 {self.available}/{self.total}"


class Member:
    """简化版会员：编号、姓名、密码、借阅上限。"""

    def __init__(self, member_id: str, name: str, password: str,
                 max_books: int) -> None:
        self.member_id = member_id
        self.name = name
        self._password = password
        self.max_books = max_books

    def __str__(self) -> str:
        return f"会员[{self.member_id}] {self.name} 上限 {self.max_books} 本"


class Library:
    """图书管理系统：对象创建时自动完成书籍和会员初始化。"""

    def __init__(self) -> None:
        self.books: dict[str, Book] = {}
        self.members: dict[str, Member] = {}
        self._init_books()          # 初始化书籍数据
        self._init_members()        # 初始化会员数据

    def _init_books(self) -> None:
        book_data = [
            ("B001", "Python 编程入门", 3),
            ("B002", "算法基础", 1),
            ("B003", "Web 开发实战", 2),
        ]
        for book_id, title, total in book_data:
            self.books[book_id] = Book(book_id, title, total)

    def _init_members(self) -> None:
        member_data = [
            ("M001", "小明", "123456", 3),
            ("M002", "小红", "654321", 6),
        ]
        for member_id, name, password, limit in member_data:
            self.members[member_id] = Member(member_id, name, password, limit)

    def summary(self) -> None:
        print(f"书籍 {len(self.books)} 种，会员 {len(self.members)} 人")
        for book in self.books.values():
            print(" ", book)
        for member in self.members.values():
            print(" ", member)


library = Library()                 # 创建对象即自动初始化
library.summary()
print("按编号取书：", library.books["B001"].title)
print("按编号取会员：", library.members["M001"].name)

# ===== 练习题 =====
# 1. 在 _init_members 中增加一个管理员账号（会员号 M003，上限 10 本）。
# 2. 增加 book_count 方法，返回所有书籍的总库存数量。
# 3. 思考：为什么把初始化拆成 _init_books 和 _init_members 两个方法？
