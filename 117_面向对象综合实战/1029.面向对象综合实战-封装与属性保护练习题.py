# ===== 第1029课：面向对象综合实战-封装与属性保护 =====
# 知识点：
#   - 单下划线 _name：约定"内部使用"，外部别碰（不强制）
#   - 双下划线 __name：名称改写，外部访问 self.__name 会变成 _类名__name
#   - property 装饰器：把方法伪装成属性，读和写分别控制
#   - 封装的本质：数据藏在里面，只能通过公开方法按规矩修改

# 案例一：不封装的隐患 —— 外部随便改
class BadAccount:
    def __init__(self, owner, balance):
        self.owner = owner
        self.balance = balance

bad = BadAccount("小张", 100)
bad.balance = -9999  # 外部直接改，余额变成负的，没有任何拦截
print(f"不封装的后果：{bad.owner} 余额 {bad.balance}")

# 案例二：_单下划线 + 公开方法 —— 按约定保护
class Account:
    def __init__(self, owner, balance):
        self.owner = owner
        self._balance = balance  # 约定：_ 开头表示内部属性

    def deposit(self, amount):
        if amount > 0:
            self._balance += amount

    def get_balance(self):
        return self._balance

acc = Account("小李", 100)
acc.deposit(50)
print(f"{acc.owner} 余额：{acc.get_balance()} 元")
# acc._balance 也能访问，但团队约定"别这么干"

# 案例三：__双下划线 —— 真正拦截外部访问
class SafeAccount:
    def __init__(self, owner, balance):
        self.__balance = balance  # 双下划线会被改写成 _SafeAccount__balance

    def get_balance(self):
        return self.__balance

safe = SafeAccount("小王", 100)
print(f"余额：{safe.get_balance()} 元")
try:
    print(safe.__balance)  # 外部直接访问会报 AttributeError
except AttributeError:
    print("外部无法访问 __balance，被名称改写拦住了")

# 案例四：property —— 读写都走方法，用起来却像属性
class Temperature:
    def __init__(self):
        self._celsius = 0

    @property
    def celsius(self):  # 读：obj.celsius 像属性一样用
        return self._celsius

    @celsius.setter
    def celsius(self, value):  # 写：obj.celsius = x 自动进入这里
        if value < -273.15:
            print("温度不能低于绝对零度，拒绝设置")
            return
        self._celsius = value

t = Temperature()
t.celsius = 25  # 看似直接赋值，实际走了 setter 校验
print(f"当前温度：{t.celsius} 度")
t.celsius = -300  # 非法值被拦截
print(f"尝试设为 -300 后仍是：{t.celsius} 度")

# ===== 练习题 =====
# 1. 设计 PasswordManager 类：__password 为私有属性；set_password(old, new) 验证旧密码后才能改；check_password(pwd) 返回 True/False。
# 2. 设计 Product 类：price 用 property 管理，setter 校验"价格必须 >= 0"，非法赋值打印提示且不生效。
# 3. 给 Account 类（案例二）加 _balance 的只读保护：只提供 get_balance 方法，不提供任何修改入口，验证存款只能通过 deposit。
