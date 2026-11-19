# ===== 第1034课：面向对象综合实战-组合与对象协作 =====
# 知识点：
#   - 组合：一个类的属性是另一个类的对象，表达"整体-部分"关系
#   - 组合让职责拆分：订单管流程，商品管自己，互不干扰
#   - 委托：订单对象调用商品对象的方法，替外部"转达"
#   - 组合优于继承的场景：关系是"有"而不是"是"时，一律用组合

# 案例一：订单组合商品 —— 整体包含部分
class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price

    def info(self):
        return f"{self.name}（{self.price} 元）"

class Order:
    def __init__(self, order_id):
        self.order_id = order_id
        self.products = []  # 组合：订单里装着商品对象

    def add(self, product):
        self.products.append(product)
        print(f"订单 {self.order_id} 添加 {product.info()}")

    def total(self):
        return sum(p.price for p in self.products)

    def show(self):
        detail = "、".join(p.info() for p in self.products)
        print(f"订单 {self.order_id}：{detail}，合计 {self.total()} 元")

apple = Product("苹果", 5.5)
milk = Product("牛奶", 8.0)
order = Order("A001")
order.add(apple)
order.add(milk)
order.show()

# 案例二：多层组合 —— 顾客有购物车，购物车有商品
class Cart:
    def __init__(self):
        self.items = []  # 再往下一层的组合

    def add(self, product):
        self.items.append(product)

    def total(self):
        return sum(p.price for p in self.items)

class Customer:
    def __init__(self, name):
        self.name = name
        self.cart = Cart()  # 顾客"有"购物车

    def buy(self, product):
        self.cart.add(product)
        print(f"{self.name} 把 {product.name} 放进购物车")

    def checkout(self):
        print(f"{self.name} 结账，共 {self.cart.total()} 元")

c = Customer("小王")
c.buy(apple)      # 上一课创建的 apple 对象
c.buy(milk)
c.checkout()

# 案例三：委托 —— 对外只暴露自己的方法
# 场景：餐厅菜单"委托"厨房做菜，顾客不需要认识厨房
class Kitchen:
    def cook(self, dish):
        print(f"厨房正在制作：{dish}")

class Restaurant:
    def __init__(self):
        self.kitchen = Kitchen()  # 内部零件

    def order(self, dish):
        print(f"前台接单：{dish}")
        self.kitchen.cook(dish)  # 委托给内部对象，外部看不到厨房

r = Restaurant()
r.order("宫保鸡丁")

# 案例四：组合 + 多态 —— 部件可以替换
class SmsAlert:
    def send(self, msg):
        print(f"[短信] {msg}")

class EmailAlert:
    def send(self, msg):
        print(f"[邮件] {msg}")

class AlarmSystem:
    def __init__(self, alert):  # 报警方式可以随时替换
        self.alert = alert

    def trigger(self, msg):
        self.alert.send(msg)

alarm = AlarmSystem(SmsAlert())
alarm.trigger("仓库温度过高")
alarm.alert = EmailAlert()  # 换个部件，系统代码一行不改
alarm.trigger("仓库温度过高")

# ===== 练习题 =====
# 1. 设计 Engine（马力）和 Car 类，Car 组合 Engine；Car 的 start() 委托 engine 的 start() 并追加"车辆就绪"。
# 2. 设计 Teacher 和 Course 类：Course 组合一个 teacher 对象和课程名，Course.info() 输出 "课程名 - 授课教师"。
# 3. 设计 Team 组合多个 Player（有名字和得分），Team 的 best() 返回得分最高的队员，top3() 返回前三名。
