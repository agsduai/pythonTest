# ===== 第167课：面向对象高级-案例-代码实现(书籍信息) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - Book 类封装书籍编号、书名、作者、总库存和可借数量
#   - 构造方法中同时初始化 total 和 available
#   - borrow_one / return_one 维护库存，库存不能为负
#   - @property 提供“是否可借”的只读查询
#   - __str__ 让书籍信息可以直接打印


class Book:
    """书籍信息：管理总库存和当前可借数量。"""

    def __init__(self, book_id: str, title: str, author: str, total: int) -> None:
        if total < 0:
            raise ValueError("库存不能为负数")
        self.book_id = book_id
        self.title = title
        self.author = author
        self.total = total           # 总库存
        self.available = total       # 当前可借数量

    @property
    def is_available(self) -> bool:
        """还有库存时为 True。"""
        return self.available > 0

    def borrow_one(self) -> bool:
        """借出一本：成功返回 True，无库存返回 False。"""
        if not self.is_available:
            return False
        self.available -= 1
        return True

    def return_one(self) -> bool:
        """归还一本：已满或数据异常时返回 False。"""
        if self.available >= self.total:
            return False
        self.available += 1
        return True

    def __str__(self) -> str:
        return (f"[{self.book_id}] 《{self.title}》 作者：{self.author} "
                f"可借：{self.available}/{self.total}")


books = [
    Book("B001", "Python 编程入门", "张三", 3),
    Book("B002", "算法基础", "李四", 1),
    Book("B003", "Web 开发实战", "王五", 2),
]

for book in books:
    print(book)

print("\n借出 B002：", books[1].borrow_one())    # 库存 1 -> 0
print("再次借出 B002：", books[1].borrow_one())  # 无库存，失败
print("归还 B002：", books[1].return_one())
print(books[1])

print("B001 是否可借：", books[0].is_available)

# ===== 练习题 =====
# 1. 给 Book 增加 category（分类）和 price（价格）属性，并更新 __str__。
# 2. 写函数 find_books(books, keyword)，按书名关键字模糊查找并返回列表。
# 3. 思考：如果 total 为 0，borrow_one 和 return_one 应分别返回什么？
