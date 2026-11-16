# ===== 第800课：流式算法与数据摘要-滑动窗口与时间衰减 =====
# 知识点：
#   - 很多流指标是「最近 N 条/最近 T 秒」语义，而不是从头累计
#   - 滑动窗口实现：环形缓冲（计数型） / 指数衰减 EWMA（平滑型）
#   - 指数衰减：w ← w·e^(-λΔt) + x；λ 决定「记忆长度」（半衰期）
#   - 半衰期 t½ = ln2/λ：过了 t½ 时间，旧值权重减半
#   - 滑动窗口计数：分桶 + 过期淘汰，O(1) 查询
#   - 与第68章调度、第782课时间序列分析的关系：EWMA 是最简单的「在线指数平滑」
# 依赖：无（标准库）
import math
import random
import statistics
from collections import deque


class SlidingWindowCounter:
    """最近 max_items 条的滑动窗口计数（计数型）。"""

    def __init__(self, max_items):
        self.max_items = max_items
        self.buf = deque(maxlen=max_items)
        self.counts = {}

    def add(self, key, count=1):
        if len(self.buf) == self.buf.maxlen:
            old = self.buf[0]
            self.counts[old] = self.counts.get(old, 0) - 1
            if self.counts[old] <= 0:
                del self.counts[old]
        self.buf.append(key)
        self.counts[key] = self.counts.get(key, 0) + 1

    def top(self, k=3):
        return sorted(self.counts.items(), key=lambda x: -x[1])[:k]


class EWMA:
    """指数加权移动平均：w = w·decay + x·(1-decay)。"""

    def __init__(self, halflife=10.0):
        self.decay = math.exp(-math.log(2) / halflife)   # 半衰期转衰减系数
        self.w = 0.0
        self.last_t = 0.0
        self.initialized = False

    def update(self, value, t=None):
        if not self.initialized:
            self.w = value; self.last_t = t or 0.0
            self.initialized = True
            return self.w
        dt = (t - self.last_t) if t is not None else 1.0
        self.last_t = t if t is not None else self.last_t + 1.0
        d = self.decay ** dt
        self.w = self.w * d + value * (1 - d)
        return self.w


print("== 滑动窗口计数：最近 100 条的 Top-K ==")
sw = SlidingWindowCounter(100)
# 前 100 条全是 A，后 100 条是 B/C 交替——A 应被逐渐「挤出窗口」
events = (["A"] * 100) + (["B", "C"] * 50)
for e in events:
    sw.add(e)
print(f"  最新窗口 Top-3: {sw.top(3)}")
print("  A 已不在窗口内 -> 被自动淘汰")

print("\n== 窗口大小的影响 ==")
for size in (10, 50, 100, 200, 400):
    sw2 = SlidingWindowCounter(size)
    for e in events:
        sw2.add(e)
    print(f"  window={size:>3}: Top-3={sw2.top(3)}")
print("  窗口越小越「追热点」，越大越「反映整体」")

print("\n== EWMA：半衰期与平滑度 ==")
# 信号：稳定 10 -> 阶跃到 30
signal = [10.0]*30 + [30.0]*30
for halflife in (1.0, 5.0, 15.0):
    e = EWMA(halflife=halflife)
    trace = [e.update(v) for v in signal]
    print(f"  半衰期={halflife:<5}: 阶跃后第 10 步≈{trace[40]:.1f} "
          f"末值≈{trace[-1]:.2f}")
print("  半衰期越短，跟随越快但噪声也越大（与第736课 φ 检测器的权衡一致）")

print("\n== EWMA 对异常值的鲁棒性 ==")
rng = random.Random(5)
signal2 = [rng.gauss(10, 1) for _ in range(50)] + [500.0] + [rng.gauss(10, 1) for _ in range(50)]
e_fast = EWMA(halflife=3)
e_slow = EWMA(halflife=20)
trace_fast = [e_fast.update(v) for v in signal2]
trace_slow = [e_slow.update(v) for v in signal2]
print(f"  异常值 500 出现在第 51 个点")
print(f"  快速 EWMA(半衰期3) 在异常后: {[round(trace_fast[i],1) for i in (49,50,51,55)]}")
print(f"  慢速 EWMA(半衰期20) 在异常后: {[round(trace_slow[i],1) for i in (49,50,51,55)]}")
print("  快 EWMA 受异常影响大；慢 EWMA 更稳但恢复慢")

print("\n== 时间感知的 EWMA（不规则间隔）==")
e = EWMA(halflife=10.0)
events = [(0.0, 5.0), (1.0, 5.0), (2.0, 5.0),   # 正常间隔
          (10.0, 5.0),                          # 隔了 8 秒
          (10.5, 5.0)]                          # 只隔 0.5 秒
trace = []
for t, v in events:
    val = e.update(v, t=t)
    trace.append(round(val, 2))
print(f"  各时刻的 EWMA: {trace}")
print("  时间间隔越大，旧值衰减越多 -> 同样的值「过期」得更快")

print("\n== 滑动窗口 vs EWMA ==")
print(f"  {'维度':<14}{'滑动窗口计数':<20}{'EWMA'}")
for row in (("衰减", "阶梯式（过期就清零）", "平滑指数"),
            ("内存", "O(窗口大小)", "O(1)"),
            ("突发敏感", "完全反映", "被平滑"),
            ("典型用途", "Top-K 榜单", "QPS/延迟监控")):
    print(f"  {row[0]:<14}{row[1]:<20}{row[2]}")

print("\n== 组合：滑动窗口 + Top-K ==")
for line in (
    "  热搜榜 = 滑动窗口内的 Misra-Gries（第799课）",
    "  实时大屏 = 滑动窗口 + EWMA 平滑显示",
    "  告警去抖 = EWMA 超阈值持续 N 秒才触发",
    "  全部是本章「近似 + 有界内存」思想的组合",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  deque(maxlen=n) 的 Python 实现已够用；高频场景用环形数组 + 指针",
    "  EWMA 需按真实时间间隔衰减，不要假定等间隔",
    "  半衰期是比「衰减系数」更直观的调参方式",
    "  分布式场景各节点独立 EWMA 再聚合，与全局略有偏差（可接受）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「时间感知的滑动窗口」：元素过期按时间而非数量。
# 2. 用 EWMA 检测 QPS 突增（当前值 > 均值 × 3 触发告警），并测量误报率。
# 3. 组合 SlidingWindowCounter + Misra-Gries，实现「最近 1 小时 Top-10」。
# 4. 思考：为什么监控指标都用 EWMA 而不用简单移动平均？
