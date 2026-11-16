# ===== 第490课：缓存设计-综合案例-商品详情缓存 =====
# 知识点：
#   - 综合运用：Cache-Aside（483）+ TTL（484）+ 空值缓存（485）
#     + 互斥锁（486）+ 多级缓存（489）+ 失效（488）
#   - 读流程：L1 → L2 → 加锁回源 → 回填两级；不存在则缓存空值
#   - 写流程：更新 DB → 删除 L2 → 删除 L1
#   - 指标：命中率、数据库调用次数、平均延迟、空值命中
#   - 目标：在模拟流量下，把数据库调用压到最低且不返回脏数据
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor


class LRUCache:
    def __init__(self, capacity=50):
        self.capacity = capacity
        self.data = OrderedDict()

    def get(self, key):
        if key not in self.data:
            return None
        self.data.move_to_end(key)
        return self.data[key]

    def put(self, key, value):
        if key in self.data:
            self.data[key] = value
            self.data.move_to_end(key)
            return
        if len(self.data) >= self.capacity:
            self.data.popitem(last=False)
        self.data[key] = value

    def delete(self, key):
        self.data.pop(key, None)


class FakeDB:
    def __init__(self):
        self.data = {f"p{i}": f"商品{i}" for i in range(1, 11)}
        self.reads = 0
        self.writes = 0
        self.read_delay = 0.005

    def get(self, key):
        self.reads += 1
        time.sleep(self.read_delay)        # 模拟慢查询
        return self.data.get(key)

    def set(self, key, value):
        self.writes += 1
        self.data[key] = value


class ProductCache:

    def __init__(self, negative_ttl=2.0):
        self.l1 = LRUCache(capacity=10)
        self.l2 = {}                       # key -> (value, expire_at)
        self.db = FakeDB()
        self.lock = threading.Lock()
        self.negative_ttl = negative_ttl
        self.stats = {"L1": 0, "L2": 0, "DB": 0, "negative": 0}

    def _l2_get(self, key):
        item = self.l2.get(key)
        if item is None:
            return None
        value, expire_at = item
        if time.monotonic() >= expire_at:
            self.l2.pop(key, None)
            return None
        return value

    def get(self, key):
        # 1) L1
        value = self.l1.get(key)
        if value is not None:
            self.stats["L1"] += 1
            if value == "__NULL__":
                self.stats["negative"] += 1
                return None
            return value

        # 2) L2
        value = self._l2_get(key)
        if value is not None:
            self.stats["L2"] += 1
            self.l1.put(key, value)
            if value == "__NULL__":
                self.stats["negative"] += 1
                return None
            return value

        # 3) 回源（互斥 + 双重检查）
        with self.lock:
            value = self.l1.get(key)
            if value is None:
                value = self._l2_get(key)
            if value is None:
                self.stats["DB"] += 1
                value = self.db.get(key)
                ttl = self.negative_ttl if value is None else 60.0
                stored = value if value is not None else "__NULL__"
                self.l2[key] = (stored, time.monotonic() + ttl)
                self.l1.put(key, stored)
                if value is None:
                    self.stats["negative"] += 1
                    return None
                return value

        if value == "__NULL__":
            self.stats["negative"] += 1
            return None
        return value

    def update(self, key, value):
        self.db.set(key, value)
        self.l2.pop(key, None)
        self.l1.delete(key)

    def hit_rate(self):
        total = self.stats["L1"] + self.stats["L2"] + self.stats["DB"]
        if total == 0:
            return 0.0
        hits = self.stats["L1"] + self.stats["L2"]
        return hits / total


cache = ProductCache()

# ---------------- 1. 并发读：热 key + 普通 key + 不存在的 key ----------------
print("== 200 个并发请求 ==")
keys = ["p1"] * 80 + ["p2"] * 50 + [f"p{i}" for i in range(3, 8)] * 10 + ["missing"] * 20
start = time.perf_counter()
with ThreadPoolExecutor(max_workers=20) as pool:
    results = list(pool.map(cache.get, keys))
cost = time.perf_counter() - start

print(f"  总请求 {len(keys)}，耗时 {cost:.2f}s")
print(f"  数据库读取 {cache.db.reads} 次（无缓存时需 {len(keys)} 次）")
print(f"  命中率 {cache.hit_rate():.1%} | 空值命中 {cache.stats['negative']} 次")
print("  结果样例：p1 →", results[0], "| missing →", results[-1])

# ---------------- 2. 更新后一致性 ----------------
print("\n== 更新商品价格 ==")
cache.update("p1", "商品1（新价格）")
value = cache.get("p1")
print("  更新后读取：", value)
print("  数据库写入次数：", cache.db.writes)
print("  说明：更新删除了两级缓存，下次读回源拿到新值")

# ---------------- 3. 不存在的商品：只穿透一次 ----------------
print("\n== 不存在的商品 ==")
before = cache.db.reads
for _ in range(30):
    cache.get("ghost")
print(f"  30 次查询 ghost → 数据库新增调用 {cache.db.reads - before} 次（空值已缓存）")

# ---------------- 4. 指标报告 ----------------
print("\n== 指标报告 ==")
print("  统计：", cache.stats)
print(f"  命中率：{cache.hit_rate():.1%}")
print(f"  数据库读取：{cache.db.reads} 次（原始请求 {len(keys) + 30 + 1} 次）")
print(f"  数据库写入：{cache.db.writes} 次")

print("\n== 优化前后对比（理论）==")
raw_calls = len(keys) + 30 + 1
print(f"  无缓存：约 {raw_calls} 次数据库读")
print(f"  本方案：{cache.db.reads} 次，降低到 {cache.db.reads / raw_calls:.1%}")

# ---- 生产落地清单 ----
print("\n== 落地清单 ==")
for item in [
    "L1 用 LRU + 短 TTL，注意多实例失效广播",
    "L2 TTL 加随机抖动（第487课）",
    "空值缓存 TTL 要短（5~30 秒），避免新数据长期 404",
    "热点 key 用互斥锁/逻辑过期防击穿",
    "更新走“先库后删缓存”，必要时延迟双删",
    "监控命中率、DB QPS、P99 延迟（第417课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把 L1 容量改成 3，观察命中率变化。
# 2. 模拟 L2 失效（清空），统计 L1 兜住了多少请求。
# 3. 给 cache 增加“批量预热”方法，启动时加载 Top10 商品。
# 4. 思考：这个实现里还有哪些并发问题？（提示：L1 的 OrderedDict 非线程安全）
