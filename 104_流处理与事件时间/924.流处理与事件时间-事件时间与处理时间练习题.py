# ===== 第924课：流处理与事件时间-事件时间与处理时间 =====
# 知识点：
#   - 事件时间：业务发生时刻（写在事件里）；处理时间：系统收到时刻
#   - 网络延迟/重试/离线补传 → 两者必然存在偏差（event-time skew）
#   - 按处理时间统计：结果随到达顺序漂移；按事件时间：需要处理乱序
#   - 乱序是常态而非异常：移动网络、时钟漂移、批量补传
#   - 与 88 章的区别：88 是流的摘要统计，本章是流的时序语义
# 依赖：无（标准库）
import math
import random
from collections import defaultdict


def make_stream(rng, n=40, skew=8):
    """生成带乱序的流：(处理时间, 事件时间, value)。处理时间 = 到达顺序。"""
    events = [(t, round(math.sin(t / 5) * 10 + 10 + rng.gauss(0, 2), 1))
              for t in range(n)]
    arrived = []
    for et, val in events:
        delay = rng.randint(0, skew)        # 网络延迟造成的乱序
        arrived.append((et + delay, et, val))
    arrived.sort(key=lambda x: x[0])        # 按处理时间排序（到达顺序）
    return [(pt, et, val) for pt, et, val in arrived]


def window_by(arrival_ordered, time_key, width=10):
    """按指定时间维度做 10 秒滚动窗口。"""
    buckets = defaultdict(list)
    for pt, et, val in arrival_ordered:
        t = time_key(pt, et)
        buckets[t // width * width].append(val)
    return {k: round(sum(v) / len(v), 2) for k, v in sorted(buckets.items())}


def max_skew(arrival_ordered):
    return max(pt - et for pt, et, _ in arrival_ordered)


rng = random.Random(111)
stream = make_stream(rng)

print("== 流样本（前 10 条）==")
print(f"  {'处理时间':>8}{'事件时间':>10}{'值':>8}{'偏差':>6}")
for pt, et, val in stream[:10]:
    print(f"  {pt:>8}{et:>10}{val:>8}{pt - et:>6}")
print(f"  最大乱序偏差 = {max_skew(stream)} 个时间单位")

print("\n== 两种时间的窗口结果对比 ==")
by_et = window_by(stream, lambda pt, et: et)
by_pt = window_by(stream, lambda pt, et: pt)
print(f"  {'窗口起点':>10}{'按事件时间':>12}{'按处理时间':>12}")
for k in sorted(set(by_et) | set(by_pt)):
    print(f"  {k:>10}{by_et.get(k, '-')!s:>12}{by_pt.get(k, '-')!s:>12}")
diff_keys = [k for k in set(by_et) | set(by_pt)
             if by_et.get(k) != by_pt.get(k)]
print(f"  结果不同的窗口数 = {len(diff_keys)} / {len(set(by_et) | set(by_pt))}")
print("  乱序让『处理时间窗口』把旧事件的值记到了新窗口 —— 业务上通常不可接受")

print("\n== 乱序对『求和正确性』的影响 ==")
total = round(sum(v for _, _, v in stream), 2)
print(f"  全流总和 = {total}（与选哪种时间无关 —— 只有『窗口』才有记到哪的问题）")
print("  但『某窗口的值』在两种时间下不同 —— 窗口语义必须明确选边")

print("\n== 事件时间窗口的『不完整』问题 ==")
print("  按事件时间分桶时，处理时间已经走到 40，")
print("  但可能还有事件时间 < 40 的迟到事件在路上（如 et=12, v=99 之类）")
print("  若此刻就发布窗口结果，迟到事件的到来会让已发布结果失效")
print("  → 需要一个『可以关窗』的判据 —— 下一课的水印（watermark）")

print("\n== 事件时间选择的工程准则 ==")
for line in (
    "  计费/审计/报表：用事件时间（业务事实以发生时刻为准）",
    "  监控告警/负载评估：常用处理时间（关心系统当下）",
    "  混合用法：事件时间聚合 + 处理时间触发",
    "  无论选哪个，乱序处理策略都必须显式设计",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  事件时间与处理时间的偏差是流处理的第一个核心矛盾",
    "  处理时间简单但语义漂移；事件时间正确但要解决『何时关窗』",
    "  乱序程度（skew）是流系统的重要监控指标",
    "  下一课：水印 —— 事件时间世界的进度条",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「偏差分布统计」：P50/P95/P99 偏差，评估乱序严重程度。
# 2. 构造『时钟回拨』场景（事件时间倒退），观察两种窗口的行为差异。
# 3. 实现「双维度聚合」：同时输出事件时间窗口与处理时间窗口的对照表。
# 4. 思考：为什么有些业务必须用事件时间？举一个用处理时间会导致资损的例子。
