# ===== 第069课：核心语法-函数进阶-案例1(递归) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 递归：函数在内部调用自己
#   - 递归必须有终止条件（基准情形），否则会无限调用
#   - 每次递归都要让问题规模变小，逐渐接近终止条件
#   - 递归适合处理阶乘、斐波那契、累加等具有自相似结构的问题

def factorial(n):
    if n == 1:                    # 终止条件
        return 1
    return n * factorial(n - 1)   # 递归调用，规模减 1

print("5! =", factorial(5))

def sum_to(n):
    if n == 1:
        return 1
    return n + sum_to(n - 1)

print("1~100 的和：", sum_to(100))

def fibonacci(n):
    if n <= 2:                    # 前两项都是 1
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)

print("斐波那契前 8 项：", [fibonacci(i) for i in range(1, 9)])

# 递归调用过程（以 factorial(3) 为例）：
# factorial(3) = 3 * factorial(2)
#              = 3 * (2 * factorial(1))
#              = 3 * (2 * 1) = 6

# 没有终止条件会报 RecursionError
# def wrong(n):
#     return wrong(n - 1)
# wrong(1)

# ===== 练习题 =====
# 1. 用递归实现 countdown(n)，从 n 倒序输出到 1。
# 2. 用递归求一个正整数的各位数字之和，如 1234 的结果为 10。
# 3. 用递归反转字符串，如 "python" 反转为 "nohtyp"。
