# ===== 第636课：定时任务与调度系统-固定间隔与抖动 =====
# 知识点：
#   - fixed-rate：按固定起点 + n×interval 排期，不受单次执行时长影响
#   - fixed-delay：每次执行结束后再等 interval，节奏会随耗时漂移
#   - 抖动 jitter：给触发时间加随机偏移，避免「惊群」（thundering herd）
#   - 全抖动 vs 有界抖动：randrange 全窗口 / ±jitter 比例
#   - 用可注入的 clock 与 rng，让调度逻辑完全确定、可单测，不真实 sleep
#   - 错过触发（missed fire）：时钟跳跃或阻塞后的补偿策略要显式定义
# 依赖：无（标准库）
import random
from dataclasses import dataclass, field


@dataclass
class Clock:
    """可注入的虚拟时钟，单位秒。"""
    now: float = 0.0

    def advance(self, seconds):
        self.now += seconds

    def __call__(self):
        return self.now


@dataclass
class Schedule:
    interval: float
    start: float = 0.0
    last: float | None = None
    ticks: list = field(default_factory=list)


def fixed_rate_next(sched: Schedule, clock: Clock) -> float:
    """下一次 = 起点 + ceil((now-start)/interval) * interval。"""
    import math
    n = max(0, math.floor((clock() - sched.start) / sched.interval) + 1)
    return sched.start + n * sched.interval


def fixed_delay_next(sched: Schedule, clock: Clock, last_duration: float = 0.0) -> float:
    """下一次 = 上次执行结束时刻 + interval（首次从 start 起算）。"""
    base = sched.last if sched.last is not None else sched.start
    return base + sched.interval


def with_jitter(t: float, jitter: float, rng, mode="bounded") -> float:
    if jitter <= 0:
        return t
    if mode == "full":
        return t + rng.uniform(0, jitter)
    return t + rng.uniform(-jitter, jitter)


print("== fixed-rate：任务耗时不改变排期 ==")
clock = Clock()
sched = Schedule(interval=10)
for duration in (0, 3, 8, 1):
    t = fixed_rate_next(sched, clock)
    print(f"  now={clock():>5.1f}  下次触发={t:>5.1f}  本次耗时={duration}")
    sched.ticks.append(t)
    clock.advance(duration)
    sched.last = clock()
print("  触发序列:", sched.ticks, "（始终落在 10 的倍数上）")

print("\n== fixed-delay：耗时把节奏往后推 ==")
clock = Clock()
sched = Schedule(interval=10)
fires = []
for duration in (0, 3, 8, 1):
    t = fixed_delay_next(sched, clock, duration)   # 上次结束 + interval
    fires.append(round(t, 1))
    finish = t + duration                          # 本次执行结束时刻
    clock.now = finish
    sched.last = finish
print("  触发序列:", fires, "（相邻间隔 = 10 + 上次耗时，节奏逐渐后移）")
print("  相邻间隔:", [round(b - a, 1) for a, b in zip(fires, fires[1:])])

print("\n== 抖动：1000 个客户端分散到 60s 窗口 ==")
rng = random.Random(42)
base_times = [0.0] * 1000
full = [with_jitter(t, 60, rng, "full") for t in base_times]
bounded = [with_jitter(t + 30, 15, rng, "bounded") for t in base_times]
import statistics
print(f"  无抖动     : 全部在 t=0，标准差={statistics.pstdev(base_times):.1f}")
print(f"  全抖动     : 范围 [{min(full):.1f},{max(full):.1f}] 标准差={statistics.pstdev(full):.1f}")
print(f"  有界±15s   : 范围 [{min(bounded):.1f},{max(bounded):.1f}] 标准差={statistics.pstdev(bounded):.1f}")

buckets = [0] * 6
for t in full:
    buckets[min(5, int(t // 10))] += 1
print("  每 10s 桶内客户端数:", buckets, "（不再瞬间全打过来）")

print("\n== 可复现性：同一 seed 得到同一序列 ==")
a = [round(with_jitter(0, 5, random.Random(7), "full"), 3) for _ in range(5)]
b = [round(with_jitter(0, 5, random.Random(7), "full"), 3) for _ in range(5)]
print("  ", a, "==", b, "->", a == b)

print("\n== 错过触发（时钟跳跃）==")
clock = Clock(0)
sched = Schedule(interval=10)
clock.advance(95)        # 模拟进程卡了 95 秒
due = []
n = 0
while sched.start + n * sched.interval <= clock():
    t = sched.start + n * sched.interval
    due.append(t)
    n += 1
print(f"  跳跃到 now={clock()}，累计应触发 {len(due)} 次")
print("  补偿策略:")
for line in (
    "  - now: 立刻补跑全部遗漏（可能洪峰）",
    "  - one: 只补跑最近一次（常用，防重复）",
    "  - skip: 直接丢弃，按未来排期继续（最安全）",
):
    print(line)
print("  选 skip 后下一次触发:", fixed_rate_next(sched, clock))

print("\n== 工程要点 ==")
for line in [
    "监控/心跳用 fixed-rate（Tick 不能漂），批处理用 fixed-delay（不重叠）",
    "所有分布式客户端都要独立 jitter，且种子不能相同",
    "单测注入 Clock 与 Random，绝不 time.sleep 真等待",
    "跨主机仍需时钟同步（NTP），否则 rate 与 delay 都会偏",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 should_run(sched, clock) 并支持 skip/one/now 三种错过补偿策略。
# 2. 给 jitter 加「比例抖动」模式：偏移 = interval × ratio × uniform(-1,1)。
# 3. 模拟 5000 台机器，对比无抖动/全抖动的峰值 QPS。
# 4. 思考：为什么 fixed-rate 在任务变慢时可能产生「重叠执行」？
