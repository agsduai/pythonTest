# ===== 第489课：缓存设计-多级缓存 =====
# 知识点：
#   - 多级缓存：L1 本地（进程内，纳秒级）+ L2 分布式（Redis 等，毫秒级）+ DB
#   - 读路径：L1 → L2 → DB；L2 命中后回填 L1，DB 命中后回填 L2 与 L1
#   - 写路径：更新 DB → 失效 L2 → 失效 L1（或广播失效）
#   - 本地缓存的问题：多实例之间不一致，需要失效广播/短 TTL
#   - 容量：L1 小（LRU）、L2 大；不同层 TTL 不同
#   - 与第421课 LRU、第484课 TTL、第487课多级兜底配套
from collections import OrderedDict


class LRUCache:
    """L1：容量小、按 LRU 淘汰。"""

    def __init__(self, capacity=3):
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

    def invalidate(self, key):
        self.data.pop(key, None)

    def keys(self):
        return list(self.data)


class FakeRedis:
    """L2：容量大、独立进程（这里用 dict 模拟）。"""

    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value

    def delete(self, key):
        self.data.pop(key, None)

    def keys(self):
        return list(self.data)


class FakeDB:
    def __init__(self):
        self.data = {"p1": "商品1", "p2": "商品2", "p3": "商品3", "p4": "商品4"}
        self.reads = 0
        self.writes = 0

    def get(self, key):
        self.reads += 1
        return self.data.get(key)

    def set(self, key, value):
        self.writes += 1
        self.data[key] = value


class MultiLevelCache:

    def __init__(self, l1_capacity=3):
        self.l1 = LRUCache(l1_capacity)
        self.l2 = FakeRedis()
        self.db = FakeDB()
        self.stats = {"L1": 0, "L2": 0, "DB": 0}

    def get(self, key):
        value = self.l1.get(key)
        if value is not None:
            self.stats["L1"] += 1
            return value, "L1"

        value = self.l2.get(key)
        if value is not None:
            self.stats["L2"] += 1
            self.l1.put(key, value)          # 回填 L1
            return value, "L2"

        self.stats["DB"] += 1
        value = self.db.get(key)
        if value is not None:
            self.l2.set(key, value)          # 回填 L2
            self.l1.put(key, value)          # 回填 L1
        return value, "DB"

    def update(self, key, value):
        self.db.set(key, value)
        self.l2.delete(key)                  # 先失效 L2
        self.l1.invalidate(key)              # 再失效 L1（多实例要广播）
        print(f"    [更新] {key}={value}，两级缓存已失效")

    def invalidate(self, key):
        self.l2.delete(key)
        self.l1.invalidate(key)


cache = MultiLevelCache(l1_capacity=3)

print("== 读取路径演示 ==")
for key in ("p1", "p1", "p2", "p1", "p3", "p4", "p2"):
    value, level = cache.get(key)
    print(f"  get({key}) → {value}（来自 {level}）")

print("\n== 命中统计 ==")
print("  ", cache.stats)
print("  L1 keys：", cache.l1.keys(), "（容量 3，p1 被淘汰）")
print("  L2 keys：", cache.l2.keys())

# ---- 更新后两级都失效 ----
print("\n== 更新数据 ==")
cache.update("p2", "商品2（新价格）")
value, level = cache.get("p2")
print(f"  更新后读取 p2：{value}（来自 {level}）")

# ---- 本地缓存不一致问题 ----
print("\n== 多实例下的 L1 不一致 ==")
print("  实例 A 的 L1 有 p1=旧值；实例 B 更新了 p1 并只失效了自己的 L1")
print("  结果：A 仍会返回旧值，直到 TTL 到期或收到失效广播")
print("  解决：发布订阅广播失效 / L1 设很短 TTL（1~5 秒）")
for item in [
    "广播失效：更新时向所有实例发消息，各自清本地缓存",
    "短 TTL：接受秒级不一致，换取实现简单",
    "版本号：值里带版本，读到旧版本主动丢弃",
]:
    print("  -", item)

# ---- 各层职责 ----
print("\n== 各层职责 ==")
rows = [
    ("L1 本地", "纳秒~微秒", "极小（百~千条）", "极热数据，1~5s TTL"),
    ("L2 分布式", "毫秒", "大（百万级）", "共享缓存，分钟级 TTL"),
    ("DB", "毫秒~百毫秒", "全量", "最终数据源"),
]
print(f"  {'层':<10}{'延迟':<12}{'容量':<18}{'策略'}")
for r in rows:
    print(f"  {r[0]:<10}{r[1]:<12}{r[2]:<18}{r[3]}")

# ===== 练习题 =====
# 1. 给 L1 加 TTL（比如 5 秒），观察命中率与一致性的变化。
# 2. 实现广播失效：模拟 3 个实例，更新时清空所有实例的 L1。
# 3. 统计 1000 次随机读取的 L1/L2/DB 命中率。
# 4. 思考：L1 容量太小会怎样？太大又有什么风险？
