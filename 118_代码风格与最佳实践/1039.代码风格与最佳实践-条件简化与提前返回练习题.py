# ===== 第1039课：代码风格与最佳实践-条件简化与提前返回 =====
# 知识点：
#   - 嵌套 if 是可读性杀手：能用提前返回就别嵌套
#   - 多个 or 条件可以合并：x in ("a", "b", "c") 替代三个 ==
#   - 三元表达式：value = A if 条件 else B，简单赋值一行搞定
#   - 空值判断链：if not obj: return 提前拦截，主逻辑不再缩进

# 案例一：合并重复条件 —— in 扫清一排 ==
# 烂写法：
fruit = "苹果"
# if fruit == "苹果" or fruit == "香蕉" or fruit == "橙子":
#     print("水果区")
# 好写法：
if fruit in ("苹果", "香蕉", "橙子"):
    print(f"{fruit} 属于水果区")
if fruit not in ("牛奶", "面包"):
    print(f"{fruit} 不属于烘焙区")

# 案例二：提前返回 —— 消灭 else
# 烂：主逻辑藏在 else 里
def ship_fee_bad(weight):
    if weight > 10:
        fee = 30
    else:
        if weight > 5:
            fee = 20
        else:
            fee = 10
    return fee

# 好：条件一不满足就立刻返回
def ship_fee_good(weight):
    if weight > 10:
        return 30
    if weight > 5:
        return 20
    return 10

print(f"运费对比：{ship_fee_bad(7)} / {ship_fee_good(7)}")

# 案例三：三元表达式 —— 简单赋值不再写 if 块
# 烂：
score = 85
# if score >= 60:
#     label = "及格"
# else:
#     label = "不及格"
# 好：一行
label = "及格" if score >= 60 else "不及格"
print(f"{score} 分：{label}")

# 默认值场景：or 或三元
phone = ""
display = phone if phone else "未填写"
print(f"电话：{display}")

# 案例四：空值拦截链 —— 先排雷再干活
def process_order(order):
    if order is None:
        return "订单不存在"
    if not order.get("items"):
        return "空订单"
    if order.get("status") != "paid":
        return "未支付"
    # 走到这里说明一切正常，主逻辑零嵌套
    return f"处理订单 {order['id']}，{len(order['items'])} 件商品"

print(process_order(None))
print(process_order({"id": "A1", "items": [], "status": "paid"}))
print(process_order({"id": "A2", "items": ["苹果"], "status": "unpaid"}))
print(process_order({"id": "A3", "items": ["苹果", "牛奶"], "status": "paid"}))

# 案例五：and/or 短路 —— 别炫技，可读优先
# ok = data and data.get("key")  这种写法省事但容易看不懂，团队协作少用
data = {"key": "value"}
if data and data.get("key"):
    print(f"key 存在且非空：{data['key']}")

# ===== 练习题 =====
# 1. 用 in 合并判断：生肖属于 ["鼠","牛","虎","兔"] 之一输出"北半球生肖"（自造题意即可），else 输出"其他"。
# 2. 把嵌套的 if/else 判断（VIP？有券？满 100？各不同折扣）改写成提前返回式的函数，三种输入验证结果一致。
# 3. 用三元表达式一行实现：score >= 90 给 "A"，>=80 给 "B"，否则 "C"（可嵌套三元）。
