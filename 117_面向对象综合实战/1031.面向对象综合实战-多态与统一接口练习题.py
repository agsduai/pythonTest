# ===== 第1031课：面向对象综合实战-多态与统一接口 =====
# 知识点：
#   - 多态：不同类的对象调用"同名方法"，各自执行自己的版本
#   - 好处：调用方不用管对象具体是什么类，统一调用同个方法名
#   - 鸭子类型：不看是不是继承关系，"有这个方法"就能用
#   - 配合循环遍历对象列表，是写扩展性好代码的关键

# 案例一：同名的 pay 方法 —— 不同支付方式各干各的
# 场景：收银台只管调 pay()，不关心用户用什么支付
class Alipay:
    def pay(self, amount):
        print(f"支付宝支付 {amount} 元")

class WechatPay:
    def pay(self, amount):
        print(f"微信支付 {amount} 元")

class BankCard:
    def pay(self, amount):
        print(f"银行卡支付 {amount} 元")

def checkout(payment, amount):
    payment.pay(amount)  # 调用方只认 pay 这个接口

for p in [Alipay(), WechatPay(), BankCard()]:
    checkout(p, 99)  # 同一行代码，三种输出

# 案例二：形状都算面积 —— 循环里统一处理
# 场景：统计画布上所有图形的总面积
import math

class Circle:
    def __init__(self, r):
        self.r = r
    def area(self):
        return math.pi * self.r ** 2

class Square:
    def __init__(self, side):
        self.side = side
    def area(self):
        return self.side ** 2

shapes = [Circle(2), Square(3), Circle(1)]
total = sum(s.area() for s in shapes)  # 都会 area()，直接求和
print(f"总面积：{total:.2f}")

# 案例三：鸭子类型 —— 不需要继承关系
# 场景：新增一种"免费支付"，只要它有 pay 方法就能进收银台
class FreePass:
    def pay(self, amount):
        print(f"免费券抵扣 {amount} 元")

checkout(FreePass(), 99)  # 没继承任何父类，照样能用

# 案例四：配合 sorted 的 key —— 按统一接口排序
# 场景：按面积从小到大排列图形
by_area = sorted(shapes, key=lambda s: s.area())
for s in by_area:
    print(f"{type(s).__name__} 面积 {s.area():.2f}")

# ===== 练习题 =====
# 1. 设计 Dog 和 Cat 两个类，都有 speak() 方法（输出"汪"和"喵"），写循环让每个动物 speak 一次。
# 2. 设计 Rectangle 和 Triangle，都有 area()；把它们放进列表算总面积。
# 3. 写函数 notify(channel, msg)：channel 对象只要有 send(msg) 方法就调用它；实现 SmsChannel 和 EmailChannel 并测试统一调用。
