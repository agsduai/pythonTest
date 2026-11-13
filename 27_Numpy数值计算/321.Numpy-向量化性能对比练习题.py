# ===== 第321课：Numpy-向量化性能对比 =====
# 知识点：
#   - 向量化：把循环变成整组运算，C 层执行
#   - 与第274课呼应：算法优化 > 数据结构 > 微优化，向量化是“换引擎”
#   - 内存：ndarray 连续紧凑；list 是“指针数组 + 每个对象独立开销”
# 依赖：pip install numpy

import sys
import timeit

import numpy as np

N = 1_000_000
py_list = list(range(N))
arr = np.arange(N)


def loop_double():
    total = 0
    for x in py_list:
        total += x * 2
    return total


t_loop = timeit.timeit(loop_double, number=10) / 10
t_vec = timeit.timeit(lambda: (arr * 2).sum(), number=10) / 10
print(f"Python 循环：{t_loop:.4f} 秒/次")
print(f"NumPy 向量化：{t_vec:.5f} 秒/次")
print(f"加速约 {t_loop / t_vec:.0f} 倍")

# 内存对比
print("ndarray 占用：", arr.nbytes / 1e6, "MB（纯数据）")
print("list 容器本身：", sys.getsizeof(py_list) / 1e6, "MB（还不含每个 int 对象约 28 字节）")

# 向量化改写的思维方式：先想“整组怎么算”，再想“每个元素怎么算”
prices = np.array([100, 200, 300])
quantities = np.array([2, 1, 3])
# 不写循环：直接两组数组对应相乘再求和
print("总金额：", (prices * quantities).sum())

# ===== 练习题 =====
# 1. 把 N 改成 10_000_000 再测，观察加速倍数变化。
# 2. 向量化重写第274课的判重逻辑（提示：np.unique）。
# 3. 思考：哪些任务不适合向量化？（提示：前后依赖的迭代、复杂分支逻辑）
