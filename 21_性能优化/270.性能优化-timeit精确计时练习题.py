# ===== 第270课：性能优化-timeit精确计时 =====
# 知识点：
#   - timeit：多次重复取最小值，排除偶然干扰，适合微基准
#   - number：执行多少次；repeat：重复几轮，取最优
#   - setup：准备工作（导入、造数据），不计入计时
#   - 分工：粗测整体用 perf_counter，精测单行用 timeit

import random
import timeit

# 基本用法：语句字符串 + 执行次数
stmt = "sum(range(1000))"
print("1000 次共耗时：", timeit.timeit(stmt, number=1000))

# repeat：跑 5 轮取最小值（最小值最能代表真实开销）
best = min(timeit.repeat(stmt, number=1000, repeat=5))
print("5 轮最优：", best)

# setup：先准备环境（不计入时间）
shuffle_time = timeit.timeit(
    "random.shuffle(x)",
    setup="import random; x = list(range(100))",
    number=1000,
)
print("洗牌 100 次：", shuffle_time)

# 对比两种写法：join 生成器 vs join 列表推导
t_gen = timeit.timeit('"-".join(str(n) for n in range(100))', number=10000)
t_list = timeit.timeit('"-".join([str(n) for n in range(100)])', number=10000)
print(f"join 生成器：{t_gen:.4f}s | join 列表推导：{t_list:.4f}s")

# 用函数方式计时（不用字符串也行）
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)


t = timeit.timeit(lambda: fib(20), number=100)
print(f"fib(20) x100：{t:.4f}s")

# ===== 练习题 =====
# 1. 对比 x in list 与 x in set（1000 次判断），量化差距。
# 2. 用 repeat=5 测两种字符串格式化：f-string 与 %，谁更快？
# 3. 写一个“错误示范”：只跑一次计时，解释为什么结果不可靠。
# 4. 思考：微基准的结果能直接推断整个程序的性能吗？
