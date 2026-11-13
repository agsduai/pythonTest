# ===== 第346课：OOP进阶-__slots__与内存 =====
# 知识点：
#   - 普通对象的属性存在 __dict__ 里：灵活但每个对象多一份字典开销
#   - __slots__：固定属性集合，省内存、防手滑加错属性
#   - 代价：失去动态性（加不进 slots 之外的属性）
#   - 场景：百万级小对象（粒子、订单行、棋子）
import sys


class PointNormal:

    def __init__(self, x, y):
        self.x, self.y = x, y


class PointSlots:

    __slots__ = ("x", "y")            # 声明：只有这两个属性

    def __init__(self, x, y):
        self.x, self.y = x, y


p = PointNormal(1, 2)
print("普通对象有 __dict__：", p.__dict__)
p.z = 99                            # 随手加属性，无人拦截
print("动态加属性：", p.z)

s = PointSlots(1, 2)
print("slots 对象没有 __dict__：", not hasattr(s, "__dict__"))
try:
    s.z = 99
except AttributeError as exc:
    print("slots 拦截：", exc)

# 内存估算：属性字典约 100+ 字节/对象
print("普通对象字典开销：", sys.getsizeof(p.__dict__), "字节")
print("slots 对象本体：", sys.getsizeof(s), "字节")
print("100 万个对象：普通 ≈ 多用", sys.getsizeof(p.__dict__) * 1e6 / 1e8, "亿字节级差距")

# 与第272课呼应：这也是“换数据结构”级别的优化

# ===== 练习题 =====
# 1. 用 tracemalloc（第366课预告）实测 10 万个对象的内存差。
# 2. 给 PointSlots 加继承子类（子类也要声明 __slots__）。
# 3. 思考：什么时候“能动态加属性”比省内存更重要？
