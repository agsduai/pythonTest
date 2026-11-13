# ===== 第164课：面向对象高级-多态 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 多态：同一种方法调用，作用于不同对象时产生不同的行为
#   - 实现前提：继承 + 方法重写
#   - 调用者只依赖父类定义的接口，不关心对象的具体子类
#   - 新增子类时通常不需要修改调用方代码，扩展性好
#   - 多态让程序面向抽象编程，降低模块之间的耦合


class Shape:
    """父类：所有图形都应实现 area 方法。"""

    def area(self) -> float:
        raise NotImplementedError("子类必须实现 area 方法")


class Circle(Shape):
    def __init__(self, radius: float) -> None:
        self.radius = radius

    def area(self) -> float:
        return 3.14159 * self.radius ** 2


class Rectangle(Shape):
    def __init__(self, width: float, height: float) -> None:
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height


def show_area(shape: Shape) -> None:
    """只依赖 Shape 接口，具体调用哪个 area 由对象类型决定。"""
    print(f"{type(shape).__name__} 的面积：{shape.area():.2f}")


shapes = [Circle(2), Rectangle(3, 4)]
for shape in shapes:
    show_area(shape)          # 同一行代码，不同对象有不同结果


class Animal:
    def speak(self) -> str:
        raise NotImplementedError("子类必须实现 speak 方法")


class Dog(Animal):
    def speak(self) -> str:
        return "汪汪"


class Cat(Animal):
    def speak(self) -> str:
        return "喵喵"


def chorus(animals: list[Animal]) -> None:
    for animal in animals:
        print(animal.speak(), end=" ")


chorus([Dog(), Cat(), Dog()])
print()

# ===== 练习题 =====
# 1. 定义 Employee 父类，提供 work 方法；Manager 和 Developer 两个子类
#    重写 work，分别输出“开会”和“写代码”，用循环调用验证多态。
# 2. 定义 Payment 父类，Alipay 和 WeChatPay 子类重写 pay 方法，
#    编写 checkout(payment, amount) 函数完成支付。
# 3. 用自己的话说明多态的好处，以及它和继承、重写的关系。
