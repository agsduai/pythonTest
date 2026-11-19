# ===== 第1035课：面向对象综合实战-综合案例-图书管理 =====
# 知识点：
#   - 综合运用：类设计、封装、魔术方法、组合、异常处理
#   - 大项目拆小类：Book 管"一本书"，Library 管"一批书"
#   - 每个类职责单一，方法短小，出错好定位
#   - 状态（借出/在馆）放在对象自己身上，类只提供操作方法

# 案例一：Book 类 —— 一本书的基本信息和状态
class Book:
    def __init__(self, isbn, title, author):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.borrowed = False  # 状态：是否借出

    def __str__(self):
        status = "已借出" if self.borrowed else "在馆"
        return f"《{self.title}》{self.author} 著 [{status}]"

    def __eq__(self, other):
        return isinstance(other, Book) and self.isbn == other.isbn

# 案例二：Library 类 —— 组合多个 Book，提供借还操作
class Library:
    def __init__(self, name):
        self.name = name
        self.books = {}  # {isbn: Book}

    def add_book(self, book):
        if book.isbn in self.books:
            print(f"《{book.title}》已在馆，无需重复入库")
            return
        self.books[book.isbn] = book
        print(f"入库成功：{book}")

    def find(self, keyword):
        """按书名模糊查找"""
        return [b for b in self.books.values() if keyword in b.title]

    def borrow(self, isbn):
        book = self.books.get(isbn)
        if book is None:
            raise LookupError(f"没有编号 {isbn} 的书")
        if book.borrowed:
            raise RuntimeError(f"《{book.title}》已被借走")
        book.borrowed = True
        print(f"借出成功：{book}")

    def give_back(self, isbn):
        book = self.books.get(isbn)
        if book is None:
            raise LookupError(f"没有编号 {isbn} 的书")
        if not book.borrowed:
            raise RuntimeError(f"《{book.title}》本来就在馆")
        book.borrowed = False
        print(f"归还成功：{book}")

# 案例三：跑一遍完整流程 —— 入库、查书、借、还
lib = Library("社区图书馆")
lib.add_book(Book("B001", "Python入门", "张三"))
lib.add_book(Book("B002", "数据思维", "李四"))
lib.add_book(Book("B001", "Python入门", "张三"))  # 重复入库被拦

print(f"搜'数据'：{[str(b) for b in lib.find('数据')]}")
try:
    lib.borrow("B001")
    lib.borrow("B001")  # 再借会报"已被借走"
except (LookupError, RuntimeError) as e:
    print(f"借书失败：{e}")
try:
    lib.give_back("B001")
except (LookupError, RuntimeError) as e:
    print(f"还书失败：{e}")

# 案例四：统计与排序 —— 推导式配合对象属性
print(f"馆藏 {len(lib.books)} 种，在馆 {sum(1 for b in lib.books.values() if not b.borrowed)} 种")
on_shelf = sorted(
    (b.title for b in lib.books.values() if not b.borrowed),
)
print(f"在馆书单：{on_shelf}")

# ===== 练习题 =====
# 1. 给 Library 加 remove_book(isbn)：书被借出时抛 RuntimeError，正常则删除并打印。
# 2. 给 Book 加 __repr__ 返回 "Book(isbn, title)"；把 3 本书放进列表打印，观察使用的是 repr。
# 3. 新增 Member 类（姓名+已借列表）和 borrow_for(member, isbn) 方法：同一本书同时只能借给一人，借出后记入 member.books，用 try/except 处理所有异常情况。
