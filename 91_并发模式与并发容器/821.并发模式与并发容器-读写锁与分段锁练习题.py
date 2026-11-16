# ===== 第821课：并发模式与并发容器-读写锁与分段锁 =====
# 知识点：
#   - 读写锁 ReadWriteLock：多个读者可并发，写者独占
#   - 分段锁 striping：把数据按 key 哈希分到 N 个锁，减少锁竞争
#   - 与单一 Lock 的对比：读多写少场景读写锁吞吐量远高于互斥锁
#   - 写者饥饿问题：需要写优先策略（等待写者到达时阻止新读者）
#   - 本课手写读写锁与分段锁，并用并发压力测试对比吞吐量
# 依赖：无（标准库）
import threading
import random
import time
from collections import defaultdict


class ReadWriteLock:
    """读写锁：读共享、写独占、写优先。"""

    def __init__(self):
        self._readers = 0
        self._writers_waiting = 0
        self._write_lock = threading.Lock()
        self._cond = threading.Condition(self._write_lock)

    def acquire_read(self):
        with self._cond:
            while self._writers_waiting > 0:      # 写优先：有写者在等就让读者等
                self._cond.wait()
            self._readers += 1

    def release_read(self):
        with self._cond:
            self._readers -= 1
            if self._readers == 0:
                self._cond.notify_all()

    def acquire_write(self):
        with self._cond:
            self._writers_waiting += 1
            while self._readers > 0 or self._writers_waiting > 1:
                self._cond.wait()
            self._writers_waiting -= 1

    def release_write(self):
        with self._cond:
            self._cond.notify_all()

    def read(self):
        return self.acquire_read

    def write(self):
        return self.acquire_write


class RWDict:
    """用读写锁包装的线程安全字典。"""

    def __init__(self):
        self._rw = ReadWriteLock()
        self._data = {}

    def get(self, key):
        self._rw.acquire_read()
        try:
            return self._data.get(key)
        finally:
            self._rw.release_read()

    def set(self, key, value):
        self._rw.acquire_write()
        try:
            self._data[key] = value
        finally:
            self._rw.release_write()

    def delete(self, key):
        self._rw.acquire_write()
        try:
            self._data.pop(key, None)
        finally:
            self._rw.release_write()

    def size(self):
        self._rw.acquire_read()
        try:
            return len(self._data)
        finally:
            self._rw.release_read()


print("== 读写锁基本操作 ==")
d = RWDict()
d.set("a", 1); d.set("b", 2)
print(f"  get('a') = {d.get('a')}")
print(f"  size = {d.size()}")
d.delete("a")
print(f"  delete('a') 后 size = {d.size()}")

print("\n== 压力测试：读多写少（90% 读 10% 写）==")
def rw_benchmark(lock_type, n_threads=8, ops=5000):
    if lock_type == "rw":
        store = RWDict()
        def do_read(key): return store.get(key)
        def do_write(key, val): store.set(key, val)
    elif lock_type == "mutex":
        lock = threading.Lock()
        store = {}
        def do_read(key): 
            with lock: return store.get(key)
        def do_write(key, val):
            with lock: store[key] = val
    else:
        store = {}
        def do_read(key): return store.get(key)
        def do_write(key, val): store[key] = val

    rng = random.Random(42)
    keys = [f"key{i}" for i in range(50)]
    for k in keys: do_write(k, 0)

    errors = []
    def worker(tid):
        r = random.Random(tid)
        for _ in range(ops):
            if r.random() < 0.9:
                do_read(r.choice(keys))
            else:
                do_write(r.choice(keys), r.randint(0, 1000))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
    t0 = time.perf_counter()
    for t in threads: t.start()
    for t in threads: t.join()
    dt = time.perf_counter() - t0
    return dt

for lock_type in ("mutex", "rw"):
    dt = rw_benchmark(lock_type)
    print(f"  {lock_type:<8}: 耗时={dt*1000:.1f}ms")

print("\n== 分段锁 Striping ==")
class StripedDict:
    """按 key 哈希分到 N 个段，每段一把锁。"""

    def __init__(self, n_segments=8):
        self.n = n_segments
        self.locks = [threading.Lock() for _ in range(n_segments)]
        self.segments = [{} for _ in range(n_segments)]

    def _segment(self, key):
        return hash(key) % self.n

    def set(self, key, value):
        idx = self._segment(key)
        with self.locks[idx]:
            self.segments[idx][key] = value

    def get(self, key):
        idx = self._segment(key)
        with self.locks[idx]:
            return self.segments[idx].get(key)

    def delete(self, key):
        idx = self._segment(key)
        with self.locks[idx]:
            self.segments[idx].pop(key, None)

    def size(self):
        return sum(len(seg) for seg in self.segments)


print("\n== 分段锁：并发写不同 key 不竞争同一把锁 ==")
sd = StripedDict(n_segments=4)
threads = []
for t_id in range(4):
    def writer(tid=t_id):
        for i in range(500):
            sd.set(f"t{tid}_k{i}", i)
    threads.append(threading.Thread(target=writer))
for t in threads: t.start()
for t in threads: t.join()
print(f"  4 线程各写 500 条，总条目={sd.size()}（期望 2000）")

print("\n== 分段锁 vs 全局锁 vs RWLock 对比 ==")
print(f"  {'方案':<14}{'读并发':<14}{'写并发':<14}{'适用场景'}")
for row in (("全局 Lock", "无", "无", "简单场景"),
            ("读写锁", "有", "无", "读多写少"),
            ("分段锁", "有(不同段)", "有(不同段)", "大量独立 key")):
    print(f"  {row[0]:<14}{row[1]:<14}{row[2]:<14}{row[3]}")

print("\n== 工程要点 ==")
for line in [
    "  读写锁不总是更快：锁本身有开销，读很短时可能反而慢",
    "  分段锁的「全量遍历」需要获取所有锁，代价高",
    "  Python 的 GIL 使纯 CPU 密集操作不需要锁（但 IO 密集需要）",
    "  生产环境可考虑 concurrent.futures / asyncio 消除显式锁",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给 ReadWriteLock 加「升级」操作：读锁 → 写锁（原子升级）。
# 2. 实现带过期时间的分段锁缓存（TTL + 惰性淘汰）。
# 3. 用 `threading.Barrier` 同步所有线程启动时间，公平对比吞吐量。
# 4. 思考：为什么「分段锁」在 key 分布不均时会退化为全局锁？
