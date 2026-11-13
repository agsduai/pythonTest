# ===== 第080课：核心语法-面向对象基础-魔法方法 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 魔法方法是以双下划线开头和结尾的方法，由 Python 自动调用
#   - __init__：创建对象时初始化属性
#   - __str__：print 对象或 str() 时返回给用户看的字符串
#   - __len__：len(对象) 时调用
#   - __eq__：两个对象用 == 比较时调用
#   - __add__：两个对象用 + 运算时调用

class Book:
    """图书类：演示常用魔法方法。"""

    def __init__(self, title: str, price: float, pages: int) -> None:
        self.title = title
        self.price = price
        self.pages = pages

    def __str__(self) -> str:
        """print(对象) 时显示的内容。"""
        return f"《{self.title}》 价格：{self.price} 元"

    def __len__(self) -> int:
        """len(对象) 返回页数。"""
        return self.pages

    def __eq__(self, other: object) -> bool:
        """书名和价格都相同就视为同一本书。"""
        if not isinstance(other, Book):
            return False
        return self.title == other.title and self.price == other.price

    def __add__(self, other: "Book") -> float:
        """两本书相加，返回价格之和。"""
        return self.price + other.price

book1 = Book("Python 入门", 59.9, 320)
book2 = Book("算法基础", 79.0, 450)
book3 = Book("Python 入门", 59.9, 320)

print(book1)                  # 自动调用 __str__
print("页数：", len(book1))    # 自动调用 __len__
print("是否同一本：", book1 == book3)
print("价格合计：", book1 + book2)

# __repr__ 主要给开发者调试看，未定义时默认显示对象地址
print(repr(book1))

# ===== 练习题 =====
# 1. 定义 Student 类，实现 __str__ 返回“姓名-成绩”。
# 2. 实现 __len__ 返回选修课程数量，实现 __eq__ 按学号比较。
# 3. 实现 __add__，让两个学生的成绩相加并返回总分。
