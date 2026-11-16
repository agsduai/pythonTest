# ===== 第959课：网络传输原理-队列管理与丢包策略 =====
# 知识点：
#   - 路由器队列满了怎么办：丢谁？—— 队列管理决定整个网络的体验
#   - DropTail：队尾丢包 —— 简单但引发 TCP 全局同步（synchronized sawtooth）
#   - RED：队列平均长度超阈值就开始随机提前丢 —— 早丢一个保一群
#   - 全局同步：多条 TCP 同步锯齿 → 链路利用率周期性塌陷
#   - ECN：不丢包而是打标记，端点自行降速 —— 更文明的拥塞信号
# 依赖：无（标准库）
import random
from collections import deque


class DropTailQueue:
    def __init__(self, capacity=10):
        self.capacity = capacity
        self.queue = deque()
        self.dropped = 0

    def enqueue(self, flow_id, seq):
        if len(self.queue) >= self.capacity:
            self.dropped += 1
            return False                        # 队尾丢包
        self.queue.append((flow_id, seq))
        return True

    def dequeue(self, n=1):
        out = []
        for _ in range(n):
            if self.queue:
                out.append(self.queue.popleft())
        return out


class REDQueue:
    """随机早期检测：平均队长超过 min_thresh 开始按概率丢。"""

    def __init__(self, capacity=10, min_thresh=4, max_thresh=9):
        self.capacity = capacity
        self.min_thresh = min_thresh
        self.max_thresh = max_thresh
        self.queue = deque()
        self.avg = 0.0                          # 指数加权平均队长
        self.dropped = 0
        self.ecn_marks = 0

    def enqueue(self, flow_id, seq, rng):
        self.avg = 0.9 * self.avg + 0.1 * len(self.queue)
        if len(self.queue) >= self.capacity:
            self.dropped += 1
            return "drop"
        if self.avg > self.max_thresh:
            self.dropped += 1
            return "drop"
        if self.avg > self.min_thresh:
            # 概率随平均队长线性增长
            p = (self.avg - self.min_thresh) / (self.max_thresh - self.min_thresh)
            if rng.random() < p * 0.5:
                self.dropped += 1
                return "early_drop"
            if rng.random() < 0.3:
                self.ecn_marks += 1
                return "ecn"
        self.queue.append((flow_id, seq))
        return "ok"

    def dequeue(self, n=1):
        out = []
        for _ in range(n):
            if self.queue:
                out.append(self.queue.popleft())
        return out


def simulate_flows(queue, flows_events, rng, drain_per_round=2, rounds=40):
    """多流共享队列：每轮入队 + 排空若干包。返回每流丢包统计。"""
    per_flow = {f: {"sent": 0, "dropped": 0} for f in flows_events}
    per_round_len = []
    for r in range(rounds):
        for flow_id in flows_events:
            for _ in range(flows_events[flow_id]):
                result = queue.enqueue(flow_id, (flow_id, r), rng) \
                    if isinstance(queue, REDQueue) else queue.enqueue(flow_id, r)
                per_flow[flow_id]["sent"] += 1
                if result in ("drop", "early_drop"):
                    per_flow[flow_id]["dropped"] += 1
        queue.dequeue(drain_per_round)
        per_round_len.append(len(queue.queue))
    return per_flow, per_round_len


rng = random.Random(159)

print("== DropTail vs RED：3 条流共享 10 包队列 ==")
flows = {"A": 4, "B": 4, "C": 4}
tail = DropTailQueue(10)
per_tail, _ = simulate_flows(tail, flows, rng)
red = REDQueue(10, min_thresh=4, max_thresh=9)
per_red, red_lens = simulate_flows(red, flows, rng)
print(f"  {'流':<6}{'DropTail丢包':>14}{'RED丢包':>10}")
for f in flows:
    print(f"  {f:<6}{per_tail[f]['dropped']:>14}{per_red[f]['dropped']:>10}")
print(f"  RED 的 ECN 标记数 = {red.ecn_marks}（不丢包，打标让端点自降）")

print("\n== 全局同步演示 ==")
print("  DropTail 下所有流的锯齿同步：队满 → 各流同时 MD → 队空 → 同时 AI")
print("  链路利用率呈周期性塌陷 —— 这是 RED 论文的核心动机")

print("\n== RED 的参数语义 ==")
print(f"  {'参数':<16}{'含义'}")
for row in (("min_thresh", "低于它绝不主动丢"),
            ("max_thresh", "高于它必然丢（或强标记）"),
            ("中间区间", "丢包概率随平均队长线性增长"),
            ("平均权重 0.9", "平滑瞬时突发，只对持续拥塞反应")):
    print(f"  {row[0]:<16}{row[1]}")

print("\n== 队列长度轨迹 ==")
print(f"  {'轮':>4}{'RED 平均队长':>14}  可视化")
max_len = max(red_lens) or 1
for r, l in enumerate(red_lens[:20]):
    avg = round(0.9 * l + 0.1 * l, 1)
    print(f"  {r:>4}{avg:>14.1f}  {'#' * int(l / max_len * 40)}")

print("\n== 现代队列管理家族 ==")
for line in (
    "  RED → ARED（自适应 RED）→ CoDel/FQ-CoDel（按排队时延而非长度）",
    "  CoDel 的洞察：『站在队列里的时间』才是坏的，队列长度只是代理",
    "  ECN + DCTCP 在数据中心把丢包信号完全替换成标记信号",
    "  共同点：把『丢谁的包』从惩罚游戏变成调节游戏",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  队列管理是网络的『中央空调』：策略影响所有经过的流",
    "  DropTail 的全局同步是 TCP 锯齿同相位的根源",
    "  RED/ECN 用概率与标记提前疏导 —— 不等爆了才丢",
    "  960 课：带宽 × 延迟 = 管道的容积 —— 窗口设计的物理上限",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 CoDel 简化版：记录每个包的入队时刻，出队时检查停留时间是否超 5ms。
# 2. 实现 FQ（公平队列）：每流一个子队列轮流出包，验证份额公平性。
# 3. 扫描 RED 的 min/max_thresh 组合，绘制「丢包率-平均队长」热力表。
# 4. 思考：为什么 RED 用『平均』队长而不是『瞬时』队长判断拥塞？
