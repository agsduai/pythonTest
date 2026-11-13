# ===== 第163课：面向对象高级-继承(多继承) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 多继承：一个子类可以同时继承多个父类，语法 class C(A, B)
#   - 子类拥有所有父类的属性和方法
#   - 方法同名时按 MRO（方法解析顺序）从左到右查找
#   - 类.__mro__ 可以查看方法查找顺序
#   - 多继承适合组合“能力”（Mixin），不要滥用

class Swimmer:
    """会游泳的能力。"""

    def swim(self) -> str:
        return "游泳"

class Runner:
    """会跑步的能力。"""

    def run(self) -> str:
        return "跑步"

class Duck(Swimmer, Runner):
    """鸭子同时继承游泳和跑步两个父类。"""

    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return f"鸭子 {self.name}"

duck = Duck("小黄")
print(duck, "会：", duck.swim(), "和", duck.run())
print("Duck 的 MRO：", [cls.__name__ for cls in Duck.__mro__])

class A:
    def hello(self) -> str:
        return "A.hello"

class B(A):
    pass

class C(A):
    pass

class D(B, C):
    pass

print("菱形继承调用：", D().hello())     # 按 MRO 找到 A.hello
print("D 的 MRO：", [cls.__name__ for cls in D.__mro__])

class FlyMixin:
    def move(self) -> str:
        return "飞行"

class SwimMixin:
    def move(self) -> str:
        return "游泳"

class FlyingFish(FlyMixin, SwimMixin):
    """飞鱼：两个父类都有 move，优先使用左边的 FlyMixin。"""

print("飞鱼移动方式：", FlyingFish().move())

# ===== 练习题 =====
# 1. 定义 Camera（take_photo）和 Phone（call）两个父类，再定义
#    SmartPhone 同时继承它们，创建对象并调用两个方法。
# 2. 定义 Father 和 Mother 都有 greet 方法，Child 同时继承，
#    观察 Child().greet() 调用的是哪一个，并打印 Child.__mro__。
# 3. 说明多继承中 MRO 的作用，以及为什么建议用 Mixin 组合能力。
