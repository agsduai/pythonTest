# ===== 第066课：核心语法-函数进阶-不定长参数 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - *args：接收任意个位置参数，打包成元组
#   - **kwargs：接收任意个关键字参数，打包成字典
#   - 普通参数、*args、**kwargs 可以组合使用，顺序不能乱
#   - 调用时可以用 * 和 ** 解包列表、元组、字典

def sum_all(*args):
    total = 0
    for n in args:       # args 是一个元组
        total += n
    return total

print(sum_all(1, 2, 3))
print(sum_all(10, 20, 30, 40))

def show_info(**kwargs):
    print("收到的信息：")
    for key, value in kwargs.items():   # kwargs 是一个字典
        print(f"  {key}: {value}")

show_info(name="小明", age=18)

def mixed(a, *args, **kwargs):
    print("a =", a)
    print("args =", args)
    print("kwargs =", kwargs)

mixed(1, 2, 3, name="小红", age=20)

# 调用时解包：把容器中的元素依次传给函数
numbers = [1, 2, 3]
print("列表解包求和：", sum_all(*numbers))

info = {"name": "小刚", "city": "广州"}
show_info(**info)

# ===== 练习题 =====
# 1. 定义函数 product(*args)，返回所有参数的乘积（没有参数时返回 1）。
# 2. 定义函数 describe(name, *hobbies)，输出姓名和所有爱好。
# 3. 定义函数 show_info(**kwargs)，用字典解包的方式传入姓名、年龄、城市。
