# ===== 第486课：缓存设计-缓存击穿 =====
# 知识点：
#   - 缓存击穿：某个“热点 key”过期瞬间，大量并发请求同时打到数据库
#   - 与穿透的区别：穿透查的是不存在的数据；击穿查的是存在但缓存刚失效的数据
#   - 方案 1：互斥锁（mutex）——只让一个请求回源，其他请求等待/重试缓存
#   - 方案 2：逻辑过期——缓存不设 TTL，后台异步刷新，读取永远走缓存
#   - 方案 3：热点数据预热/永不过期
#   - 关键：锁内要“双重检查”，避免前一个请求已经填好缓存还重复回源
import threading
import time
from concurrent.futures import ThreadPoolExecutor


class SlowDB:
    def __init__(self, value):
        self.value = value
        self.calls = 0

    def get(self):
        self.calls += 1
        time.sleep(0.02)              # 模拟慢查询
        return self.value


# ---------------- 1. 无锁：并发全部回源 ----------------
def run_without_lock(db: SlowDB, threads=50):
    cache = {}
    db.calls = 0

    def get():
        if "hot" in cache:
            return cache["hot"]
        value = db.get()              # 缓存为空 → 所有线程都进来
        cache["hot"] = value
        return value

    with ThreadPoolExecutor(max_workers=threads) as pool:
        list(pool.map(lambda _: get(), range(threads)))
    return db.calls


# ---------------- 2. 互斥锁 + 双重检查 ----------------
def run_with_lock(db: SlowDB, threads=50):
    cache = {}
    lock = threading.Lock()
    db.calls = 0

    def get():
        if "hot" in cache:            # 快路径：无锁读
            return cache["hot"]
        with lock:
            if "hot" in cache:        # 双重检查：别人可能已经填好
                return cache["hot"]
            value = db.get()
            cache["hot"] = value
            return value

    with ThreadPoolExecutor(max_workers=threads) as pool:
        list(pool.map(lambda _: get(), range(threads)))
    return db.calls


print("== 50 个并发请求，热点 key 刚过期 ==")
db = SlowDB("商品详情")
print(f"  无锁：数据库调用 {run_without_lock(db)} 次")
print(f"  互斥锁：数据库调用 {run_with_lock(db)} 次")

# ---------------- 3. 逻辑过期：后台刷新 ----------------
class LogicalExpireCache:
    """存 (value, expire_at)，过期后先返回旧值，由一个线程异步刷新。"""

    def __init__(self, db: SlowDB, ttl=0.1):
        self.db = db
        self.ttl = ttl
        self.cache = None             # (value, expire_at)
        self.refresh_lock = threading.Lock()
        self.refreshes = 0
        self.db_calls = 0

    def get(self):
        now = time.monotonic()
        if self.cache is None:
            with self.refresh_lock:
                if self.cache is None:
                    self.db_calls += 1
                    self.cache = (self.db.get(), now + self.ttl)
            return self.cache[0]

        value, expire_at = self.cache
        if now >= expire_at:
            # 逻辑过期：不阻塞读，触发一次后台刷新
            if self.refresh_lock.acquire(blocking=False):
                def refresh():
                    try:
                        self.db_calls += 1
                        self.cache = (self.db.get(), time.monotonic() + self.ttl)
                        self.refreshes += 1
                    finally:
                        self.refresh_lock.release()

                threading.Thread(target=refresh, daemon=True).start()
        return value


print("\n== 逻辑过期（读旧值 + 异步刷新）==")
db2 = SlowDB("商品详情 v2")
lc = LogicalExpireCache(db2, ttl=0.05)
lc.get()                               # 预热
print("  预热完成，等待 TTL 过期...")
time.sleep(0.06)

start = time.perf_counter()
with ThreadPoolExecutor(max_workers=20) as pool:
    results = list(pool.map(lambda _: lc.get(), range(20)))
cost = time.perf_counter() - start
print(f"  20 个并发请求耗时 {cost:.3f}s（读旧值，不阻塞）")
print(f"  数据库调用 {lc.db_calls} 次，后台刷新 {lc.refreshes} 次")
print("  结果一致：", len(set(results)) == 1)

# ---------------- 4. 方案对比 ----------------
print("\n== 方案对比 ==")
rows = [
    ("互斥锁", "强一致、实现简单", "等待期间延迟升高；锁要防死锁"),
    ("逻辑过期", "读不阻塞、吞吐高", "会短暂读到旧值；要保证刷新线程"),
    ("永不过期", "无击穿", "要自己管更新与内存"),
]
print(f"  {'方案':<10}{'优点':<20}{'代价'}")
for r in rows:
    print(f"  {r[0]:<10}{r[1]:<20}{r[2]}")

# ---- 关键点 ----
print("\n== 实现要点 ==")
for item in [
    "锁的粒度按 key，不要一把大锁锁全站",
    "锁内双重检查，避免重复回源",
    "等待方可以短暂 sleep 后重试缓存，而不是无限等锁",
    "逻辑过期返回旧值时，要监控刷新失败（避免永远旧数据）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给互斥锁版增加“等待 50ms 后重试缓存”，统计平均延迟。
# 2. 模拟刷新线程失败（DB 抛异常），观察逻辑过期如何降级。
# 3. 用 threading.Semaphore 限制同时回源的请求数为 2。
# 4. 思考：为什么“热点 key”通常不设短 TTL，而用逻辑过期？
