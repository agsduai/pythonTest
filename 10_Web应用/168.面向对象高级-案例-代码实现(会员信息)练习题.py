# ===== 第168课：面向对象高级-案例-代码实现(会员信息) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - Member 类保存会员号、姓名、密码、借阅上限和已借书籍
#   - 构造方法校验借阅上限，并初始化借阅列表
#   - borrow_book / return_book 维护会员的借阅记录
#   - can_borrow 判断是否还能继续借书
#   - 密码用 _password 保存，通过 check_password 校验，不直接暴露


class Member:
    """会员信息：管理个人资料和借阅记录。"""

    def __init__(self, member_id: str, name: str, password: str,
                 max_books: int = 3) -> None:
        if max_books <= 0:
            raise ValueError("借阅上限必须大于 0")
        self.member_id = member_id
        self.name = name
        self._password = password          # 保护属性：不对外直接展示
        self.max_books = max_books
        self.borrowed_books: list[str] = []   # 已借书籍编号

    def check_password(self, password: str) -> bool:
        """校验密码是否正确。"""
        return self._password == password

    def can_borrow(self) -> bool:
        """未达到借阅上限时可以继续借书。"""
        return len(self.borrowed_books) < self.max_books

    def borrow_book(self, book_id: str) -> bool:
        """借书：达到上限、重复借同一本时返回 False。"""
        if not self.can_borrow():
            return False
        if book_id in self.borrowed_books:
            return False
        self.borrowed_books.append(book_id)
        return True

    def return_book(self, book_id: str) -> bool:
        """还书：没有借过这本书时返回 False。"""
        if book_id not in self.borrowed_books:
            return False
        self.borrowed_books.remove(book_id)
        return True

    def __str__(self) -> str:
        books = "、".join(self.borrowed_books) if self.borrowed_books else "无"
        return (f"会员[{self.member_id}] {self.name} "
                f"已借 {len(self.borrowed_books)}/{self.max_books} 本：{books}")


members = [
    Member("M001", "小明", "123456"),
    Member("M002", "小红", "654321", max_books=6),
]

for member in members:
    print(member)

print("\n小明借 B001：", members[0].borrow_book("B001"))
print("小明重复借 B001：", members[0].borrow_book("B001"))
print("小明借 B002：", members[0].borrow_book("B002"))
print("密码校验：", members[0].check_password("123456"))
print("还能借书：", members[0].can_borrow())
print("小明还 B001：", members[0].return_book("B001"))
print(members[0])

# ===== 练习题 =====
# 1. 给 Member 增加 level（等级）属性，并在 __str__ 中显示。
# 2. 写函数 count_borrowed(members)，统计所有会员当前借出的书籍总数。
# 3. 思考：为什么密码要用 _password 保存，而不是直接写成公开属性？
