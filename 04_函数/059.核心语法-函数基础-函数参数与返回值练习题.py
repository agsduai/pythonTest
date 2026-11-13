# ===== 第059课：核心语法-函数基础-函数参数与返回值 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 参数：调用函数时传给函数的数据，写在函数名后面的括号里
#   - 多个参数用逗号分隔，调用时按位置顺序一一对应
#   - return 把结果返回给调用者，同时结束当前函数的执行
#   - 函数没有 return 时默认返回 None；return 也能一次返回多个值

# 带一个参数的函数
def greet(name):
    print(f"你好，{name}！")

greet("小明")          # 实参 "小明" 传给形参 name

# 带多个参数的函数：按顺序对应
def add(a, b):
    return a + b       # 把计算结果返回给调用者

result = add(3, 5)     # 用变量接收返回值
print("3 + 5 =", result)

# 一次返回多个值：本质上返回的是元组
def calc(a, b):
    return a + b, a - b, a * b

add_res, sub_res, mul_res = calc(10, 4)   # 解包接收三个返回值
print("和：", add_res, "差：", sub_res, "积：", mul_res)

# 没有 return 的函数，返回值是 None
def show(msg):
    print("消息：", msg)

value = show("hello")
print("show 函数的返回值：", value)

# return 会立即结束函数，后面的代码不再执行
def check_score(score):
    if score >= 60:
        return "及格"
        print("这一行永远不会执行")
    return "不及格"

print(check_score(75))
print(check_score(50))

# ===== 练习题 =====
# 1. 定义函数 rectangle_area(length, width)，返回长方形面积，并调用输出结果。
# 2. 定义函数 max_of_three(a, b, c)，返回三个数中的最大值。
# 3. 定义函数 average(numbers)，接收一个列表，返回列表中所有数字的平均值。
