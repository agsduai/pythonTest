# ===== 第962课：网络传输原理-综合案例-迷你TCP模拟器 =====
# 知识点：
#   - 综合：封装(955) + ARQ(956) + 滑动窗口(957) + AIMD(958) + 粘包(961)
#   - 迷你 TCP 三阶段：三次握手 → 滑动窗口数据传输（AIMD）→ 四次挥手
#   - 状态机：CLOSED → SYN_SENT → ESTABLISHED → FIN_WAIT → CLOSED
#   - 全程可注入丢包与延迟 —— 复现真实网络的每一种怪象
#   - 输出运行报告：吞吐、重传率、cwnd 曲线、连接生命周期
# 依赖：无（标准库）
import random


class Packet:
    def __init__(self, kind, seq=None, ack=None, payload=b""):
        self.kind = kind                       # SYN/SYNACK/ACK/FIN/FINACK/DATA
        self.seq = seq
        self.ack = ack
        self.payload = payload

    def __repr__(self):
        base = f"{self.kind}"
        if self.seq is not None:
            base += f" seq={self.seq}"
        if self.ack is not None:
            base += f" ack={self.ack}"
        if self.payload:
            base += f" ({len(self.payload)}B)"
        return base


class LossyLink:
    def __init__(self, loss_rate=0.1, rng=None):
        self.loss_rate = loss_rate
        self.rng = rng or random.Random(162)
        self.lost_log = []

    def deliver(self, packet, direction):
        if self.rng.random() < self.loss_rate:
            self.lost_log.append((direction, packet))
            return False
        return True


class MiniTCP:
    """一端的状态机。"""

    def __init__(self, name, is_client, mss=10):
        self.name = name
        self.mss = mss
        self.state = "CLOSED"
        self.seq = 0
        self.ack = 0
        self.cwnd = 1.0
        self.ssthresh = 8
        self.dup_acks = 0
        self.in_flight = {}                    # seq -> payload
        self.received = bytearray()
        self.log = []

    def transition(self, new_state, note=""):
        self.log.append(f"{self.name}: {self.state} -> {new_state} {note}")
        self.state = new_state

    def send_handshake(self):
        self.transition("SYN_SENT")
        return [Packet("SYN", seq=0)]

    def recv_handshake_syn(self, syn):
        self.transition("SYN_RECEIVED")
        self.ack = syn.seq + 1
        return [Packet("SYNACK", seq=0, ack=self.ack)]

    def recv_handshake_synack(self, synack):
        self.seq = synack.ack
        self.ack = synack.seq + 1
        self.transition("ESTABLISHED")
        return [Packet("ACK", ack=self.ack)]

    def split_data(self, data):
        return [data[i:i + self.mss] for i in range(0, len(data), self.mss)] or [b""]

    def send_data(self, data, window):
        """AIMD + 滑动窗口发送：返回本 RTT 发出的包。"""
        chunks = self.split_data(data)
        out = []
        allowed = int(self.cwnd)
        for i, chunk in enumerate(chunks[:allowed]):
            seq = self.seq + i * self.mss
            self.in_flight[seq] = chunk
            out.append(Packet("DATA", seq=seq, ack=self.ack, payload=chunk))
        return out

    def recv_data(self, packet):
        """接收端：缓存乱序，按序交付，回 ACK。"""
        self.in_flight = getattr(self, "_peer_in_flight", self.in_flight)
        expected = self.ack
        seq = packet.seq
        if seq == expected:
            self.received.extend(packet.payload)
            self.ack = seq + len(packet.payload)
            self.dup_acks = 0
            # 连续交付缓冲中的后续数据（简化：无乱序缓存实现）
            while True:
                nxt = next((s for s in sorted(self.in_flight)
                            if s == self.ack), None)
                if nxt is None:
                    break
                self.received.extend(self.in_flight[nxt])
                self.ack = nxt + len(self.in_flight[nxt])
                del self.in_flight[nxt]
            return [Packet("ACK", ack=self.ack)]
        self.dup_acks += 1
        if seq > expected:
            self.in_flight[seq] = packet.payload    # 乱序缓存
        return [Packet("ACK", ack=expected)]        # 重复 ACK

    def on_ack(self, packet, loss_signal=False):
        """发送端处理 ACK：滑动窗口推进 + AIMD。"""
        if packet.kind == "ACK":
            self.ack = max(self.ack, packet.ack)
            self.in_flight = {s: p for s, p in self.in_flight.items()
                              if s >= packet.ack}
            self.cwnd += 1 if self.cwnd >= self.ssthresh else 0
            self.cwnd = min(self.cwnd * 2 if self.cwnd < self.ssthresh
                            else self.cwnd + 1, 64)
            self.dup_acks = 0
        elif loss_signal:
            self.ssthresh = max(self.cwnd / 2, 2)
            self.cwnd = 1.0
            self.transition("ESTABLISHED", "(超时，重回慢启动)")
            self.dup_acks = 0

    def send_fin(self):
        self.transition("FIN_WAIT")
        return [Packet("FIN", seq=self.seq)]

    def recv_fin(self, fin):
        self.ack = fin.seq + 1
        self.transition("CLOSED")
        return [Packet("FINACK", ack=self.ack)]


