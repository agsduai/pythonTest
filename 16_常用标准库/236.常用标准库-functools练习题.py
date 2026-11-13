# ===== 第236课：常用标准库-functools =====
# 知识点：
#   - functools.partial：固定部分参数，生成“预设版”新函数
#   - functools.reduce：滚动聚合，把序列压成一个值
#   - functools.lru_cache：给纯函数加缓存，递归性能救星
#   - functools.wraps：装饰器保留原函数元信息（第187课已用）

import functools
import time

# partial：偏函数
int2 = functools.partial(int, base=2)      # 二进制 → 十进制
print(int2("1010"), int2("11111111"))

power_of_2 = functools.partial(pow, 2)     # 2 的 n 次方
print(power_of_2(10))

# reduce：滚动聚合
print(functools.reduce(lambda a, b: a + b, [1, 2, 3, 4]))     # 10
print(functools.reduce(lambda a, b: a * b, range(1, 6)))      # 5! = 120
print(functools.reduce(lambda a, b: a if a > b else b, [3, 9, 2]))   # 最大值


# lru_cache：缓存函数结果（第069课递归斐波那契的性能救星）
@functools.lru_cache(maxsize=None)
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)


start = time.perf_counter()
print("fib(35) =", fib(35))
print(f"耗时 {time.perf_counter() - start:.4f} 秒（有缓存）")
print("缓存统计：", fib.cache_info())


# 对照组：不加缓存的朴素递归
def fib_slow(n):
    return n if n < 2 else fib_slow(n - 1) + fib_slow(n - 2)


start = time.perf_counter()
print("fib_slow(30) =", fib_slow(30))
print(f"耗时 {time.perf_counter() - start:.4f} 秒（无缓存，指数级）")

# ===== 练习题 =====
# 1. 用 partial 创建 round_to_2：默认保留 2 位小数的 round。
# 2. 用 reduce 实现“把 ['a','b','c'] 拼成 'a-b-c'”。
# 3. 给 fib_slow 加上 lru_cache，对比 fib(35) 前后的耗时。
# 4. 思考：什么函数不适合加 lru_cache？（提示：有副作用/返回可变对象）
