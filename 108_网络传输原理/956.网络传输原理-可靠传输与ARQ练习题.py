# ===== 第956课：网络传输原理-可靠传输与ARQ =====
# 知识点：
#   - IP 层会丢包/乱序/重复 —— 可靠性必须在端到端实现（端到端原则）
#   - ARQ（自动重传请求）：停等协议 = 发一包 → 等 ACK → 超时重传
#   - 序号（mod 2）区分新包与重传的旧 ACK —— 序号是可靠性的基石
#   - 停等吞吐 = 包大小 / RTT：链路再快也白搭 —— 引出流水线（957 课）
#   - 超时时间必须自适应：比 RTT 太短会误重传，太长丢包恢复慢
# 依赖：无（标准库）
import random


class LossyChannel:
    """模拟链路：按概率丢包/延迟。"""

    def __init__(self, loss_rate=0.2, rng=None):
        self.loss_rate = loss_rate
        self.rng = rng or random.Random(156)

    def send(self, packet):
        """返回是否送达。"""
        return self.rng.random() >= self.loss_rate


def stop_and_wait(channel, packets, timeout_slots=3, max_transmits=50):
    """停等协议模拟。返回 (传输日志, 统计)。"""
    log = []
    expected_seq = 0
    stats = {"sent": 0, "retransmits": 0, "acked": 0, "slots": 0}
    for pkt in packets:
        seq = expected_seq % 2                      # 序号 mod 2
        transmit = 0
        while True:
            transmit += 1
            stats["sent"] += 1
            delivered = channel.send(pkt)
            if delivered:
                log.append(f"  发送 seq={seq} ({pkt}) -> 送达")
                # 接收端回 ACK（ACK 本身也可能丢）
                if channel.send("ACK"):
                    log.append(f"  收到 ACK{seq}")
                    expected_seq += 1
                    stats["acked"] += 1
                    stats["slots"] += timeout_slots
                    break
                log.append(f"  发送 seq={seq} -> ACK 丢失，等待超时")
            else:
                log.append(f"  发送 seq={seq} -> 数据包丢失，等待超时")
            stats["retransmits"] += 1
            stats["slots"] += timeout_slots
            if transmit >= max_transmits:
                return log, stats
    return log, stats


print("== 停等协议时序（丢包率 30%）==")
rng = random.Random(156)
channel = LossyChannel(loss_rate=0.3, rng=rng)
packets = ["数据包A", "数据包B", "数据包C", "数据包D"]
log, stats = stop_and_wait(channel, packets)
for entry in log:
    print(entry)
print(f"\n  统计: 发送 {stats['sent']} 次（含重传 {stats['retransmits']}），"
      f"确认 {stats['acked']} 包，占用 {stats['slots']} 个超时槽")

print("\n== 吞吐分析：停等的根本瓶颈 ==")
for rtt in (1, 10, 100):
    throughput = 1000 / (rtt + 1)                  # 每包 1000B，每 RTT 一包
    print(f"  RTT={rtt:>4} 时间单位: 吞吐 ≈ {throughput:.1f} B/单位"
          f"（链路 1000B/单位 时利用率 {throughput / 1000:.1%}）")
print("  RTT 越大利用率越低 —— 链路带宽根本喂不饱，因为一次只飞一包")
print("  这就是为什么真实 TCP 用滑动窗口流水线化（957 课）")

print("\n== 序号为什么必须存在 ==")
print("  场景：数据送达，但 ACK 丢了 → 发送方超时重传 → 接收端收到两份")
print("  序号 mod 2：接收端发现『又是 seq=0』→ 知道是重传 → 只回 ACK 不重复交付")
print("  没有序号，接收端无法区分『新包』与『重传的旧包』")

print("\n== 超时时间的自适应 ==")


def estimate_rtt(samples, alpha=0.125):
    """Jacobson/Karels 算法：EWMA 估计 RTT 与偏差。"""
    est = samples[0]
    dev = 0.0
    history = []
    for s in samples:
        dev = (1 - 0.25) * dev + 0.25 * abs(s - est)
        est = (1 - alpha) * est + alpha * s
        timeout = est + 4 * dev
        history.append(round(timeout, 1))
    return est, history


samples = [10, 12, 11, 30, 13, 12, 11]             # 中途一次尖峰（丢包重传）
est, hist = estimate_rtt(samples)
print(f"  RTT 采样: {samples}")
print(f"  超时序列: {hist}")
print("  尖峰被 EWMA 平滑吸收 —— 固定超时做不到这一点")

print("\n== 丢包率与重传开销 ==")
print(f"  {'丢包率':>8}{'每包平均发送次数':>16}{'吞吐比(相对无损)':>16}")
for loss in (0.0, 0.1, 0.3, 0.5):
    # 每次发送成功概率 (1-p)²，期望发送次数 = 1/(1-p)²
    expected = 1 / max((1 - loss) ** 2, 1e-9)
    print(f"  {loss:>8.0%}{expected:>16.2f}{(1 - loss) ** 2:>16.1%}")
print("  注意是平方：数据或 ACK 任何一个丢都要重来")

print("\n== 小结 ==")
for line in (
    "  可靠性 = 序号 + 确认 + 超时重传，三件套缺一不可",
    "  停等协议正确但吞吐被 RTT 锁死 —— 教学基线而非工程方案",
    "  超时自适应（EWMA）让协议对网络波动鲁棒",
    "  957 课：滑动窗口 —— 让链路同时飞多包",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「ACK 携带确认号」：接收端返回下一个期望序号，替代 mod 2 序号。
# 2. 模拟『ACK 丢失但数据送达』：观察接收端如何处理重复包。
# 3. 实现 N 次重传后放弃并报告错误（可靠性上界）。
# 4. 思考：为什么可靠性放在端点（TCP）而不是链路（以太网）实现？端到端
#    原则的完整表述是什么？
