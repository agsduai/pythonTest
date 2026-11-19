# ===== 第1030课：面向对象综合实战-继承与代码复用 =====
# 知识点：
#   - class 子类(父类)：子类自动拥有父类的属性和方法
#   - 子类可以"重写"父类方法：同名方法直接覆盖
#   - super().__init__()：先跑父类初始化，再补充子类自己的
#   - 继承表达"is-a"关系：外卖骑手"是"员工，所以员工是父类

# 案例一：基本继承 —— 子类白得父类的方法
class Animal:
    def __init__(self, name):
        self.name = name

    def eat(self):
        print(f"{self.name} 在吃东西")

class Dog(Animal):
    def bark(self):  # 子类自己的新方法
        print(f"{self.name}：汪汪！")

d = Dog("旺财")
d.eat()   # 父类的方法直接能用
d.bark()  # 子类的方法

# 案例二：super().__init__ —— 子类补充自己的属性
# 场景：外卖骑手也是员工，额外有"配送单数"
class Employee:
    def __init__(self, name, salary):
        self.name = name
        self.salary = salary

    def show(self):
        print(f"员工 {self.name}，月薪 {self.salary}")

class Rider(Employee):
    def __init__(self, name, salary, orders_done):
        super().__init__(name, salary)  # 先让父类把 name/salary 存好
        self.orders_done = orders_done  # 再存自己特有的

    def show(self):  # 重写：在父类基础上补充内容
        super().show()  # 复用父类的打印
        print(f"  今天已配送 {self.orders_done} 单")

r = Rider("小王", 6000, 32)
r.show()

# 案例三：重写与多级继承 —— 祖孙三代
class Vehicle:  # 交通工具
    def move(self):
        print("交通工具在移动")

class Car(Vehicle):
    def move(self):
        print("汽车在公路上跑")

class ElectricCar(Car):  # 电动车继承汽车
    def move(self):
        print(f"电动车静音行驶")
        super().move()  # 还可以调父类版本

e = ElectricCar()
e.move()

# 案例四：继承 vs 组合的选择
# 场景：汽车"有"发动机（has-a 用组合），汽车"是"交通工具（is-a 用继承）
class Engine:
    def start(self):
        print("发动机启动")

class ModernCar(Vehicle):
    def __init__(self):
        self.engine = Engine()  # 组合：把对象装进来当属性

    def start(self):
        self.engine.start()
        print("车辆就绪")

c = ModernCar()
c.start()
print("口诀：是就用继承，有就用组合")

# ===== 练习题 =====
# 1. 父类 Shape 有 describe() 打印"我是一个图形"；子类 Circle 增加属性 radius 并重写 describe 打印半径。
# 2. 父类 Employee 有 name/salary 和 show()；子类 Manager 额外有 team_size，重写 show() 用 super() 复用父类打印并追加团队人数。
# 3. 设计三级继承：Device -> Phone -> SmartPhone，每级都有自己的属性和方法，SmartPhone 里用 super() 调用 Phone 的方法。
