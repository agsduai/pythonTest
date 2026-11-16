# ===== 第819课：并发模式与并发容器-线程安全容器 =====
# 知识点：
#   - 并发写共享数据结构必须加锁或用线程安全容器
#   - threading.Lock：互斥锁，protect-then-act 模式
#   - collections.deque(maxlen=n) 天然线程安全（单次 append/pop 是原子操作）
#   - threading.RLock：可重入锁，允许同一线程多次获取
#   - 与第12章并发基础的关系：12 章讲 Thread/Queue 基础，本课聚焦「容器层面的安全模式」
#   - 常见陷阱：复合操作（读-改-写）不是原子的，即使单个操作是安全的
# 依赖：无（标准库）
import threading
import random
from collections import deque


class SafeCounter:
    """线程安全计数器：Lock 保护复合操作。"""

    def __init__(self):
        self._lock = threading.Lock()
        self._counts = {}

    def increment(self, key, amount=1):
        with self._lock:
            self._counts[key] = self._counts.get(key, 0) + amount
            return self._counts[key]

    def get(self, key):
        with self._lock:
            return self._counts.get(key, 0)


class SafeStack:
    """线程安全栈：用 Lock 包装 list。"""

    def __init__(self):
        self._lock = threading.Lock()
        self._items = []

    def push(self, item):
        with self._lock:
            self._items.append(item)

    def pop(self):
        with self._lock:
            if not self._items:
                raise IndexError("栈为空")
            return self._items.pop()

    def size(self):
        with self._lock:
            return len(self._items)


def demonstrate_race():
    """演示竞态条件：无锁计数器会丢失增量。"""
    counter = {"value": 0}
    lock = threading.Lock()
    ITER = 10000

    def unsafe_increment():
        for _ in range(ITER):
            counter["value"] += 1       # 读-改-写，非原子！

    def safe_increment():
        for _ in range(ITER):
            with lock:
                counter["value"] += 1   # 加锁保护复合操作

    threads_unsafe = [threading.Thread(target=unsafe_increment) for _ in range(4)]
    for t in threads_unsafe: t.start()
    for t in threads_unsafe: t.join()
    unsafe_result = counter["value"]
    counter["value"] = 0

    threads_safe = [threading.Thread(target=safe_increment) for _ in range(4)]
    for t in threads_safe: t.start()
    for t in threads_safe: t.join()
    safe_result = counter["value"]

    expected = 4 * ITER
    print(f"  无锁结果={unsafe_result}（期望 {expected}，丢失 {expected-unsafe_result} 次增量）")
    print(f"  加锁结果={safe_result}  期望={expected}")
    print("  复合操作（读-改-写）不是原子的！")


demonstrate_race()

print("\n== SafeCounter 多线程验证 ==")
sc = SafeCounter()
threads = []
for t_id in range(4):
    t = threading.Thread(target=lambda tid=t_id: [sc.increment(f"key{tid}") for _ in range(1000)])
    threads.append(t)
for t in threads: t.start()
for t in threads: t.join()
print("  各线程计数:", {k: sc.get(k) for k in sorted(sc._counts.keys())})
print("  总计:", sum(sc.get(f"key{i}") for i in range(4)), "（期望 4000）")

print("\n== SafeStack 多线程 ==")
stack = SafeStack()
push_threads = [threading.Thread(target=lambda: [stack.push(i) for i in range(100)])
                for _ in range(3)]
for t in push_threads: t.start()
for t in push_threads: t.join()
print(f"  压入后大小={stack.size()}（期望 300）")
popped = [stack.pop() for _ in range(stack.size())]
print(f"  全部弹出={len(popped)} 个，栈大小={stack.size()}")

print("\n== deque(maxlen) 天然线程安全 ==")
dq = deque(maxlen=5)
def append_thread():
    for i in range(100):
        dq.append(i)
t = threading.Thread(target=append_thread)
t.start()
t.join()
print(f"  deque 长度={len(dq)} 内容={list(dq)}")
print("  deque 的 append/popleft 是原子的（GIL 保护单个 C 调用）")
print("  但 len(dq) + append 的组合仍不是原子的")

print("\n== RLock 可重入锁 ==")
class ReentrantResource:
    def __init__(self):
        self._lock = threading.RLock()    # 可重入
        self._data = []

    def outer_method(self, item):
        with self._lock:
            self._data.append(item)
            self.inner_method()            # 同一线程再次获取锁 OK

    def inner_method(self):
        with self._lock:                   # RLock 允许重入；Lock 会死锁
            self._data.append("inner")

r = ReentrantResource()
r.outer_method("test")
print(f"  RLock 重入成功: {r._data}")

print("\n== 常见陷阱 ==")
for line in [
    "  check-then-act: if key not in dict: dict[key]=... → 两线程可能同时通过检查",
    "  读-改-写: counter += 1 在 Python 字节码层是多条指令",
    "  用 Lock 保护整个复合操作，而非只保护单个赋值",
    "  锁粒度：太粗影响并发，太细容易死锁；分段锁（第820课）是折中",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 SafeDict（线程安全字典），支持 get/set/delete/keys。
# 2. 用两个 Lock 实现「分段锁」的计数器（按 key 哈希分到不同锁），对比性能。
# 3. 演示「锁顺序死锁」：两个线程分别以不同顺序获取两把锁。
# 4. 思考：为什么 deque 单次 append 是原子的但 list.append + list.pop 组合不是？
