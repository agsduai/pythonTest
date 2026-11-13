# ===== 第361课：底层机制-引用计数与垃圾回收 =====
# 知识点：
#   - 主回收机制：引用计数 —— 归零即释放（确定性强、开销平摊）
#   - sys.getrefcount：查看引用数（返回值天然多 1，因为传参本身是引用）
#   - 循环引用是计数法的盲区 → gc 模块的分代回收兜底
#   - weakref 弱引用：不增加计数，缓存/观察者的正确姿势
import gc
import sys
import weakref


class Node:
    def __init__(self, name):
        self.name = name


a = Node("A")
print("引用计数：", sys.getrefcount(a))        # 2：a + 传参
b = a
print("b = a 之后：", sys.getrefcount(a))      # 3
del b
print("del b 之后：", sys.getrefcount(a))      # 2

# ---- 循环引用：计数永远不归零 ----
x, y = Node("X"), Node("Y")
x.partner, y.partner = y, x                    # 互相引用
del x, y                                       # 外部引用没了，但内部互相拉着
gc.collect()                                   # 分代回收登场，清掉循环垃圾
print("gc.collect() 已处理循环引用")

# ---- 弱引用：引用但不续命 ----
obj = Node("缓存对象")
ref = weakref.ref(obj)
print("弱引用取值：", ref().name)
del obj                                        # 强引用没了 → 对象立刻销毁
print("销毁后弱引用：", ref())                  # None

# ---- 与第217课呼应：为什么能随手 del、不怕内存泄漏 ----
# 计数机制让“不再使用的对象”几乎立即释放；
# 例外是循环引用与全局缓存 —— 后者要靠你主动设计（如 weakref / lru_cache）

# ===== 练习题 =====
# 1. 让两个对象互相引用后 del，用 gc.collect 前后 len(gc.get_objects()) 对比。
# 2. 用 weakref.WeakValueDictionary 实现一个“对象还在才命中”的缓存。
# 3. 思考：第236课 lru_cache 为什么可能“内存泄漏”？（强引用持有结果）
