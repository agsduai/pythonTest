# ===== 第067课：核心语法-函数进阶-参数类型(函数作为参数) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 函数本身也是一种数据，可以赋值给变量、放进容器
#   - 函数可以作为另一个函数的参数传入，这种函数常被称为高阶函数
#   - 在函数内部通过“参数名()”调用传入的函数
#   - 这种写法让同一个流程可以搭配不同的具体逻辑

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def calculate(func, a, b):
    """func 是形参，接收一个函数。"""
    return func(a, b)

print("加法：", calculate(add, 3, 4))
print("减法：", calculate(subtract, 3, 4))
print("乘法：", calculate(multiply, 3, 4))

# 函数可以放进字典，根据运算符选择要执行的函数
operations = {"+": add, "-": subtract, "*": multiply}
print("字典选择函数：", operations["+"](10, 5))

# 把函数作为参数，连续应用两次
def apply_twice(func, value):
    return func(func(value))

def double(x):
    return x * 2

print("连续翻倍：", apply_twice(double, 3))

# ===== 练习题 =====
# 1. 定义 is_even(n)，再定义 count_if(numbers, func) 统计满足 func 条件的元素个数。
# 2. 定义 square(x)，用 apply_twice 让它连续平方两次，计算 2 的结果。
# 3. 在 operations 字典中加入除法函数 divide，并调用验证。
