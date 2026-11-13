# ===== 第256课：设计模式-概述与设计原则 =====
# 知识点：
#   - 设计模式：前人总结的“面向对象套路”，解决反复出现的结构问题
#   - 三大类：创建型（怎么造对象）、结构型（怎么组装）、行为型（怎么交互）
#   - 两大原则先行：单一职责、开闭原则（对扩展开放，对修改关闭）
#   - Python 特点：函数、鸭子类型就能实现很多模式，不必照搬 Java 类图
#   - 学习方法：先记“问题场景”，再记解法，不要死背 UML

# ---- 单一职责：一个类只负责一件事 ----

# 反例：上帝类什么都干，改任何功能都要动它
# class GodWorker:
#     def read_data(self): ...
#     def clean_data(self): ...
#     def save_report(self): ...
#     def send_email(self): ...

# 正例：职责拆开，各自独立演进
class DataReader:
    def read(self):
        return ["原始数据A", "原始数据B"]


class ReportSaver:
    def save(self, rows):
        return f"已保存 {len(rows)} 行"


# ---- 开闭原则：新增功能不改旧代码 ----
from abc import ABC, abstractmethod


class Shape(ABC):

    @abstractmethod
    def area(self): ...


class Circle(Shape):

    def __init__(self, r):
        self.r = r

    def area(self):
        return 3.14159 * self.r ** 2


class Rectangle(Shape):

    def __init__(self, w, h):
        self.w, self.h = w, h

    def area(self):
        return self.w * self.h


def total_area(shapes):
    """只依赖抽象 Shape，不关心具体形状。"""
    return sum(s.area() for s in shapes)


shapes = [Circle(1), Rectangle(2, 3)]
print(round(total_area(shapes), 2))


# 后来新增三角形：total_area 一行都不用改 —— 这就是开闭原则
class Triangle(Shape):

    def __init__(self, base, height):
        self.base, self.height = base, height

    def area(self):
        return self.base * self.height / 2


shapes.append(Triangle(4, 5))
print(round(total_area(shapes), 2))

# 本路线图：257单例 258工厂 259策略 260观察者 261模板方法 262适配器 263综合

# ===== 练习题 =====
# 1. 找出你写过的“上帝类”，按单一职责拆成 2~3 个类。
# 2. 给 Shape 再加一个 Oval（椭圆），验证 total_area 依然不用改。
# 3. 思考：为什么“对修改关闭”能减少引入新 bug 的概率？
