# ===== 第065课：核心语法-函数进阶-默认参数 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 定义函数时可以给参数指定默认值，调用时可以不传该参数
#   - 默认参数必须放在普通参数后面
#   - 调用时传入新值，默认值会被覆盖
#   - 默认值在函数定义时只计算一次，可变默认值要谨慎使用

def greet(name, message="你好"):
    print(f"{name}，{message}！")

greet("小明")                  # 不传 message，使用默认值
greet("小红", "早上好")        # 传入新值，覆盖默认值
greet("小刚", message="晚上好")

def power(base, exponent=2):
    return base ** exponent

print("5 的平方：", power(5))
print("2 的立方：", power(2, 3))

def make_profile(name, age=18, city="北京"):
    print(f"姓名：{name}，年龄：{age}，城市：{city}")

make_profile("小明")
make_profile("小红", 20)
make_profile("小刚", city="上海")

# 默认参数不能放在普通参数前面
# def wrong(a=1, b):  # 取消注释会报 SyntaxError
#     print(a, b)

# 可变默认值示例：默认列表会在多次调用之间共享
def add_item(item, items=[]):
    items.append(item)
    return items

print(add_item("A"))   # ['A']
print(add_item("B"))   # ['A', 'B']，默认列表被复用

# ===== 练习题 =====
# 1. 定义 send_message(content, receiver="全班同学")，不传 receiver 时发给全班。
# 2. 定义 power(base, exponent=2)，分别计算 5 的平方和 2 的立方。
# 3. 定义 make_profile(name, age=18, city="北京")，用不同方式调用并输出信息。
