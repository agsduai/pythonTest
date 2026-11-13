# ===== 第271课：性能优化-cProfile找出热点 =====
# 知识点：
#   - cProfile：统计每个函数的调用次数与耗时，定位“热点”
#   - tottime：函数自身耗时；cumtime：含子调用的累计耗时
#   - pstats 排序输出；优化铁律：先剖析，再动手，不凭感觉

import cProfile
import io
import pstats
import time


def heavy_sum(n):
    return sum(i * i for i in range(n))


def busy_wait(seconds):
    end = time.perf_counter() + seconds
    while time.perf_counter() < end:
        pass


def slow_program():
    total = 0
    for _ in range(4):
        total += heavy_sum(1_500_000)
        busy_wait(0.05)
    return total


# 剖析：包住要测的代码段
profiler = cProfile.Profile()
profiler.enable()
result = slow_program()
profiler.disable()

print("程序结果：", result)

# 输出报告：按累计耗时排序，只看前几名
stream = io.StringIO()
stats = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
stats.print_stats(6)
print(stream.getvalue())

# 说明：
#   ncalls   调用次数
#   tottime  函数自身耗时（不含子函数）
#   cumtime  累计耗时（含子函数）
# 优化只做热点：耗时占比低的函数优化了也没感觉

# ===== 练习题 =====
# 1. 把 heavy_sum 的次数改成 8，观察热点排名变化。
# 2. 用 sort_stats("tottime") 再看一次，两种排序分别适合找什么问题？
# 3. 给第249课的递归斐波那契做剖析，看“调用次数爆炸”长什么样。
# 4. 思考：为什么说“没有测量的优化是赌博”？
