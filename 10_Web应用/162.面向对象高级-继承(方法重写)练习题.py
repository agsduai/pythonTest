# ===== 第162课：面向对象高级-继承(方法重写) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 方法重写：子类定义与父类同名的方法，调用时优先使用子类版本
#   - 重写后仍可以用 super().方法名() 调用父类的原实现
#   - __str__ 等魔法方法同样可以被重写
#   - 重写让子类在继承的基础上定制自己的行为


class Animal:
    """父类：定义动物的通用行为。"""

    def __init__(self, name: str) -> None:
        self.name = name

    def speak(self) -> str:
        return f"{self.name} 发出叫声"

    def info(self) -> str:
        return f"动物：{self.name}"


class Dog(Animal):
    """子类：重写 speak 和 info。"""

    def speak(self) -> str:
        return f"{self.name} 汪汪叫"        # 完全替换父类实现

    def info(self) -> str:
        return super().info() + "（狗）"     # 先调用父类，再追加内容


class Cat(Animal):
    """子类：重写 speak。"""

    def speak(self) -> str:
        return f"{self.name} 喵喵叫"


animals = [Dog("旺财"), Cat("咪咪"), Animal("未知动物")]
for animal in animals:
    print(animal.info(), "->", animal.speak())   # 同一调用，不同表现

print("\n父类方法仍然可用：", Animal.speak(Dog("小黑")))

# ===== 练习题 =====
# 1. 定义 Shape 父类，提供 area 方法返回 0；再定义 Circle 和 Rectangle
#    子类，重写 area 方法分别计算圆和矩形面积。
# 2. 在 Rectangle 中重写 __str__，输出“矩形 宽x高”。
# 3. 子类重写方法后，如何调用父类被重写的版本？写代码验证。
