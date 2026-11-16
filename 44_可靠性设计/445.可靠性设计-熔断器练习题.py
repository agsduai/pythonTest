# ===== 第445课：可靠性设计-熔断器 =====
# 知识点：
#   - 熔断器：下游连续失败到阈值 → 直接拒绝请求（快速失败），不再傻等
#   - 三态：CLOSED（正常）→ OPEN（熔断）→ HALF_OPEN（试探恢复）
#   - 好处：保护自己（不耗尽线程/连接）、给下游恢复时间
#   - 与重试的关系：重试解决偶发失败，熔断解决持续故障
#   - 参数：失败阈值、统计窗口、恢复等待时间、半开试探次数
import time


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:

    def __init__(self, failure_threshold=3, recovery_timeout=0.5, clock=time.monotonic):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.clock = clock
        self.state = "CLOSED"
        self.failures = 0
        self.opened_at = 0.0
        self.successes_in_half_open = 0

    def _now(self):
        return self.clock()

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            elapsed = self._now() - self.opened_at
            if elapsed < self.recovery_timeout:
                raise CircuitOpenError(
                    f"熔断中：还需等待 {self.recovery_timeout - elapsed:.2f}s"
                )
            self.state = "HALF_OPEN"
            self.successes_in_half_open = 0
            print("  [状态] OPEN → HALF_OPEN（开始试探）")

        try:
            result = func(*args, **kwargs)
        except Exception:
            self.failures += 1
            if self.state == "HALF_OPEN":
                self._trip()
            elif self.failures >= self.failure_threshold:
                self._trip()
            else:
                print(f"  [失败] 累计 {self.failures}/{self.failure_threshold}")
            raise
        else:
            if self.state == "HALF_OPEN":
                self.successes_in_half_open += 1
                if self.successes_in_half_open >= 1:
                    self.state = "CLOSED"
                    self.failures = 0
                    print("  [状态] HALF_OPEN → CLOSED（下游已恢复）")
            else:
                self.failures = 0
            return result

    def _trip(self):
        self.state = "OPEN"
        self.opened_at = self._now()
        print(f"  [状态] → OPEN（失败 {self.failures} 次，暂停请求 "
              f"{self.recovery_timeout}s）")


# ---- 演示：下游先故障，后恢复 ----
class FlakyService:
    def __init__(self):
        self.healthy = False
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if not self.healthy:
            raise ConnectionError("下游服务不可用")
        return "ok"


service = FlakyService()
breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=0.3)

print("== 阶段 1：下游故障 ==")
for i in range(5):
    try:
        breaker.call(service)
    except (ConnectionError, CircuitOpenError) as exc:
        print(f"  请求 {i + 1}: {type(exc).__name__} - {exc}")
    print(f"    真实调用次数：{service.calls}")

print("\n== 阶段 2：等待恢复窗口后，下游仍故障 ==")
time.sleep(0.35)
try:
    breaker.call(service)
except (ConnectionError, CircuitOpenError) as exc:
    print("  试探失败：", type(exc).__name__)

print("\n== 阶段 3：下游恢复，试探成功 ==")
service.healthy = True
time.sleep(0.35)
print("  调用结果：", breaker.call(service))
print("  调用结果：", breaker.call(service))
print("  最终状态：", breaker.state, "| 真实调用总数：", service.calls)

# ---- 参数选择建议 ----
print("\n== 参数建议 ==")
for item in [
    "失败阈值：太小会误熔断，太大会拖垮自己（常见 5~20 次或 50% 失败率）",
    "恢复等待：根据下游重启/扩容时间设定（常见 10~60 秒）",
    "半开试探：只放少量请求，成功若干次才完全恢复",
    "按依赖分别建熔断器：A 挂了不该影响 B（舱壁，第449课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 CircuitBreaker 加“半开最多试 3 次”的控制。
# 2. 用滑动窗口统计失败率（比如最近 20 次中失败 50% 才熔断）。
# 3. 把熔断器接到第443课 retry 外层：先判熔断，再决定是否重试。
# 4. 思考：熔断器打开时，业务应该返回什么给用户？
