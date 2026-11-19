# ===== 第1028课：面向对象综合实战-类的设计思路 =====
# 知识点：
#   - 设计类的三步：找名词（属性）-> 找动词（方法）-> 定规则（校验）
#   - __init__ 里只做"存参数 + 初始化默认值"，别写复杂逻辑
#   - self 指当前对象自己，方法里访问属性都通过 self.xxx
#   - 属性是"状态"，方法是"行为"，好的类 = 状态 + 改变状态的行为

# 案例一：从需求设计"银行账户"类
# 需求：有户名和余额；能存钱、取钱、查余额；余额不能为负
class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner          # 名词 -> 属性
        self.balance = balance      # 名词 -> 属性

    def deposit(self, amount):      # 动词 -> 方法
        if amount <= 0:
            print("存款金额必须为正")   # 规则 -> 校验
            return
        self.balance += amount
        print(f"{self.owner} 存入 {amount} 元，余额 {self.balance}")

    def withdraw(self, amount):
        if amount <= 0:
            print("取款金额必须为正")
            return
        if amount > self.balance:
            print(f"余额不足，当前只有 {self.balance} 元")
            return
        self.balance -= amount
        print(f"{self.owner} 取出 {amount} 元，余额 {self.balance}")

acc = BankAccount("小张", 100)
acc.deposit(50)     # 存入 50 元，余额 150
acc.withdraw(200)   # 余额不足
acc.withdraw(80)    # 取出 80 元，余额 70

# 案例二：从需求设计"购物车"类
# 需求：能加商品（名称+数量）、能改数量、能算总价
class Cart:
    def __init__(self):
        self.items = {}  # 结构：{商品名: 数量}，初始为空

    def add(self, name, count=1):
        self.items[name] = self.items.get(name, 0) + count
        print(f"已加入 {name} x{count}")

    def remove(self, name):
        if name in self.items:
            del self.items[name]
            print(f"已移除 {name}")
        else:
            print(f"{name} 不在购物车里")

    def total(self, price_map):
        t = sum(count * price_map.get(name, 0) for name, count in self.items.items())
        print(f"购物车共 {len(self.items)} 种商品，总价 {t} 元")
        return t

cart = Cart()
cart.add("苹果", 3)
cart.add("牛奶", 2)
cart.add("苹果", 1)  # 数量自动累加成 4
cart.total({"苹果": 5.5, "牛奶": 8.0})

# 案例三：设计前的"名词动词分析表"
# 需求句子："会员用积分兑换优惠券，兑换后积分减少"
#   名词：会员(类)、积分(属性)、优惠券(属性)
#   动词：兑换(方法)、减少(在方法内部改属性)
class Member:
    def __init__(self, name, points):
        self.name = name
        self.points = points
        self.coupons = []

    def exchange(self, cost, coupon_name):
        if self.points < cost:
            print(f"{self.name} 积分不足（{self.points} < {cost}）")
            return
        self.points -= cost
        self.coupons.append(coupon_name)
        print(f"兑换成功，剩余积分 {self.points}，优惠券 {self.coupons}")

m = Member("小李", 500)
m.exchange(200, "满100减20")
m.exchange(600, "满200减50")  # 积分不足

# ===== 练习题 =====
# 1. 设计 Student 类：属性 name、scores（列表）；方法 add_score(s)（0~100 校验）和 average()（返回平均分）。
# 2. 设计 Rectangle 类：属性 width、height；方法 area() 和 perimeter()，创建 3x5 的实例验证面积 15、周长 16。
# 3. 按"名词动词法"分析需求"用户发布评论，评论有内容，用户能查看自己所有评论"，先写注释列出属性和方法，再实现 User 类。
