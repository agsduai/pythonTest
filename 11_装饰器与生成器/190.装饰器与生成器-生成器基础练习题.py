# ===== 第190课：装饰器与生成器-生成器基础 =====
# 知识点：
#   - 生成器：函数体里带 yield，调用后返回生成器对象，代码并不立即执行
#   - 惰性求值：每次 next() 执行到 yield 暂停，下次从暂停处继续
#   - 生成器是迭代器：一次性，取完即空
#   - 生成器表达式：(表达式 for x in 可迭代对象)，比列表推导式省内存


def simple_gen():
    print("第一步执行")
    yield 1
    print("第二步执行")
    yield 2
    print("第三步执行")
    yield 3


gen = simple_gen()       # 只创建生成器对象，函数体没有运行
print(type(gen))         # <class 'generator'>
print(next(gen))         # 打印“第一步执行”，返回 1 后暂停
print(next(gen))         # 从上次暂停处继续，打印“第二步执行”，返回 2

# for 会自动迭代生成器直到结束
for value in simple_gen():
    print("for拿到：", value)

# 生成器是一次性的
gen2 = simple_gen()
print(list(gen2))        # [1, 2, 3]
print(list(gen2))        # []


# 生成器表达式：把 [] 换成 () 就从“立即列表”变成“按需生成”
squares_list = [x ** 2 for x in range(5)]     # 立即算出所有元素
squares_gen = (x ** 2 for x in range(5))      # 只记下规则，不占内存
print(squares_list)
print(next(squares_gen), next(squares_gen))   # 0 1
print(sum(x ** 2 for x in range(10)))         # 聚合函数可直接接收生成器


# 对比内存：一百万个数，列表真存一百万个，生成器只存“下一步怎么算”
big_gen = (i for i in range(1_000_000))
print(next(big_gen), next(big_gen))           # 0 1


# yield 会保存“现场”：函数从暂停点继续，变量都还在
def fibonacci(limit):
    a, b = 0, 1
    while a <= limit:
        yield a            # 每次循环到这里暂停，交出一个值
        a, b = b, a + b    # 唤醒后从这里继续


print(list(fibonacci(20)))   # [0, 1, 1, 2, 3, 5, 8, 13]

# ===== 练习题 =====
# 1. 编写生成器 countdown(n)，从 n 倒数到 1，用 for 遍历验证。
# 2. 把第189课的 Countdown 类改写成生成器函数，对比代码量。
# 3. 分别用 sys.getsizeof 查看 1000 万元素的列表和生成器表达式
#    各占多少字节，体会惰性求值的好处。
# 4. 思考：什么时候该用列表，什么时候该用生成器？
