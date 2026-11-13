# ===== 第063课：核心语法-函数进阶-变量作用域 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 局部变量：定义在函数内部，只在函数内部有效
#   - 全局变量：定义在函数外部，整个文件都可以读取
#   - 函数内读取全局变量可以直接使用，修改全局变量需要 global 声明
#   - 变量查找顺序：局部作用域 -> 全局作用域 -> 内置作用域

score = 100  # 全局变量

def show_score():
    print("函数内读取全局变量 score：", score)  # 直接读取全局变量

show_score()

def change_score():
    score = 60  # 这里创建的是局部变量，不会修改全局变量
    print("函数内的局部变量 score：", score)

change_score()
print("函数外的全局变量 score：", score)

total = 0  # 全局变量，用于累计总分

def add_score(value):
    global total          # 声明下面修改的是全局变量 total
    total += value

add_score(90)
add_score(85)
print("累计总分：", total)

def local_demo():
    msg = "我是局部变量"
    print(msg)

local_demo()
# print(msg)  # 取消注释会报错：局部变量在函数外无法访问

# ===== 练习题 =====
# 1. 定义全局变量 count = 0，定义函数 increase() 每次把 count 加 1，调用三次后输出 count。
# 2. 定义全局变量 price = 100，在函数 discount 内部定义同名局部变量 price = 80，观察输出。
# 3. 先预测再验证：x = 10；定义函数 f() 内部写 x = 20 并打印，调用 f() 后再打印 x。
