# ===== 第957课：网络传输原理-滑动窗口与流水线 =====
# 知识点：
#   - 滑动窗口：允许同时飞 N 个未确认包 —— 把 RTT 藏进流水线里
#   - Go-Back-N：丢了 k 号包 → 重传 k 起的所有包；Selective Repeat：只重传缺的
#   - 吞吐 ≈ min(带宽, 窗口大小 / RTT)：窗口是并发度
#   - 接收端缓冲：乱序到达的包先存着，等空洞填上再按序交付
#   - 窗口推进：收到 ACK 后窗口右移 —— ACK 是窗口的燃料
# 依赖：无（标准库）
import random
from collections import deque


class SendWindow:
    """Go-Back-N 发送窗口。"""

    def __init__(self, size, total_packets):
        self.size = size
        self.next_seq = 0                       # 下一个可发送序号
        self.base = 0                           # 最小未确认序号
        self.total = total_packets
        self.in_flight = {}                     # seq -> 是否已发未确认

    def can_send(self):
        return self.next_seq < self.base + self.size and self.next_seq < self.total

    def send(self):
        pkt = self.next_seq
        self.in_flight[pkt] = True
        self.next_seq += 1
        return pkt

    def on_ack(self, ack):
        """累积确认：ack = 已连续收到的最大序号 + 1。"""
        moved = 0
        while self.base < ack:
            self.in_flight.pop(self.base, None)
            self.base += 1
            moved += 1
        return moved


def simulate_gbn(total=10, window=3, loss_p=0.15, rng=None, max_slots=60):
    """GBN：发送 [base, base+window)，接收端只按序收，乱序一律丢弃；
    丢包 → 超时后整个窗口重传。"""
    rng = rng or random.Random(157)
    expected = 0                            # 接收端期望序号（=发送窗口左沿）
    slots = retrans = 0
    sent_before = set()
    timeline = []
    while expected < total and slots < max_slots:
        slots += 1
        events = []
        top = min(expected + window, total)
        any_lost = False
        for seq in range(expected, top):
            is_re = seq in sent_before
            retrans += 1 if is_re else 0
            sent_before.add(seq)
            lost = rng.random() < loss_p
            if lost:
                any_lost = True
                events.append(f"发{seq}✗")
            elif seq == expected:
                events.append(f"发{seq}✓")
                expected += 1
            else:
                events.append(f"发{seq}拒")   # GBN：乱序包直接丢弃
                any_lost = True
        events.append(f"ACK{expected}")
        timeline.append(" ".join(events))
    return timeline, slots, retrans, expected


def simulate_sr(total=10, window=3, loss_p=0.15, rng=None, max_slots=60):
    """SR：乱序包缓存等缺口，只重传真正缺失的包。"""
    rng = rng or random.Random(158)
    expected = 0
    slots = retrans = 0
    sent_before = set()
    buffered = set()
    timeline = []
    while expected < total and slots < max_slots:
        slots += 1
        events = []
        top = min(expected + window, total)
        for seq in range(expected, top):
            is_re = seq in sent_before
            retrans += 1 if is_re else 0
            sent_before.add(seq)
            lost = rng.random() < loss_p
            if lost:
                events.append(f"发{seq}✗")
            elif seq == expected:
                events.append(f"发{seq}✓")
                expected += 1
                while expected in buffered:      # 交付缓存中连续的包
                    events.append(f"交付{expected}")
                    buffered.discard(expected)
                    expected += 1
            else:
                buffered.add(seq)
                events.append(f"收{seq}(缓存)")
        events.append(f"ACK{expected}")
        timeline.append(" ".join(events))
    return timeline, slots, retrans, expected


print("== Go-Back-N 模拟：10 包 / 窗口 3 / 丢包率 15% ==")
timeline, slots, retrans, delivered = simulate_gbn(
    total=10, window=3, loss_p=0.15, rng=random.Random(157))
for i, t in enumerate(timeline):
    print(f"  槽{i + 1}: {t}")
print(f"  完成 = {delivered} 包，用时 {slots} 槽，重传发送 {retrans} 次")
print("  乱序包被『拒』= GBN 接收端丢弃；缺失包在下槽随窗口重传")

print()
print("== 窗口大小 vs 吞吐（无损）==")


print(f"  {'窗口':>6}{'完成槽数':>10}")
for w in (1, 2, 3, 5, 10):
    _, slots_w, _, _ = simulate_gbn(total=10, window=w, loss_p=0.0,
                                    rng=random.Random(157))
    print(f"  {w:>6}{slots_w:>10}")
print("  无损时：槽数 ≈ ceil(包数/窗口) —— 窗口就是并发度")
print("  窗口 1 = 退化成停等协议（956 课）")

print()
print("== Selective Repeat 对照（同丢包率，20 次平均）==")


def average_runs(sim, runs=20, **kwargs):
    total_slots = total_retrans = 0
    for seed in range(runs):
        _, slots_i, retrans_i, _ = sim(rng=random.Random(seed), **kwargs)
        total_slots += slots_i
        total_retrans += retrans_i
    return total_slots / runs, total_retrans / runs


avg_gbn = average_runs(simulate_gbn, 20, total=10, window=3, loss_p=0.15)
avg_sr = average_runs(simulate_sr, 20, total=10, window=3, loss_p=0.15)
print(f"  {'方案':<8}{'平均槽数':>10}{'平均重传':>10}")
print(f"  {'GBN':<8}{avg_gbn[0]:>10.1f}{avg_gbn[1]:>10.1f}")
print(f"  {'SR':<8}{avg_sr[0]:>10.1f}{avg_sr[1]:>10.1f}")
tl_sr, _, _, _ = simulate_sr(total=10, window=3, loss_p=0.15,
                             rng=random.Random(159))
for line in tl_sr[:5]:
    print(f"    {line}")
print("  SR 缓存乱序包、只重传缺失 → 重传更少；代价是接收端内存")

print("\n== 接收端缓冲演示 ==")


def receiver_buffer(arrival_order):
    """乱序到达 → 缓存 → 按序交付。"""
    buffered = set()
    delivered = []
    next_expected = 0
    log = []
    for seq in arrival_order:
        buffered.add(seq)
        while next_expected in buffered:
            delivered.append(next_expected)
            buffered.discard(next_expected)
            next_expected += 1
        log.append(f"收{seq} → 已交付 {delivered} 缓存 {sorted(buffered - set(delivered))}")
    return log


arrival = [0, 2, 3, 1]                          # 1 号晚到
for line in receiver_buffer(arrival):
    print(f"  {line}")
print("  2/3 先到只能缓存，1 号一到立即连发 1,2,3 —— 按序交付的机械实现")

print("\n== 小结 ==")
for line in (
    "  滑动窗口 = 并发度控制：吞吐 ≈ 窗口/RTT（受带宽封顶）",
    "  GBN 简单省内存、SR 省带宽费内存 —— 真实 TCP 混合两者",
    "  接收缓冲把『乱序到达』整理成『按序交付』的字节流",
    "  958 课：窗口该多大？—— 让网络自己告诉你（拥塞控制）",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「累积 ACK + SACK 选项」：ACK 里携带乱序接收的区段，SR 重传更精准。
# 2. 实现「窗口自动调优」：连续无损时窗口 +1，丢包时减半，观察收敛。
# 3. 统计 GBN 与 SR 在不同丢包率下的重传包数曲线（0%~30%）。
# 4. 思考：为什么接收缓冲不能无限大？缓冲塞满后新的乱序包该丢弃还是替换？