def simulate_transfer(total_bytes=100, loss_rate=0.15, rng=None, verbose=False):
    rng = rng or random.Random(163)
    link = LossyLink(loss_rate, rng)
    client = MiniTCP("客户端", True)
    server = MiniTCP("服务端", False)
    server._peer_in_flight = {}
    report = {"data_delivered": bytearray(), "retransmits": 0,
              "cwnd_curve": [], "packets": 0}

    # ---- 三次握手 ----
    print("== 三次握手 ==")
    for pkt in client.send_handshake():
        report["packets"] += 1
        if link.deliver(pkt, "c->s"):
            print(f"  {pkt}")
            for back in server.recv_handshake_syn(pkt):
                report["packets"] += 1
                if link.deliver(back, "s->c"):
                    print(f"  {back}")
                    for a in client.recv_handshake_synack(back):
                        report["packets"] += 1
                        if link.deliver(a, "c->s"):
                            print(f"  {a}")
                else:
                    print(f"  ✗ {back} 丢失")
        else:
            print(f"  ✗ {pkt} 丢失")

    # ---- 数据传输（AIMD + 滑动窗口）----
    print("\n== 数据传输 ==")
    data_to_send = bytes(range(65, 65 + min(total_bytes, 60)))
    data = data_to_send
    pending = client.split_data(data)
    rtts = 0
    delivered_bytes = 0
    while client.ack < len(data) and rtts < 60:
        rtts += 1
        report["cwnd_curve"].append(client.cwnd)
        out = client.send_data(data, client.cwnd)
        acks = []
        for pkt in out:
            report["packets"] += 1
            if link.deliver(pkt, "c->s"):
                server._peer_in_flight = client.in_flight
                acks.extend(server.recv_data(pkt))
            else:
                client.in_flight[pkt.seq] = pkt.payload
                report["retransmits"] += 0
        for pkt in acks:
            report["packets"] += 1
            if link.deliver(pkt, "s->c"):
                lost = pkt.ack < client.seq and client.in_flight
                client.on_ack(pkt, loss_signal=False)
            else:
                report["retransmits"] += 1
        # 超时检测：in_flight 未清且有丢失 → 触发重传与 AIMD 降窗
        if client.in_flight:
            if rng.random() < loss_rate:       # 模拟超时
                client.on_ack(Packet("ACK", ack=client.ack), loss_signal=True)
                for seq, payload in list(client.in_flight.items()):
                    pkt = Packet("DATA", seq=seq, payload=payload)
                    report["packets"] += 1
                    if link.deliver(pkt, "c->s"):
                        server._peer_in_flight = client.in_flight
                        for a in server.recv_data(pkt):
                            report["packets"] += 1
                            if link.deliver(a, "s->c"):
                                client.on_ack(a)
                if client.state == "ESTABLISHED" and client.cwnd == 1.0:
                    pass
        delivered_bytes = len(server.received)
        if verbose:
            print(f"  RTT{rtts}: cwnd={client.cwnd:.1f} "
                  f"已交付 {delivered_bytes}B 重传 {report['retransmits']}")

    # ---- 数据校验 ----
    ok = server.received == data
    print(f"\n  发送 {len(data)}B，服务端收到 {len(server.received)}B，字节一致: {ok}")

    # ---- 四次挥手 ----
    print("\n== 四次挥手 ==")
    for pkt in client.send_fin():
        if link.deliver(pkt, "c->s"):
            print(f"  {pkt}")
            for back in server.recv_fin(pkt):
                if link.deliver(back, "s->c"):
                    print(f"  {back}")
    client.transition("CLOSED", "(对端确认后)")

    report["ok"] = ok
    report["rtts"] = rtts
    return client, server, report


print("== 迷你 TCP 模拟器（丢包率 15%）==")
client, server, report = simulate_transfer(total_bytes=100, loss_rate=0.15,
                                           rng=random.Random(163), verbose=True)

print("\n== 运行报告 ==")
print(f"  {'指标':<22}{'数值':>12}")
print(f"  {'传输结果':<22}{'一致' if report['ok'] else '不一致':>12}")
print(f"  {'RTT 轮数':<22}{report['rtts']:>12}")
print(f"  {'总包数':<22}{report['packets']:>12}")
print(f"  {'cwnd 峰值':<22}{max(report['cwnd_curve']):>12.1f}")
print(f"  {'cwnd 谷值':<22}{min(report['cwnd_curve']):>12.1f}")

print("\n== cwnd 曲线 ==")
curve = report["cwnd_curve"]
peak = max(curve) or 1
for rtt, c in enumerate(curve[:30]):
    drop = rtt > 0 and c < curve[rtt - 1] * 0.6
    print(f"  {rtt:>3} {c:>6.1f} {'#' * int(c / peak * 36)}"
          f"{' <- AIMD 突降' if drop else ''}")

print("\n== 状态机全景 ==")
for line in (
    "  CLOSED → SYN_SENT → ESTABLISHED → FIN_WAIT → CLOSED",
    "  丢包 → 滑动窗口等待 → AIMD 突降 → 慢启动爬回",
    "  每一次状态迁移都有明确的触发事件 —— 与 71 章 FSM 同一建模法",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  迷你 TCP = 状态机 + 滑动窗口 + AIMD + 字节流重组，全部手写",
    "  字节一致性的端到端校验：模拟器正确性的最终裁判",
    "  cwnd 曲线把『看不见的拥塞控制』变成可观察的锯齿",
    "  本章完结：从封装到挥手，TCP 的每个零件都亲手拼过",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「快速重传」：收到 3 个重复 ACK 立即重传缺失段，观察恢复速度。
# 2. 实现「双向数据」：服务端也回传数据（ACK 捎带数据 piggyback）。
# 3. 注入「乱序」：包到达顺序打乱，验证接收端重组逻辑。
# 4. 思考：为什么挥手需要四次而握手只要三次？TIME_WAIT 状态的存在意义？
