# ===== 第484课：缓存设计-TTL与过期策略 =====
# 知识点：
#   - TTL（Time To Live）：给缓存设置存活时间，到期自动失效
#   - 惰性删除：访问时发现过期才删（省 CPU，但可能占内存）
#   - 定期删除：后台周期清理（可控内存，但需要线程/任务）
#   - TTL 设计：热点数据长、普通数据短、随机抖动防雪崩（第487课）
#   - 缓存永不过期 + 后台更新是另一种策略（适合极热数据）
#   - 与第421课 LRU 组合：TTL 管“时间”，LRU 管“空间”
import time


class FakeClock:
    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class TTLCache:

    def __init__(self, default_ttl: float = 60.0, clock=None):
        self.default_ttl = default_ttl
        self.clock = clock or time.monotonic
        self.data: dict[str, tuple[object, float]] = {}   # key -> (value, expire_at)
        self.expired_count = 0

    def set(self, key, value, ttl: float | None = None):
        expire_at = self.clock() + (self.default_ttl if ttl is None else ttl)
        self.data[key] = (value, expire_at)

    def get(self, key, default=None):
        item = self.data.get(key)
        if item is None:
            return default
        value, expire_at = item
        if self.clock() >= expire_at:
            del self.data[key]          # 惰性删除：访问时才发现
            self.expired_count += 1
            print(f"    [过期] {key}")
            return default
        return value

    def cleanup(self) -> int:
        """定期删除：主动扫描所有键。"""
        now = self.clock()
        expired = [k for k, (_, exp) in self.data.items() if now >= exp]
        for k in expired:
            del self.data[k]
        self.expired_count += len(expired)
        return len(expired)

    def ttl(self, key) -> float | None:
        item = self.data.get(key)
        if item is None:
            return None
        return max(0.0, item[1] - self.clock())

    def __len__(self):
        return len(self.data)


print("== 惰性删除 ==")
clock = FakeClock()
cache = TTLCache(default_ttl=10, clock=clock)
cache.set("a", "A")
cache.set("b", "B", ttl=3)
print("  t=0 读取 a：", cache.get("a"), "| b 剩余 TTL：", cache.ttl("b"))
clock.advance(4)
print("  t=4 读取 b：", cache.get("b"), "（已过期并被删除）")
print("  当前键：", list(cache.data), "| 过期计数：", cache.expired_count)

print("\n== 定期删除 ==")
clock2 = FakeClock()
cache2 = TTLCache(default_ttl=10, clock=clock2)
for i in range(5):
    cache2.set(f"k{i}", i, ttl=1 if i < 3 else 100)
clock2.advance(2)
print("  清理前键数：", len(cache2))
removed = cache2.cleanup()
print(f"  主动清理 {removed} 个，剩余键：{list(cache2.data)}")

# ---- TTL 设计表 ----
print("\n== TTL 设计参考 ==")
rows = [
    ("商品详情", "5~30 分钟", "价格变动可接受短延迟"),
    ("用户会话", "30 分钟~7 天", "安全与体验平衡"),
    ("验证码", "5 分钟", "安全要求"),
    ("热点榜单", "1~5 分钟", "更新频繁"),
    ("静态配置", "1 小时~1 天", "变化少"),
]
print(f"  {'数据':<10}{'TTL':<16}{'理由'}")
for r in rows:
    print(f"  {r[0]:<10}{r[1]:<16}{r[2]}")

# ---- TTL + 随机抖动：防雪崩预览 ----
print("\n== TTL 抖动（第487课预告）==")
import random
random.seed(1)
base = 300
print("  固定 TTL：", [base] * 8)
print("  抖动 TTL：", [base + random.randint(-30, 30) for _ in range(8)])
print("  同一批写入的缓存不要在同一秒集体过期")

# ---- 过期策略对比 ----
print("\n== 策略对比 ==")
for item in [
    "惰性删除：实现简单、开销低；内存可能被冷数据占着",
    "定期删除：内存可控；扫描频率要调，太频繁耗 CPU",
    "生产常用：惰性 + 定期 组合，Redis 就是这么做的",
    "永不过期 + 后台更新：无过期抖动，但要自己保证一致性",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 实现 LRU + TTL 组合：先按 TTL 淘汰，再按容量淘汰。
# 2. 给 TTLCache 增加“最大容量”，满了淘汰最早过期的键。
# 3. 模拟 1000 个键同时写入，比较固定 TTL 与抖动 TTL 的过期分布。
# 4. 思考：为什么“缓存永不过期”在高并发下反而可能更简单？
