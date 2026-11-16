# ===== 第487课：缓存设计-缓存雪崩 =====
# 知识点：
#   - 缓存雪崩：大量 key 在同一时间集中过期（或缓存服务整体宕机），请求全打到数据库
#   - 与击穿的区别：击穿是“一个热点 key”，雪崩是“一大片 key 同时失效”
#   - 方案 1：TTL 加随机抖动，把过期时间打散
#   - 方案 2：多级缓存（本地 + 分布式），一层失效还有另一层
#   - 方案 3：缓存高可用（集群/主从）、熔断降级（第445/449课）
#   - 方案 4：预热：系统启动/大促前先把热点数据加载进缓存
import random
from collections import Counter


def simulate_expiry(ttl_func, n=1000):
    """模拟 n 个 key 的过期时刻，统计每秒过期数量。"""
    buckets = Counter()
    for _ in range(n):
        expire_at = int(ttl_func())
        buckets[expire_at] += 1
    return buckets


def report(name, buckets):
    peak = max(buckets.values())
    print(f"\n== {name} ==")
    for second in sorted(buckets):
        count = buckets[second]
        bar = "█" * (count // 20)
        print(f"  t={second:2d}s：{count:4d} 个过期 {bar}")
    print(f"  峰值每秒过期 {peak} 个 → 数据库瞬间承受 {peak} 次回源")


random.seed(7)

# ---- 1. 固定 TTL：同一秒集体过期 ----
fixed = simulate_expiry(lambda: 10, n=1000)
report("固定 TTL=10s", fixed)

# ---- 2. 随机抖动：过期时间打散 ----
jittered = simulate_expiry(lambda: 10 + random.uniform(-3, 3), n=1000)
report("TTL=10s ± 3s 抖动", jittered)

print("\n== 对比 ==")
print(f"  固定 TTL 峰值：{max(fixed.values())} / 秒")
print(f"  抖动 TTL 峰值：{max(jittered.values())} / 秒")
print(f"  峰值下降约 {max(fixed.values()) / max(jittered.values()):.0f} 倍")

# ---- 3. 多级缓存兜底 ----
print("\n== 多级缓存：L1 失效还有 L2 ==")


class TwoLevelCache:
    def __init__(self):
        self.l1 = {}                    # 本地缓存（快、容量小）
        self.l2 = {}                    # 分布式缓存（慢一点、容量大）
        self.db_calls = 0
        self.l1_hits = self.l2_hits = 0

    def get(self, key, db_loader):
        if key in self.l1:
            self.l1_hits += 1
            return self.l1[key], "L1"
        if key in self.l2:
            self.l2_hits += 1
            self.l1[key] = self.l2[key]  # 回填 L1
            return self.l2[key], "L2"
        self.db_calls += 1
        value = db_loader(key)
        self.l2[key] = value
        self.l1[key] = value
        return value, "DB"


cache = TwoLevelCache()
for _ in range(100):
    cache.get("hot", lambda k: "商品详情")
print(f"  100 次读取：L1 命中 {cache.l1_hits}，L2 命中 {cache.l2_hits}，"
      f"数据库 {cache.db_calls} 次")

# 模拟 L1 大量过期但 L2 还在
cache.l1.clear()
for _ in range(100):
    cache.get("hot", lambda k: "商品详情")
print(f"  L1 清空后 100 次：L2 命中 {cache.l2_hits - 99}，数据库 {cache.db_calls} 次"
      "（全部由 L2 兜住）")

# ---- 4. 雪崩的连锁反应 ----
print("\n== 雪崩为什么会拖垮系统 ==")
for item in [
    "数据库连接池被瞬间占满 → 其他正常查询也排队",
    "请求超时 → 上游重试 → 流量翻倍（第443课重试风暴）",
    "线程/协程被阻塞 → 整个服务不可用",
    "缓存恢复后，大量请求同时回填，可能再次打满（需要限流）",
]:
    print("  -", item)

# ---- 5. 防御清单 ----
print("\n== 防御清单 ==")
for item in [
    "TTL 加随机抖动（最简单、必做）",
    "多级缓存：本地 + 分布式",
    "缓存集群高可用，避免单点",
    "热点数据预热，大促前提前加载",
    "数据库侧限流 + 熔断降级，保护最后一道防线",
    "缓存宕机时降级返回旧值/默认值（第449课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把抖动范围改成 ±1s / ±5s，比较峰值。
# 2. 给 TwoLevelCache 增加 TTL，模拟 L1/L2 不同过期时间。
# 3. 模拟“缓存服务宕机 5 秒”，用降级策略（返回默认值）统计成功率。
# 4. 思考：为什么“缓存预热”不能只在发布时做一次？
