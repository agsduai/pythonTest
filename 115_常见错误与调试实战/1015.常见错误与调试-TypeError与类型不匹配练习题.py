# ===== 第1015课：常见错误与调试-TypeError与类型不匹配 =====
# 知识点：
#   - TypeError：对错误类型做了不支持的操作，如字符串加数字
#   - type() 查看变量类型，调试第一步：先搞清楚"它到底是什么类型"
#   - 常见来源：input() 得到的永远是字符串、函数忘了 return 得到 None
#   - 修复思路：str()、int()、float() 显式转换，或改用正确的操作

# 案例一：字符串拼接数字 —— 最高频的 TypeError
goods = "苹果"
price = 5.5
# print("单价：" + price)  # 报 TypeError：str 不能直接拼 float
print("单价：" + str(price))  # 方法1：转字符串
print(f"单价：{price}")  # 方法2：f-string 自动转，推荐

# 案例二：input() 的坑 —— 得到的永远是字符串
# 场景：让用户输入数量再计算总价
# count = input("请输入数量：")  # 假设输入 3
count = "3"  # 模拟 input 的返回值
price = 8.0
# total = price * int(count) 没问题，但下面这种写法就错了：
# total = price + count  # 报 TypeError：float + str 不行
total = price + float(count)  # 先转换再运算
print(f"总价：{total} 元")

# 案例三：函数忘写 return —— 得到 None
def get_discount(price):
    if price >= 100:
        return price * 0.8
    # 漏了 else 的 return！不满 100 时函数返回 None
    return price  # 修复：每个分支都要有返回值

result = get_discount(50)
if result is None:
    print("函数返回了 None，八成是忘写 return")
else:
    print(f"折后价：{result} 元")

# 案例四：None 上调用方法 —— object of type 'NoneType'
items = None  # 某个函数意外返回了 None
if items is not None and len(items) > 0:
    print(f"共 {len(items)} 件")
else:
    print("items 是 None，不能直接 len()，先判空")  # None 没有长度

# ===== 练习题 =====
# 1. 用 type() 打印 "5"、5、5.0、[5]、(5,) 的类型，写成一行注释总结它们各是什么。
# 2. 写函数 calc(amount, count) 返回 amount * count；先只写 half_amount = amount * 0.9 不写 return，观察调用结果是 None，再补上 return。
# 3. 有 name = "订单" 和 nums = [3, 5]，写出三种正确方式打印 "订单3-5"（f-string、str() 拼接、sep 参数）。
