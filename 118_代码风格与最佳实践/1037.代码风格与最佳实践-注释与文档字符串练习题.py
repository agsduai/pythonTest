# ===== 第1037课：代码风格与最佳实践-注释与文档字符串 =====
# 知识点：
#   - 注释解释"为什么这么写"，不是重复"代码在干什么"
#   - 文档字符串（docstring）：函数/类下第一行的三引号说明
#   - docstring 三要素：功能一句话、参数说明、返回值说明
#   - help(函数) 读的就是 docstring，所以写它等于自带说明书

# 案例一：坏注释 vs 好注释
# 坏注释：把代码翻译一遍，没有信息量
price = 100
price = price * 0.8  # price 乘 0.8  <- 废话

# 好注释：解释业务原因
price = 100
price = price * 0.8  # 运营要求：新品期统一打 8 折（2024-01 运营部通知）
print(f"折后价：{price}")

# 案例二：函数 docstring 标准写法
def calc_shipment(weight_kg, is_express=False):
    """计算快递运费。

    参数:
        weight_kg (float): 包裹重量（公斤），须大于 0
        is_express (bool): 是否特快，特快加收 10 元

    返回:
        float: 运费金额
    """
    if weight_kg <= 0:
        raise ValueError("重量必须大于 0")
    fee = 8 + (weight_kg - 1) * 2 if weight_kg > 1 else 8
    return fee + 10 if is_express else fee

print(f"普通 3kg：{calc_shipment(3)} 元")
print(f"特快 3kg：{calc_shipment(3, True)} 元")
print(f"查看说明书：")
help(calc_shipment)  # 打印的就是上面的 docstring

# 案例三：类 docstring 与属性说明
class Wallet:
    """电子钱包。

    管理余额的存取，负数操作会被拒绝。
    """
    def __init__(self, owner, balance=0):
        self.owner = owner        # 所有者姓名
        self._balance = balance   # 余额（内部属性，通过方法改）

    def pay(self, amount):
        """支付指定金额，余额不足返回 False。"""
        if amount > self._balance:
            return False
        self._balance -= amount
        return True

w = Wallet("小张", 100)
print(f"支付 50：{w.pay(50)}，支付 100：{w.pay(100)}")

# 案例四：TODO 注释 —— 标记待办事项
def export_report(data):
    """导出报表。当前仅支持 CSV 格式。"""
    # TODO(小张): 支持导出 Excel，预计下版本
    # FIXME: 数据超过 1 万行时会很慢，需要分批
    return ",".join(map(str, data))

print(f"导出：{export_report([1, 2, 3])}")

# ===== 练习题 =====
# 1. 给函数 check_age(age) 写完整 docstring（功能/参数/返回值）：0~120 返回 True 否则 False，并用 help() 验证。
# 2. 把"# 循环列表"这种废话注释改写成解释业务意图的注释（如：找出今天要发货的订单）。
# 3. 给 Calculator 类写 docstring 和 add/subtract 两个方法的 docstring，用 help(Calculator) 查看效果。
