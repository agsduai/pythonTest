# ===== 第348课：OOP进阶-描述符 =====
# 知识点：
#   - 描述符：实现 __get__ / __set__ 的类，接管“别的类的属性”读写
#   - @property 就是描述符的语法糖 —— 本课揭开它的底层
#   - 杀伤力：一个描述符类定义一次，N 个字段复用（property 要每个写一遍）
#   - __set_name__：自动拿到属性名，不用手工传
class Positive:
    """可复用的“正数校验”描述符。"""

    def __set_name__(self, owner, name):
        self.private_name = "_" + name      # 真实数据存 _price / _quantity

    def __get__(self, instance, owner):
        if instance is None:                # 通过类访问时返回描述符自身
            return self
        return getattr(instance, self.private_name)

    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError(f"{self.private_name[1:]} 必须为正数，收到 {value}")
        setattr(instance, self.private_name, value)


class Order:
    price = Positive()                      # 同一个描述符类，两个字段
    quantity = Positive()

    def __init__(self, price, quantity):
        self.price = price                  # 赋值即触发 __set__ 校验
        self.quantity = quantity


o = Order(9.9, 3)
print("单价：", o.price, "| 数量：", o.quantity, "| 总价：", round(o.price * o.quantity, 2))

o.quantity = 5                             # 合法修改
print("改数量后总价：", round(o.price * o.quantity, 2))

try:
    o.price = -1
except ValueError as exc:
    print("校验拦截：", exc)

# property vs 描述符：
#   property —— 一个字段一套逻辑，够用但不复用
#   描述符 —— 校验/缓存/类型转换等“横切逻辑”一次定义、多处挂载

# ===== 练习题 =====
# 1. 写一个 String 描述符：非 str 赋值报 TypeError，长度超上限报 ValueError。
# 2. 把第210课 StudentDB 的字段校验改成描述符版。
# 3. 思考：ORM 框架的 Column 字段，本质上是不是描述符？
