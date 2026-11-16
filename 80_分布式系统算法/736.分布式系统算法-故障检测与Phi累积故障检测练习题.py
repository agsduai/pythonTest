# ===== 第736课：分布式系统算法-故障检测与 Phi 累积故障检测 =====
# 知识点：
#   - 故障检测不可能「准确」区分「宕机」与「慢」（FLP 不可能结果）
#   - 心跳 + 超时：固定阈值太死，网络抖动会误判，慢恢复又太迟
#   - φ 累积故障检测（Φ Accrual）：输出「怀疑度」而非布尔值
#   - φ = -log10(P_later)，P_later 是「心跳比当前已等待时间还晚到」的概率
#   - 用近期心跳间隔的均值/方差（或指数加权）估计分布；φ 越大越可疑
#   - 应用可自定阈值：φ>=8 标记宕机、φ>=5 只降级，不用改检测器
# 依赖：无（标准库）
import math
import random
import statistics
import time

print("== 固定超时 vs 自适应 ==")
intervals = [1.0, 1.0, 1.0, 1.0, 0.98, 1.02, 1.0]      # 稳定期
print(f"  稳定心跳间隔: mean={statistics.fmean(intervals):.3f}s "
      f"std={statistics.pstdev(intervals):.4f}s")
fixed = 3.0
print(f"  固定超时={fixed}s：网络抖动到 3.5s 就误判，或 2.5s 才判太慢")
print("  φ 检测器输出连续怀疑度，由业务按场景选阈值")


class PhiDetector:
    """用正态分布近似心跳间隔，输出 φ = -log10(P(X > t))。"""

    def __init__(self, window=100, min_samples=5):
        self.window, self.min_samples = window, min_samples
        self.intervals = []
        self.last = None
        self.now = 0.0

    def heartbeat(self, at=None):
        if at is None:
            at = self.now
        if self.last is not None:
            self.intervals.append(at - self.last)
            if len(self.intervals) > self.window:
                self.intervals.pop(0)
        self.last = at

    def advance(self, dt):
        self.now += dt

    def phi(self, at=None):
        at = self.now if at is None else at
        if self.last is None:
            return 0.0
        t = at - self.last
        if len(self.intervals) < self.min_samples:
            return 0.0                  # 样本不足，不误判
        mu = statistics.fmean(self.intervals)
        sigma = max(statistics.pstdev(self.intervals), 1e-3)
        # 正态分布尾概率 P(X > t)，用 erfc 近似
        p_later = 0.5 * math.erfc((t - mu) / (sigma * math.sqrt(2)))
        p_later = max(p_later, 1e-16)
        return -math.log10(p_later)

    def suspicion(self, phi):
        if phi < 1: return "正常"
        if phi < 3: return "轻微怀疑"
        if phi < 5: return "明显可疑"
        if phi < 8: return "高度可疑"
        return "判定宕机"


print("\n== 正常心跳下 φ 随时间变化 ==")
d = PhiDetector(min_samples=4)
r = random.Random(1)
t = 0.0
for _ in range(10):
    t += r.gauss(1.0, 0.05)
    d.advance(t - d.now)
    d.heartbeat(t)
print(f"  采样 {len(d.intervals)} 个间隔, mean={statistics.fmean(d.intervals):.3f}s")
for wait in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
    phi = d.phi(at=t + wait)            # 显式给定「现在」时刻，不推进真实时钟
    print(f"  距上次心跳 {wait:.1f}s -> φ={phi:>6.2f}  {d.suspicion(phi)}")

print("\n== 抖动环境下（间隔方差大）φ 增长更慢 ==")
d2 = PhiDetector(min_samples=4)
t = 0.0
for gap in (0.5, 1.5, 0.4, 1.8, 0.6, 1.4, 0.7, 1.3):
    t += gap
    d2.advance(gap)
    d2.heartbeat(t)
print(f"  间隔 std={statistics.pstdev(d2.intervals):.3f}s（比稳定期大得多）")
for wait in (1.0, 2.0, 3.0):
    phi = d2.phi(at=t + wait)
    print(f"  等待 {wait:.1f}s -> φ={phi:.2f}  {d2.suspicion(phi)}")
print("  方差大 -> 分布尾巴厚 -> 同样的等待时间 φ 更小 -> 少误判")

print("\n== 阈值可按业务选择（同一检测器，不同决策）==")
for threshold, action in ((3, "触发探活/告警"), (5, "从负载均衡摘除"),
                          (8, "标记宕机并触发选主"), (12, "强制下线")):
    print(f"  φ >= {threshold:>2}: {action}")
print("  这正是 accrual 检测器的优势：检测器与应用策略解耦")

print("\n== 误判率与检测时间的权衡 ==")
for thr in (3, 5, 8, 12):
    print(f"  阈值 {thr:>2}: 检测更快但误判更高 / 更慢但更稳（按场景调）")

print("\n== 心跳设计要点 ==")
for line in [
    "  心跳要带任期/序列号，防止旧消息让检测器误以为节点还活着",
    "  用滑动窗口或指数加权(EWMA)适应网络变化，别用全历史",
    "  多路径探测（直连 + 通过第三方）减少共因误判",
    "  SWIM 用「间接 ping」+ 流言传播，扩展性优于全对全心跳",
]:
    print("  -", line)

print("\n== 理论边界 ==")
for line in (
    "  FLP 不可能：异步系统里即使只有一个进程可能崩溃，也无法保证共识终止",
    "  因此故障检测只能是「最终怀疑」，不能 100% 准确",
    "  工程上靠超时 + 重试 + 共识把「不确定」限制在可控范围",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 用 EWMA 替换滑动窗口，对比网络突变时 φ 的响应速度。
# 2. 实现 SWIM 的间接 ping：可疑时请 k 个节点帮忙探测。
# 3. 模拟一次真实 GC 停顿（心跳中断 5s），观察 φ 曲线与误判。
# 4. 思考：为什么「怀疑度」比「布尔宕机标志」更适合分布式系统？
