# ===== 第446课：可靠性设计-限流器 =====
# 知识点：
#   - 限流：保护自己不被突发流量打垮，也保护下游（第201课 Semaphore 的进阶）
#   - 令牌桶：固定速率补充令牌，容量允许短时突发（最常用）
#   - 漏桶：固定速率流出，天然平滑，不允许突发
#   - 滑动窗口日志：记录时间戳，统计窗口内请求数，精确但有内存成本
#   - 关键设计：时钟可注入 —— 便于测试，不用真的 sleep
from collections import deque
import time


class FakeClock:
    """可控时钟：测试限流逻辑时不用真的等待。"""

    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


# ---------------- 1. 令牌桶 ----------------
class TokenBucket:

    def __init__(self, rate: float, capacity: int, clock=None):
        """rate: 每秒补充令牌数；capacity: 桶容量（允许的突发量）。"""
        self.rate = rate
        self.capacity = capacity
        self.clock = clock or time.monotonic
        self.tokens = float(capacity)
        self.last = self.clock()

    def allow(self, tokens: int = 1) -> bool:
        now = self.clock()
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
        self.last = now
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


print("== 令牌桶：rate=2/s，容量=3 ==")
clock = FakeClock()
bucket = TokenBucket(rate=2, capacity=3, clock=clock)
print("  初始 3 个令牌，连续请求 5 次：")
for i in range(5):
    ok = bucket.allow()
    print(f"    第 {i + 1} 次：{'通过' if ok else '拒绝'}（剩余 {bucket.tokens:.1f}）")
print("  时间前进 0.5s（补 1 个令牌）：")
clock.advance(0.5)
print("    请求：", "通过" if bucket.allow() else "拒绝", f"（剩余 {bucket.tokens:.1f}）")
print("  时间前进 1s（补 2 个）：")
clock.advance(1)
for i in range(3):
    print(f"    请求 {i + 1}：", "通过" if bucket.allow() else "拒绝",
          f"（剩余 {bucket.tokens:.1f}）")


# ---------------- 2. 漏桶（固定速率放行）----------------
class LeakyBucket:

    def __init__(self, rate: float, capacity: int, clock):
        self.rate = rate
        self.capacity = capacity
        self.clock = clock
        self.water = 0.0
        self.last = clock()

    def allow(self) -> bool:
        now = self.clock()
        self.water = max(0.0, self.water - (now - self.last) * self.rate)
        self.last = now
        if self.water + 1 <= self.capacity:
            self.water += 1
            return True
        return False


print("\n== 漏桶：rate=1/s，容量=2 ==")
clock2 = FakeClock()
leaky = LeakyBucket(rate=1, capacity=2, clock=clock2)
for i in range(5):
    print(f"  第 {i + 1} 次：", "通过" if leaky.allow() else "拒绝",
          f"（水位 {leaky.water:.1f}）")
clock2.advance(1)
print("  1s 后：", "通过" if leaky.allow() else "拒绝", f"（水位 {leaky.water:.1f}）")


# ---------------- 3. 滑动窗口日志 ----------------
class SlidingWindowLimiter:

    def __init__(self, limit: int, window: float, clock):
        self.limit = limit
        self.window = window
        self.clock = clock
        self.log: deque[float] = deque()

    def allow(self) -> bool:
        now = self.clock()
        while self.log and self.log[0] <= now - self.window:
            self.log.popleft()                # 淘汰窗口外的请求
        if len(self.log) >= self.limit:
            return False
        self.log.append(now)
        return True


print("\n== 滑动窗口：每 1s 最多 3 次 ==")
clock3 = FakeClock()
window = SlidingWindowLimiter(limit=3, window=1.0, clock=clock3)
for t in (0.0, 0.1, 0.2, 0.3, 0.9, 1.05, 1.1):
    clock3.now = t
    print(f"  t={t:.2f}s：", "通过" if window.allow() else "拒绝")

# ---------------- 对比 ----------------
print("\n== 三种算法对比 ==")
rows = [
    ("令牌桶", "允许突发到容量", "需要存令牌数", "API 网关常用"),
    ("漏桶", "输出绝对平滑", "需要存水位", "流量整形"),
    ("滑动窗口", "统计精确", "存时间戳，内存较高", "按用户/IP 限流"),
]
print(f"  {'算法':<8}{'特点':<14}{'成本':<18}{'典型场景'}")
for row in rows:
    print(f"  {row[0]:<8}{row[1]:<14}{row[2]:<18}{row[3]}")

# ===== 练习题 =====
# 1. 实现“按用户限流”：每个 user_id 一个令牌桶（dict + 懒创建）。
# 2. 给第410课的 API 加限流中间件，超过返回 429。
# 3. 用滑动窗口实现“每分钟最多 100 次”的登录尝试限制。
# 4. 思考：限流阈值应该由谁决定？压测数据怎么用？
