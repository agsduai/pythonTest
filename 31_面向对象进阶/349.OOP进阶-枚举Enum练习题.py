# ===== 第349课：OOP进阶-枚举Enum =====
# 知识点：
#   - Enum：一组“有名字的常量”，替代魔法字符串/数字
#   - auto() 自动编号；按名取值 Status["PAID"]；按值取 Status(2)
#   - 成员是单例：is 比较安全；重复值会合并成同一成员
#   - 场景：订单状态、日志级别、配置开关 —— 拼写错误在定义处就暴露
from enum import Enum, auto


class Status(Enum):
    PENDING = auto()        # 待支付
    PAID = auto()           # 已支付
    SHIPPED = auto()        # 已发货
    CLOSED = auto()         # 已关闭


def handle(status: Status) -> str:
    if status is Status.PAID:                  # 单例：is 比较最稳
        return "已支付，准备发货"
    return f"当前状态：{status.name}"


print(handle(Status.PAID))
print(handle(Status.PENDING))

# 遍历与查找
print("全部状态：", [s.name for s in Status])
print("按名取值：", Status["PAID"], "| 按值取：", Status(2))

# 字符串值枚举：直接存库/传接口都友好
class Color(Enum):
    RED = "红色"
    BLUE = "蓝色"


print(Color.RED.value, "| 按值取：", Color("蓝色"))

# 重复值会合并：RED2 和 RED 是同一个成员
class Badge(Enum):
    GOLD = 1
    TOP = 1                    # 别名：Badge.TOP 就是 Badge.GOLD

print("别名合并：", Badge.TOP is Badge.GOLD)

# 对照魔法值的三大痛点：拼错不报错、取值含义不明、新增状态全局搜
# def handle_bad(status): if status == "paid": ...   ← "Paid"/"PAYD" 都不报错

# ===== 练习题 =====
# 1. 用 Enum 重写第196课日志级别（DEBUG/INFO/...），并实现“能否显示”判断。
# 2. 给 Status 增加 is_finished 属性（用 property：CLOSED/SHIPPED 算完结）。
# 3. 思考：枚举与“模块级大写常量”相比多了什么能力？
