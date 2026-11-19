# ===== 第1036课：代码风格与最佳实践-PEP8命名规范 =====
# 知识点：
#   - 变量/函数用 snake_case（小写加下划线）：total_price、get_name
#   - 类名用 PascalCase（首字母大写）：BankAccount、OrderItem
#   - 常量全大写：MAX_RETRY、DEFAULT_PORT
#   - 名字要"见名知义"：宁可长一点，也不要 a、x、tmp

# 案例一：烂命名 vs 好命名 对比
# 烂命名：三个月后自己都看不懂
d = {"a": 1, "b": 2}
def f1(x):
    return x * 0.8

# 好命名：读代码就像读句子
prices = {"苹果": 5.5, "牛奶": 8.0}
def get_vip_price(price):
    return price * 0.8

print(f"VIP 价：{get_vip_price(100)} 元")

# 案例二： snake_case 与 PascalCase 实战
class ShoppingCart:  # 类名 PascalCase
    MAX_ITEMS = 50   # 常量全大写

    def __init__(self):
        self.item_count = 0  # 变量 snake_case
        self._owner_name = ""  # 内部属性：单下划线开头

    def add_item(self):  # 方法 snake_case
        if self.item_count >= self.MAX_ITEMS:
            print("购物车已满")
            return
        self.item_count += 1

cart = ShoppingCart()
cart.add_item()
print(f"商品数：{cart.item_count}，上限 {ShoppingCart.MAX_ITEMS}")

# 案例三：布尔变量命名 —— is_ / has_ 开头
# 场景：布尔变量名要能直接读成"是不是/有没有"
is_vip = True
has_coupon = False
is_paid = True
if is_vip and not has_coupon:
    print("VIP 无券，给 95 折")
if is_paid and has_coupon is False:
    print("已支付且未使用优惠券")

# 案例四：避免与内置函数/关键字撞名
# 烂：list = [1, 2]  -> 之后再 list() 会报错
# 烂：str = "abc"    -> 同理
# 好：加复数或换词
number_list = [1, 2, 3]
text_value = "abc"
print(f"{number_list} / {text_value}")
# 想知道某个名字是不是内置函数：没报错定义后 dir(__builtins__) 里查
print("list" in dir(__builtins__) and "list 是内置名，别拿它当变量名")

# ===== 练习题 =====
# 1. 把烂命名 a、b、c1、func1 的变量重命名成符合 PEP8 的名字（商品数量、单价、总价、计算折后价函数），重写一遍代码。
# 2. 设计 OrderItem 类（PascalCase），属性 product_name / unit_price / quantity（snake_case），常量 MAX_QUANTITY = 99，实现 add(count) 校验。
# 3. 有布尔变量：是否登录、是否管理员、有未读消息，分别按 is_/has_ 规范命名，并写一个组合判断的 if。
