# ===== 第640课：定时任务与调度系统-时窗与补跑 =====
# 知识点：
#   - 数据批处理按「事件时间窗」而非「启动时刻」取数：bucket = floor(ts / size) * size
#   - 水位线 watermark：允许一定迟到，超过水位才认定窗口完成
#   - 补跑 backfill：指定起止窗口，逐窗重算；要幂等（第638课）
#   - 窗口闭开区间 [start, end)，避免相邻窗口重复或漏掉边界数据
#   - 迟到数据：落在已封闭窗口时，触发该窗口的局部重算
#   - 全部用整数秒时间戳 + 可注入数据，纯函数、可单测、无真实 sleep
# 依赖：无（标准库）
from collections import defaultdict
from datetime import datetime, timedelta, timezone

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def ts(dt: datetime) -> int:
    return int((dt - EPOCH).total_seconds())


def to_dt(sec: int) -> datetime:
    return EPOCH + timedelta(seconds=sec)


def window_of(event_ts: int, size: int) -> tuple[int, int]:
    """返回事件所属窗口 [start, end)。"""
    start = (event_ts // size) * size
    return start, start + size


def build_windows(events, size):
    """按窗口聚合事件，events 为 (ts, value)。"""
    buckets = defaultdict(list)
    for t, v in events:
        buckets[window_of(t, size)[0]].append(v)
    return {start: (sum(vals), len(vals)) for start, vals in sorted(buckets.items())}


def backfill(start_dt, end_dt, size, events):
    """逐窗补跑：返回 [(窗口, 总和, 条数)]，与实时聚合结果一致。"""
    out = []
    cur = ts(start_dt)
    end = ts(end_dt)
    while cur < end:
        vals = [v for t, v in events if cur <= t < cur + size]
        out.append((cur, sum(vals), len(vals)))
        cur += size
    return out


print("== 窗口归属（5 分钟窗）==")
SIZE = 300
base = datetime(2026, 11, 14, 9, 0, tzinfo=timezone.utc)
for delta in (0, 299, 300, 301, 899, 900):
    t = ts(base) + delta
    a, b = window_of(t, SIZE)
    print(f"  +{delta:>4}s -> [{to_dt(a):%H:%M}, {to_dt(b):%H:%M})")

print("\n== 闭开区间避免边界重复 ==")
t = ts(base) + SIZE
a1, b1 = window_of(t - 1, SIZE)
a2, b2 = window_of(t, SIZE)
print(f"  t-1={b1} 属于 [{a1},{b1})；t={a2} 属于 [{a2},{b2})；b1 == a2: {b1 == a2}")

events = []
for i in range(20):
    events.append((ts(base) + i * 97, i + 1))     # 跨多个 5 分钟窗
print("\n== 实时聚合 ==")
live = build_windows(events, SIZE)
for start, (total, count) in live.items():
    print(f"  [{to_dt(start):%H:%M}, {to_dt(start+SIZE):%H:%M})  和={total:>3} 条数={count}")

print("\n== 补跑同一区间（结果应完全一致）==")
bf = backfill(base, base + timedelta(minutes=20), SIZE, events)
for start, total, count in bf:
    match = live.get(start, (0, 0)) == (total, count)
    print(f"  [{to_dt(start):%H:%M})  和={total:>3} 条数={count}  与实时一致={match}")
print("  全部一致:", all(live.get(s, (0, 0)) == (t, c) for s, t, c in bf))

print("\n== 水位线与迟到数据 ==")
watermark = ts(base) + SIZE * 2
late = (ts(base) + 10, 999)     # 迟到事件，落在已封闭的第 0 个窗口
closed = watermark - 3 * SIZE  # 早于该窗口的都已封闭
late_start, _ = window_of(late[0], SIZE)
print(f"  当前水位线: {to_dt(watermark):%H:%M}")
print(f"  迟到事件属于窗口 {to_dt(late_start):%H:%M}，已封闭={late_start < closed}")
if late_start < closed:
    old_total = live.get(late_start, (0, 0))[0]
    print(f"  触发局部重算：{old_total} -> {old_total + late[1]}，并标记该窗口版本 +1")
else:
    print("  仍在允许迟到范围内，正常并入当前窗口")

print("\n== 水位线延迟与「 completeness / latency 」权衡 ==")
for lag_min in (0, 5, 15, 60):
    print(f"  允许迟到 {lag_min:>2} 分钟 -> 结果更完整，但产出延迟 {lag_min} 分钟")

print("\n== DST / 时区注意（对接第605课）==")
print("  窗口用 UTC 整数秒计算，展示时才转本地时区")
print("  若按本地墙上时间分窗，秋季重复 1 点会导致同窗两批数据")
print("  窗口边界一律用 aware datetime 转 UTC 时间戳")

print("\n== 工程要点 ==")
for line in [
    "窗口大小按业务选：分钟级监控、小时级报表、天级账单",
    "补跑必须幂等：覆盖写同一分区，而不是 append",
    "记录每个窗口的 run_id / 版本号，方便审计与回放",
    "迟到数据超水位线时走「修正流」，不要阻塞主链路",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现滑动窗口（size=300, slide=60），统计每个窗口的去重用户数。
# 2. 给 backfill 增加「只补跑失败窗口」参数，跳过已成功的窗口。
# 3. 用版本号实现窗口结果覆盖写，验证重复补跑不会产生重复行。
# 4. 思考：为什么按事件时间分窗，比按「任务启动时间」取数更可靠？
