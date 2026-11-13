# ===== 第360课：底层机制-一切皆对象 =====
# 知识点：
#   - Python 里“万物皆对象”：int 是对象，函数是对象，类本身也是对象
#   - type 链条：实例 → 类 → type；id() 身份、is 身份比较、== 值比较
#   - 函数可赋值、可挂属性、可传参 —— 第187课装饰器的地基
#   - 小整数缓存是 CPython 实现细节：知道即可，别依赖
print(type(42), type(int), type(type))     # 一路向上都是 type

# 身份 vs 值
a, b = [1, 2], [1, 2]
print("== 值相等：", a == b, "| is 身份相同：", a is b)
print("id：", id(a) != id(b))

# 函数是对象
def hello():
    return "hi"


f = hello                                  # 赋值：函数可以当值传来传去
print("调用别名：", f(), "| 函数名：", hello.__name__, "| 可调用：", callable(hello))
hello.author = "课程学员"                    # 函数也能挂属性
print("函数属性：", hello.author)

# 类也是对象：可以赋值、传参、动态创建
MyList = list                              # 类赋值
print(MyList([1, 2]))
Dynamic = type("Dynamic", (), {"greet": lambda self: "我是动态类"})
print(Dynamic().greet())

# 小整数缓存（-5~256）与字符串驻留：CPython 优化细节
x, y = 100, 100
print("小整数缓存：", x is y)
print("大整数没有缓存保证 —— 数值比较永远用 ==，别用 is")

# ===== 练习题 =====
# 1. 打印 "abc" 的 type、id，再连续两次 id("abc") 看是否相同。
# 2. 把一个函数放进 dict 当值，模拟“策略表”（对照第259课）。
# 3. 思考：type(type) 为什么是 type 自己？（自举）
