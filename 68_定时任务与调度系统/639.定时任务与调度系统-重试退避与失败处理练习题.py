# ===== 第639课：定时任务与调度系统-重试退避与失败处理 =====
# 知识点：
#   - 重试要配「退避」：固定 / 线性 / 指数 / 指数+抖动，避免打垮下游
#   - 指数退避公式：delay = base × 2^(attempt-1)，用 cap 封顶
#   - 全抖动 decorrelated jitter 能显著削平重试洪峰
#   - 只重试「可恢复错误」（超时、5xx、连接断开），4xx 参数错误不该重试
#   - 记录每次尝试：序号、延迟、结果、总耗时；用可注入 clock/rng/sleeper 做单测
#   - 超过 max_attempts 进入死信/告警，交由人工或补偿任务处理（第53章）
# 依赖：无（标准库）
import random
from dataclasses import dataclass, field

RETRYABLE = {"TimeoutError", "ConnectionError", "ServiceUnavailable"}
PERMANENT = {"ValueError", "ValidationError", "PermissionError"}


def compute_delays(kind, n, base=1.0, cap=60.0, rng=None):
    """返回前 n 次重试的延迟列表（秒），不真实等待。"""
    rng = rng or random.Random(0)
    out = []
    for i in range(1, n + 1):
        if kind == "fixed":
            d = base
        elif kind == "linear":
            d = base * i
        elif kind == "exponential":
            d = min(cap, base * (2 ** (i - 1)))
        elif kind == "exp_jitter":
            d = rng.uniform(0, min(cap, base * (2 ** (i - 1))))
        elif kind == "decorrelated":
            prev = out[-1] if out else base
            d = min(cap, rng.uniform(base, prev * 3))
        else:
            raise ValueError(kind)
        out.append(round(d, 3))
    return out


@dataclass
class Attempt:
    n: int
    delay: float
    error: str | None
    ok: bool


@dataclass
class Result:
    attempts: list = field(default_factory=list)
    succeeded: bool = False
    total_delay: float = 0.0

    @property
    def final_state(self):
        return "DONE" if self.succeeded else "DEAD_LETTER"


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def sleep(self, seconds):
        self.sleeps.append(round(seconds, 3))
        self.now += seconds


def run_with_retry(work, *, kind="exponential", max_attempts=5, base=1.0,
                   cap=30.0, rng=None, clock=None):
    """work() 返回成功值或抛异常；返回 Result，全程不真实等待。"""
    rng = rng or random.Random(0)
    clock = clock or FakeClock()
    result = Result()
    delays = compute_delays(kind, max_attempts - 1, base, cap, rng)
    for attempt in range(1, max_attempts + 1):
        # delays[0] 是「第 1 次失败后、第 2 次尝试前」的等待；最后一次尝试无需等待
        delay = delays[attempt - 2] if 1 < attempt <= len(delays) + 1 else 0.0
        if delay:
            clock.sleep(delay)
            result.total_delay += delay
        try:
            work(attempt)
            result.attempts.append(Attempt(attempt, delay, None, True))
            result.succeeded = True
            break
        except Exception as e:
            name = type(e).__name__
            result.attempts.append(Attempt(attempt, delay, name, False))
            if name in PERMANENT:
                break                       # 不可恢复，立刻停止
            if name not in RETRYABLE and not name.endswith("Error"):
                # 未知异常默认允许重试，便于演示
                pass
    return result


print("== 四种退避策略的延迟序列 ==")
for kind in ("fixed", "linear", "exponential", "exp_jitter", "decorrelated"):
    d = compute_delays(kind, 6, base=1, cap=20, rng=random.Random(42))
    print(f"  {kind:<14} {d}  合计={sum(d):.1f}s")

print("\n== 指数退避封顶 ==")
print("  cap=10, base=2:", compute_delays("exponential", 8, base=2, cap=10))

print("\n== 抖动削峰：200 个客户端同时失败 ==")
import statistics
for kind in ("exponential", "exp_jitter"):
    first = [compute_delays(kind, 1, base=1, cap=30, rng=random.Random(i))[0]
             for i in range(200)]
    print(f"  {kind:<14} 首次重试: min={min(first):.2f} max={max(first):.2f} "
          f"标准差={statistics.pstdev(first):.2f}")

print("\n== 成功路径：第 3 次才成功 ==")
clock = FakeClock()
def flaky(n):
    if n < 3:
        raise TimeoutError("downstream timeout")
    return "ok"

r = run_with_retry(flaky, kind="exponential", base=2, max_attempts=5, clock=clock)
for a in r.attempts:
    print(f"  第 {a.n} 次: 延迟={a.delay:>5}s 错误={a.error or '无'} 成功={a.ok}")
print(f"  最终={r.final_state} 总等待={r.total_delay}s sleeps={clock.sleeps}")

print("\n== 永久错误：不重试 ==")
def bad(n):
    raise ValueError("参数非法")

r2 = run_with_retry(bad, max_attempts=5, clock=(c2 := FakeClock()))
print(f"  尝试次数={len(r2.attempts)}（应为 1）  最终={r2.final_state}  sleeps={c2.sleeps}")
print("  4xx / 参数校验 / 权限错误直接失败，重试只会浪费配额")

print("\n== 全部失败：进死信 ==")
def always(n):
    raise ConnectionError("network down")
r3 = run_with_retry(always, kind="linear", max_attempts=4, base=3,
                    clock=(c3 := FakeClock()))
print(f"  尝试次数={len(r3.attempts)}  最终={r3.final_state}  总等待={r3.total_delay}s")
print("  处理：写死信队列 + 告警 + 人工/补偿任务，不要静默丢弃")

print("\n== 退避选型建议 ==")
for line in [
    "内部 RPC 短暂抖动：指数 + 全抖动，base=100ms~1s",
    "外部限流 API：尊重 Retry-After 头，别自己猜",
    "批处理大任务：固定/线性退避更好预测完成时间",
    "永远设 cap 与 max_attempts，防止无限重试",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「尊重 Retry-After」的退避：异常携带服务端建议秒数时优先采用。
# 2. 给 run_with_retry 增加 on_failure 回调，用于写死信队列与打点。
# 3. 模拟 1000 客户端对比「无抖动 vs 全抖动」在 t=1s 的并发重试数。
# 4. 思考：为什么「未知异常默认重试」在生产里可能是危险的？
