# ===== 第925课：流处理与事件时间-水印与乱序处理 =====
# 知识点：
#   - 水印 watermark：单调递增的「事件时间进度条」—— 声明 W 之前的事件应到齐
#   - 生成启发式：W = 已见最大事件时间 − 允许乱序度（bounded-out-of-orderness）
#   - 窗口关闭判据：window_end ≤ watermark → 触发计算并发布
#   - 迟到事件（et < 已发布窗口）：侧输出（side output）单独处理
#   - 水印的权衡：太紧 → 频繁迟到；太松 → 结果延迟高
# 依赖：无（标准库）
import random
from collections import defaultdict


def make_stream(rng, n=30, skew=6):
    events = [(t, t % 7 + 1) for t in range(n)]        # (事件时间, 用户id)
    arrived = []
    for et, uid in events:
        arrived.append((et + rng.randint(0, skew), et, uid))
    arrived.sort()
    return [(pt, et, uid) for pt, et, uid in arrived]


class WatermarkTracker:
    """有界乱序水印：W = max_event_time − allowed_lateness（单调不减）。"""

    def __init__(self, allowed_lateness):
        self.allowed = allowed_lateness
        self.max_et = None
        self.value = None

    def update(self, event_time):
        self.max_et = event_time if self.max_et is None else max(self.max_et, event_time)
        candidate = self.max_et - self.allowed
        if self.value is None or candidate > self.value:
            self.value = candidate
        return self.value


class WindowedCounter:
    """事件时间 5 秒滚动窗口（按 uid 计数），带水印触发与侧输出。"""

    def __init__(self, width=5, allowed_lateness=2):
        self.width = width
        self.tracker = WatermarkTracker(allowed_lateness)
        self.buckets = defaultdict(list)        # 窗口起点 -> [(et, uid)]
        self.emitted = {}                       # 已发布窗口 -> 计数
        self.side_output = []                   # 迟到事件（无法修正已发布窗口）

    def process(self, pt, et, uid):
        wm = self.tracker.update(et)
        window_start = et // self.width * self.width
        self.buckets[window_start].append((et, uid))
        # 关闭所有 window_end ≤ watermark 的窗口
        closed = []
        for start in sorted(self.buckets):
            if start + self.width <= wm and start not in self.emitted:
                self.emitted[start] = len(self.buckets.pop(start))
                closed.append(start)
        # 迟到：事件所属窗口已发布
        if window_start in self.emitted:
            self.side_output.append((pt, et, uid))
        return closed, wm


def rebuild_with_late(emitted, buckets, side_output, width=5):
    """把侧输出事件手工并回窗口，展示『完整事实』。"""
    final = dict(emitted)
    for _, et, uid in side_output:
        start = et // width * width
        final[start] = final.get(start, 0) + 1
    return dict(sorted(final.items()))


rng = random.Random(112)
stream = make_stream(rng)

print("== 流与水印推进 ==")
tracker = WatermarkTracker(2)
print(f"  {'到达':>4}{'事件时间':>8}{'水印':>8}")
for pt, et, uid in stream[:12]:
    wm = tracker.update(et)
    print(f"  {pt:>4}{et:>8}{wm:>8}")
print("  水印单调不减：永远等于『最大事件时间 − 允许乱序度』")

print("\n== 窗口触发过程 ==")
wc = WindowedCounter(width=5, allowed_lateness=2)
print(f"  {'处理':>4}{'事件时间':>8}{'uid':>4}{'关窗':>14}{'水印':>6}")
for pt, et, uid in stream:
    closed, wm = wc.process(pt, et, uid)
    tag = str(closed) if closed else "-"
    print(f"  {pt:>4}{et:>8}{uid:>4}{tag:>14}{wm:>6.0f}")

print("\n== 发布的窗口结果 ==")
for start in sorted(wc.emitted):
    print(f"  [{start},{start + wc.width}): 计数 {wc.emitted[start]}")
print(f"  侧输出（迟到被丢弃的事件）: {wc.side_output}")

print("\n== 迟到事件并回后的完整事实 ==")
full = rebuild_with_late(wc.emitted, wc.buckets, wc.side_output, wc.width)
print(f"  发布版: {dict(sorted(wc.emitted.items()))}")
print(f"  完整版: {full}")
diff_windows = [k for k in full if full[k] != wc.emitted.get(k)]
print(f"  受迟到影响的窗口: {diff_windows}")
print("  工程对策：侧输出二次处理 / 延长 allowed_lateness / 可修正的下游存储")

print("\n== 水印松紧的权衡 ==")
print(f"  {'允许乱序':>10}{'发布窗口数':>12}{'迟到事件':>10}{'最后发布时刻':>14}")
for lateness in (0, 1, 2, 4, 8):
    w2 = WindowedCounter(width=5, allowed_lateness=lateness)
    last_pt = 0
    for pt, et, uid in stream:
        w2.process(pt, et, uid)
        if w2.emitted:
            last_pt = max(last_pt, pt)
    print(f"  {lateness:>10}{len(w2.emitted):>12}{len(w2.side_output):>10}{last_pt:>14}")
print("  lateness=0：结果最快但迟到全丢；lateness=8：无迟到但发布延迟")
print("  这条曲线就是流系统的『延迟-正确性』帕累托前沿")

print("\n== 水印的生成策略 ==")
for line in (
    "  有界乱序：W = max_et − 常数 —— 最常用，可配置",
    "  周期性标点（punctuate）：源端显式发『我到这了』的信号",
    "  空闲源处理：某分区长时间无事件 → 空闲分区不应拖住全局水印",
    "  完美水印需要预知未来 —— 工程上永远在『等多久』上做取舍",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  水印把『何时可以信任结果』变成可计算的判据",
    "  窗口生命周期：创建 → 累积 → 水印触发 → 发布 →（迟到 → 侧输出）",
    "  迟到不是错误，是需要显式策略的常态",
    "  926 课：不用丢弃迟到数据 —— 用撤回（retraction）修正已发布结果",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「周期性水印」：每处理 N 个事件才推进一次水印，对比发布延迟。
# 2. 实现「多分区水印」：取各分区水印的最小值，模拟一个分区空闲的拖累效应。
# 3. 实现「迟到事件重开窗口」：已发布窗口再来事件时重新聚合并发布 v2 结果。
# 4. 思考：水印本质上是『放弃绝对正确换取可判定性』——什么业务能接受
#    侧输出兜底，什么业务不能？
