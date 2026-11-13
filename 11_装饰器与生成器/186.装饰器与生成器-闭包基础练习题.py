# ===== 第186课：装饰器与生成器-闭包基础 =====
# 知识点：
#   - 闭包：内层函数引用外层函数的变量，并且外层函数把内层函数返回
#   - 闭包让函数“记住”创建它时的环境，是实现装饰器的基础
#   - nonlocal：让内层函数可以修改外层函数的局部变量
#   - 经典陷阱：循环中创建的闭包共享同一个循环变量


def make_multiplier(factor):
    """外层函数：接收 factor，返回一个内层函数。"""
    def multiply(x):
        # multiply 引用了外层的 factor，形成闭包
        return x * factor

    return multiply        # 返回函数本身，注意不带括号


double = make_multiplier(2)    # double 记住了 factor=2
triple = make_multiplier(3)    # triple 记住了 factor=3
print(double(10))      # 20
print(triple(10))      # 30

# 每次调用 make_multiplier 都会产生一套独立的变量
print(double(5), triple(5))    # 10 15


# nonlocal：内层函数修改外层函数的局部变量
def make_counter():
    count = 0

    def step():
        nonlocal count      # 声明使用外层的 count，而不是新建局部变量
        count += 1
        return count

    return step


counter = make_counter()
print(counter(), counter(), counter())    # 1 2 3：状态被“记住”了


# 经典陷阱：循环变量被所有闭包共享
funcs = []
for i in range(3):
    funcs.append(lambda: i)          # 三个 lambda 引用的是同一个 i
print([f() for f in funcs])          # [2, 2, 2]，循环结束后 i=2

funcs_fixed = []
for i in range(3):
    funcs_fixed.append(lambda x=i: x)   # 用默认参数把当时的值“固化”
print([f() for f in funcs_fixed])       # [0, 1, 2]


# 闭包典型应用：带配置的工具函数
def make_validator(min_len):
    def validate(text):
        return len(text) >= min_len

    return validate


check_username = make_validator(4)     # 用户名至少 4 位
check_password = make_validator(8)     # 密码至少 8 位
print(check_username("tom"), check_password("12345678"))
print(check_username("ab"), check_password("123456"))

# ===== 练习题 =====
# 1. 编写闭包 make_greeter(greeting)，make_greeter("你好") 返回的函数
#    接收姓名参数，返回 "你好，姓名"。
# 2. 编写闭包 make_accumulator()，返回的函数每次调用会把参数累加进去
#    并返回累计总和（提示：nonlocal）。
# 3. 解释为什么 funcs 的三个 lambda 都输出 2，并用默认参数方式验证修复。
# 4. 思考：闭包和全局变量都能“记住”状态，各自有什么优缺点？
