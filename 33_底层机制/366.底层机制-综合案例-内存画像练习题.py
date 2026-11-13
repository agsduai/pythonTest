# ===== 第366课：底层机制-综合案例-内存画像 =====
# 知识点：
#   - tracemalloc：跟踪“Python 层”内存分配，定位吃内存的代码
#   - 对比四种装点方式：元组 / 普通类 / __slots__ 类 / dataclass
#   - 生成器：不持有数据，内存与数据量无关（第190课）
#   - 方法论：先画像、再动手 —— 和第271课 CPU 剖析同一套思路
import sys
import tracemalloc
from dataclasses import dataclass


class Plain:

    def __init__(self, x, y):
        self.x, self.y = x, y


class Slotted:

    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x, self.y = x, y


@dataclass
class DataPoint:
    x: int
    y: int


def profile(label, builder, n=100_000):
    tracemalloc.start()
    objs = builder(n)                      # 期间分配的内存都被记账
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"{label:<22} 当前 {current / 1e6:5.1f} MB | 峰值 {peak / 1e6:5.1f} MB")
    return objs


profile("list + 元组", lambda n: [(i, i) for i in range(n)])
profile("list + 普通类", lambda n: [Plain(i, i) for i in range(n)])
profile("list + __slots__类", lambda n: [Slotted(i, i) for i in range(n)])
profile("list + dataclass", lambda n: [DataPoint(i, i) for i in range(n)])

# 生成器对照：只持有“下一个怎么算”
def gen(n):
    for i in range(n):
        yield (i, i)


tracemalloc.start()
g = gen(100_000)
print(f"{'生成器（不装数据）':<22} 持有 {sys.getsizeof(g)} 字节")
tracemalloc.stop()

# 结论预期：slots ≈ 元组 < dataclass < 普通类（每个对象省一份 __dict__）

# ===== 练习题 =====
# 1. 把 n 改成 1_000_000，观察各类占比是否保持一致。
# 2. 用 tracemalloc.take_snapshot() + statistics("lineno") 找出最耗内存的那一行。
# 3. 思考：CPU 剖析（271）与内存画像（本课）分别回答什么问题？
