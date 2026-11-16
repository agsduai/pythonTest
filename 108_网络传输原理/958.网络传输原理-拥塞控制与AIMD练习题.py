# ===== 第958课：网络传输原理-拥塞控制与AIMD =====
# 知识点：
#   - 拥塞控制 vs 流量控制：前者防『网络』过载，后者防『接收端』过载
#   - 慢启动：cwnd 从 1 指数增长到 ssthresh；拥塞避免：线性 +1（AIMD）
#   - 丢包信号：超时（cwnd 归 1 重回慢启动）与三重重复 ACK（cwnd 减半快恢复）
#   - AIMD 产生著名的『锯齿』曲线 —— 加性增、乘性减
#   - 多流公平性：AIMD 让竞争流收敛到均分带宽
# 依赖：无（标准库）
import random


class TCPSender:
    """迷你 TCP 拥塞控制状态机。cwnd 单位 = 包数。"""

    def __init__(self, ssthresh=8):
        self.cwnd = 1.0
        self.ssthresh = ssthresh
        self.state = "slow_start"
        self.sent_total = 0

    def rtt_step(self, lost=False, triple_dup_ack=False):
        """每个 RTT 推进一步。返回 (cwnd, 状态)。"""
        if lost:
            self.ssthresh = max(self.cwnd / 2, 2)
            self.cwnd = 1.0
            self.state = "slow_start"
        elif triple_dup_ack:
            self.ssthresh = max(self.cwnd / 2, 2)
            self.cwnd = self.ssthresh + 3
            self.state = "fast_recovery"
        elif self.state == "slow_start":
            self.cwnd *= 2
            if self.cwnd >= self.ssthresh:
                self.state = "congestion_avoidance"
                self.cwnd = float(self.ssthresh)
        else:
            self.cwnd += 1                      # AIMD 的 AI
        self.sent_total += int(self.cwnd)
        return round(self.cwnd, 1), self.state


print("== 一次完整的拥塞控制生命周期 ==")
sender = TCPSender(ssthresh=8)
events = [("start", False, False)] + \
         [("ok", False, False)] * 10 + \
         [("timeout", True, False)] + \
         [("ok", False, False)] * 8 + \
         [("dup_ack", False, True)] + \
         [("ok", False, False)] * 6
print(f"  {'RTT':>4}{'事件':<10}{'cwnd':>8}{'状态':<20}")
for i, (_, lost, dup) in enumerate(events):
    cwnd, state = sender.rtt_step(lost, dup)
    event = events[i][0]
    print(f"  {i:>4}{event:<10}{cwnd:>8}{state:<20}")
print("  曲线：指数爬升 → 到 ssthresh 转线性 → 超时归 1 → 快恢复减半")

print("\n== AIMD 锯齿（丢包率 2%，50 个 RTT）==")
rng = random.Random(158)


def is_drop(rtt, values):
    return rtt > 0 and values[rtt] < values[rtt - 1] * 0.6


sender2 = TCPSender(ssthresh=8)
sawtooth = []
for rtt in range(50):
    lost = rng.random() < 0.02
    cwnd, _ = sender2.rtt_step(lost)
    sawtooth.append(cwnd)
peak = max(sawtooth)
drops = sum(1 for rtt in range(len(sawtooth)) if is_drop(rtt, sawtooth))
for rtt, c in enumerate(sawtooth):
    bar = "#" * int(c / peak * 40)
    marker = " <- 丢包!" if is_drop(rtt, sawtooth) else ""
    print(f"  {rtt:>3} {c:>6.1f} {bar}{marker}")
print(f"  50 个 RTT 内检测到 {drops} 次丢包 —— 锯齿的每一齿 = AI 爬升 + MD 突降")
print("  平均吞吐 = 锯齿面积/时长：拥塞控制带宽与丢包率的权衡")


print("\n== 多流公平性：AIMD 的收敛魔法 ==")


class Flow:
    def __init__(self, cwnd):
        self.cwnd = cwnd

    def step(self, share_loss):
        self.cwnd += 1                      # AI
        if share_loss:                      # 瓶颈溢出时大家一起 MD
            self.cwnd /= 2


flows = [Flow(10), Flow(2)]
print(f"  {'轮':>4}{'流A':>8}{'流B':>8}{'占比A':>8}")
for r in range(24):
    total = sum(f.cwnd for f in flows)
    ratio = flows[0].cwnd / total
    if r % 2 == 0 or r < 4:
        print(f"  {r:>4}{flows[0].cwnd:>8.1f}{flows[1].cwnd:>8.1f}{ratio:>8.1%}")
    loss = r % 4 == 3                       # 周期性瓶颈溢出
    for f in flows:
        f.step(loss)
print(f"  起点悬殊 (10 vs 2) → 24 轮后占比 {flows[0].cwnd / sum(f.cwnd for f in flows):.1%}")
print("  AIMD 的收敛是渐近的：每次 MD 都把差距减半，差距按 1/2 指数收缩")
print("  『趋近』而非『立刻达到』—— 加性增只补差、乘性减专削强者")

print("\n== 拥塞控制 vs 流量控制 ==")
print(f"  {'维度':<12}{'拥塞控制':<20}{'流量控制'}")
for row in (("保护对象", "网络（路由器队列）", "接收端缓冲"),
            ("信号来源", "丢包/ECN/延迟", "接收窗口 rwnd"),
            ("实际窗口", "min(cwnd, rwnd)", "两者取小")):
    print(f"  {row[0]:<12}{row[1]:<20}{row[2]}")

print("\n== 小结 ==")
for line in (
    "  慢启动不是慢 —— 是指数增长，名字来自『谨慎地开始』",
    "  AIMD 的 MD 保证快速退让、AI 保证渐进探测 —— 既稳定又公平",
    "  超时 vs 三重重复 ACK 是两种丢包信号，对应两种恢复强度",
    "  959 课：丢包从哪来 —— 路由器队列的管理策略",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 CUBIC 的简化版：cwnd 增长与上次丢包后的时间三次方相关，对比锯齿。
# 2. 实现「三重重复 ACK」的精确判定（连续 3 个相同 ACK 才触发快恢复）。
# 3. 模拟 5 条流共享一条 100 包/RTT 链路，统计收敛后的份额分布。
# 4. 思考：为什么无线网络（Wi-Fi 丢包≠拥塞）会让 AIMD 误判？BBR 如何绕开？
