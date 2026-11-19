# ===== 第1012课：常见错误与调试-读懂Traceback =====
# 知识点：
#   - Traceback 是程序报错时的"事故报告"，从最后一行往上看
#   - 最后一行是错误类型和提示，如 NameError、ZeroDivisionError
#   - 中间的 File "xxx", line N 告诉你错在哪个文件第几行
#   - 看懂错误信息是调试的第一步，不要看到红色报错就慌

# 案例一：NameError —— 用了不存在的变量名
# 场景：变量名打错字，比如把 total_price 写成 total_prise
total_price = 59.9
# print(total_prise)  # 取消注释会报 NameError: name 'total_prise' is not defined
# 报错解读：'total_prise' 未定义 —— 十有八九是拼写错误，去检查变量名
print(f"总价：{total_price} 元")

# 案例二：ZeroDivisionError —— 除数是 0
# 场景：计算人均消费时，人数可能为 0
order_amount = 240
people_count = 0
if people_count > 0:
    print(f"人均：{order_amount / people_count} 元")
else:
    print("人数为 0，暂时不算人均，避免除零报错")

# 案例三：亲自触发一次报错，观察 Traceback 的结构
# 报错时会看到三部分：
#   Traceback (most recent call last):   <- 开头，表示"调用过程回溯"
#     File "xxx.py", line 20, in <module>  <- 错在哪一行
#     ZeroDivisionError: division by zero  <- 错误类型和原因
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"捕获到报错：{type(e).__name__}：{e}")
    print("真实场景里，报错信息直接告诉你错在哪一行、错在哪")

# 案例四：从报错信息反推修复方法
# 场景：报错 TypeError: can only concatenate str (not "int") to str
# 解读：字符串只能拼接字符串，你却拼了数字
name = "订单"
count = 3
# print(name + count)  # 报 TypeError
print(name + str(count))  # 正确做法：数字转成字符串再拼接

# ===== 练习题 =====
# 1. 故意写一行会报 NameError 的代码（用一个未定义的变量），运行并抄写报错的最后一行，再修正它。
# 2. 写"输入两数求商"的程序：当除数为 0 时不要报错崩溃，而是输出"除数不能为 0"。
# 3. 有 price = "100" 和 count = 3，直接 price * count 会输出 "100100100" 而不是 300，先运行观察，再改出正确算总价 300 的写法。
