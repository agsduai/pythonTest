# ===== 第1032课：面向对象综合实战-类方法与静态方法 =====
# 知识点：
#   - 实例方法：第一个参数 self，操作具体某个对象的数据
#   - @classmethod：第一个参数 cls，操作"类本身"，常做"备选构造器"
#   - @staticmethod：不需要 self 也不需要 cls，就是放进类里的普通函数
#   - 选择标准：用到对象数据用实例方法；跟类相关用类方法；都不沾用静态方法

# 案例一：三种方法对比 —— 一眼看出区别
class Pizza:
    kind = "披萨"  # 类属性：所有对象共享

    def __init__(self, ingredients):
        self.ingredients = ingredients  # 实例属性：每个对象自己的

    def describe(self):            # 实例方法：要用 self
        return f"{Pizza.kind}：{self.ingredients}"

    @classmethod
    def margherita(cls):           # 类方法：要用 cls，当"备选构造器"
        return cls(["番茄", "芝士"])  # cls 就是 Pizza 本身

    @staticmethod
    def is_valid(ingredients):     # 静态方法：self/cls 都不需要
        return len(ingredients) > 0

p = Pizza(["火腿", "芝士"])
print(p.describe())
print(f"工厂创建：{Pizza.margherita().describe()}")
print(f"配料校验：{Pizza.is_valid(['番茄'])}")

# 案例二：类方法当备选构造器 —— 从不同来源创建对象
# 场景：日期可以"年月日"创建，也可以从字符串 "2024-01-15" 创建
class MyDate:
    def __init__(self, year, month, day):
        self.year, self.month, self.day = year, month, day

    @classmethod
    def from_string(cls, text):  # 字符串 -> 对象
        y, m, d = text.split("-")
        return cls(int(y), int(m), int(d))  # 最终还是走 __init__

    def show(self):
        print(f"{self.year} 年 {self.month} 月 {self.day} 日")

d1 = MyDate(2024, 1, 15)
d2 = MyDate.from_string("2024-03-08")  # 字符串也能建对象了
d1.show()
d2.show()

# 案例三：类方法统计实例个数 —— cls 操作类属性
class Order:
    count = 0  # 类属性：记录一共创建过多少个订单

    def __init__(self, order_id):
        self.order_id = order_id
        Order.count += 1  # 直接改类属性（类方法也行）

    @classmethod
    def total(cls):
        return cls.count

Order("A001")
Order("A002")
Order("A003")
print(f"累计订单数：{Order.total()}")

# 案例四：静态方法放工具函数 —— 逻辑上属于这个类
class FileUtils:
    @staticmethod
    def get_ext(filename):
        return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

print(f"后缀：{FileUtils.get_ext('report.PDF')}")  # pdf
print(f"无后缀：'{FileUtils.get_ext('README')}'")

# ===== 练习题 =====
# 1. 给 Temperature 类写类方法 from_fahrenheit(f)：把华氏温度转摄氏（(f-32)*5/9）后创建实例。
# 2. 设计 Counter 类：类属性 total 记录创建次数，写类方法 get_total() 返回它；创建 3 个实例后打印 3。
# 3. 把"校验手机号是否 11 位纯数字"写成静态方法，放进 User 类里，用 "13800138000" 和 "123" 测试。
