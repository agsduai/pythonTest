# ===== 第187课：装饰器与生成器-函数装饰器 =====
# 知识点：
#   - 装饰器：接收一个函数，返回一个“增强版”函数的高阶函数
#   - @语法：@deco 写在函数定义上方，等价于 func = deco(func)
#   - wrapper 用 *args/**kwargs 兼容被装饰函数的任意参数
#   - functools.wraps：保留原函数的名字、文档字符串等元信息

import time
from functools import wraps


def log_call(func):
    """打印函数的调用与返回信息的装饰器。"""

    @wraps(func)                       # 没有它，add.__name__ 会变成 "wrapper"
    def wrapper(*args, **kwargs):
        print(f"调用 {func.__name__}，参数：{args} {kwargs}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} 返回：{result}")
        return result

    return wrapper


@log_call
def add(a, b):
    """计算两数之和。"""
    return a + b


add(1, 2)                  # 调用被自动记录，无需修改 add 的代码
print(add.__name__)        # add（有 @wraps 才能保留原名）
print(add.__doc__)         # 计算两数之和。


# 不用 @ 的等价写法，帮助理解 @ 的本质
def sub(a, b):
    return a - b


sub = log_call(sub)        # @log_call 只是这一行的语法糖
print(sub(5, 2))


# 实用装饰器：统计函数执行耗时
def timer(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        cost = time.perf_counter() - start
        print(f"{func.__name__} 耗时 {cost:.4f} 秒")
        return result

    return wrapper


@timer
def heavy_sum(n):
    """计算 0~n 的累加和。"""
    return sum(range(n + 1))


print(heavy_sum(1_000_000))

# ===== 练习题 =====
# 1. 编写装饰器 shout，把函数的返回值变成 "值!!!"（前后各加一个感叹号）。
# 2. 编写递归版斐波那契函数，用 timer 装饰它，对比 n=30 与 n=35 的耗时。
# 3. 删掉 @wraps(func) 再运行，观察 add.__name__ 变成了什么。
# 4. 思考：装饰器的包装逻辑在什么时机执行？（函数定义时还是调用时？）
