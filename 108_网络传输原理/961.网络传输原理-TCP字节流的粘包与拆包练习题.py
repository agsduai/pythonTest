# ===== 第961课：网络传输原理-TCP字节流的粘包与拆包 =====
# 知识点：
#   - TCP 是字节流：没有消息边界 —— 『粘包』是应用层没设计边界的错觉
#   - 三种消息边界方案：定长 / 分隔符 / 长度前缀 —— 各有适用场景
#   - Nagle 算法：小包攒着发（省带宽）；delayed ACK：ACK 攒着回（省包）
#   - 两者交互可能造成 40ms 假死 —— 真实系统的经典调优项
#   - 心跳消息：让 NAT/防火墙记住连接 + 探测死连接
# 依赖：无（标准库）
import random


class TCPStream:
    """模拟 TCP 字节流语义：写入的是字节，读出时边界不可预期。"""

    def __init__(self):
        self.buffer = bytearray()
        self.pending = bytearray()              # Nagle 攒着的小包

    def write(self, data):
        self.pending.extend(data)

    def flush(self):
        self.buffer.extend(self.pending)
        self.pending.clear()

    def read_available(self):
        """应用读走『当前可读的全部』—— 边界由应用自己定义。"""
        data = bytes(self.buffer)
        self.buffer.clear()
        return data


def demo_sticky(rng):
    """三次 write 10 字节 + 一次 read = 30 字节粘成一坨。"""
    stream = TCPStream()
    for msg in ("msg1|", "msg2|", "msg3|"):
        stream.write(msg.encode())
    stream.flush()
    return stream.read_available()


def split_by_delimiter(data, delim=b"|"):
    """分隔符方案：简单但有转义难题。"""
    messages = data.split(delim)
    return [m for m in messages if m]


def split_by_length_prefix(data):
    """长度前缀方案：4 字节小端长度 + 内容 —— 工业标准做法。"""
    messages = []
    pos = 0
    while pos + 4 <= len(data):
        length = int.from_bytes(data[pos:pos + 4], "little")
        pos += 4
        if pos + length > len(data):
            break                              # 半包：等待更多数据
        messages.append(data[pos:pos + length].decode())
        pos += length
    return messages


def pack_length_prefix(message):
    body = message.encode()
    return len(body).to_bytes(4, "little") + body


print("== 粘包现象 ==")
rng = random.Random(161)
sticky = demo_sticky(rng)
print(f"  三次 write('msgN|') 后一次 read 得到: {sticky!r}")
print(f"  字节数 = {len(sticky)} —— 三条消息粘成一坨，TCP 只保证字节序")
parsed = split_by_delimiter(sticky)
print(f"  用分隔符 | 拆开: {parsed}")

print("\n== 半包：读到的数据不完整 ==")
stream = TCPStream()
stream.write(pack_length_prefix("你好世界"))
half = bytes(stream.read_available()[:6])      # 只读到长度 + 2 字节内容
print(f"  模拟半包: 只读到 {half!r}")
msgs = split_by_length_prefix(half)
print(f"  长度前缀解析: {msgs}（内容不足 -> 缓存等待）")
stream2 = TCPStream()
stream2.write(pack_length_prefix("你好世界"))
full = stream2.read_available()
print(f"  读全量: {split_by_length_prefix(full)}")

print("\n== 三种边界方案对比 ==")
print(f"  {'方案':<14}{'优点':<20}{'缺点':<24}{'典型'}")
for row in (("定长", "解析 O(1)", "浪费带宽", "固定位字段协议"),
            ("分隔符", "可读性好", "需转义分隔符", "Redis/SMTP"),
            ("长度前缀", "无歧义/高效", "需处理半包", "HTTP2/自定义RPC")):
    print(f"  {row[0]:<14}{row[1]:<20}{row[2]:<24}{row[3]}")

print("\n== 半包处理的标准模式（状态机）==")


class LengthPrefixDecoder:
    """增量解码器：喂多少算多少，凑齐一条才吐一条。"""

    def __init__(self):
        self.buffer = bytearray()
        self.messages = []

    def feed(self, data):
        self.buffer.extend(data)
        while True:
            if len(self.buffer) < 4:
                return self.messages             # 头不够，等
            length = int.from_bytes(self.buffer[:4], "little")
            if len(self.buffer) < 4 + length:
                return self.messages             # 体不够，等
            body = bytes(self.buffer[4:4 + length])
            del self.buffer[:4 + length]
            self.messages.append(body.decode())


decoder = LengthPrefixDecoder()
decoder.feed(pack_length_prefix("第一")[:5])     # 半包
print(f"  喂半包 -> 输出 {decoder.messages}")
decoder.feed(pack_length_prefix("第一")[5:] + pack_length_prefix("第二"))
print(f"  喂剩余 + 第二条 -> 输出 {decoder.messages}")
print("  状态机模式：buffer 是状态，feed 是转移，吐消息是输出 —— 增量解析")

print("\n== Nagle 与 delayed ACK 的死亡交互 ==")
class NagleSim:
    """Nagle：存在未确认小包时，攒住新的小数据直到 ACK 或凑满 MSS。"""

    def __init__(self, mss=100, delay_ack_slots=2):
        self.mss = mss
        self.delay_slots = delay_ack_slots
        self.unacked = 0
        self.pending = []
        self.sent_log = []

    def write(self, data, slot):
        self.pending.append((slot, data))
        sent_now = []
        while self.pending:
            size = len(self.pending[0][1])
            if self.unacked == 0 or size >= self.mss:
                slot0, d = self.pending.pop(0)
                self.sent_log.append((slot0, d))
                self.unacked = size
                sent_now.append((slot0, d))
            else:
                break                            # Nagle 攒住
        return sent_now

    def on_ack(self):
        self.unacked = 0                        # ACK 到了，Nagle 解锁


nagle = NagleSim()
nagle.write("s", slot=0)
nagle.on_ack()                                  # 对端延迟 2 槽才回 ACK
nagle.write("mall", slot=1)                     # Nagle 攒住
print("  时间线: write 's' → ACK 未回 → write 'mall' 被 Nagle 攒住")
print("  对端 delayed ACK 要 2 槽后才回 → 'mall' 白白多等 2 槽 → 40ms 假死")
print("  对策：客户端设置 TCP_NODELAY（禁 Nagle）；服务端避免延迟 ACK")

print("\n== 心跳消息 ==")
print("  TCP 连接空闲时 NAT/防火墙可能静默回收 —— 应用层心跳保持活性")
print("  心跳也是死连接探测器：2 次心跳无回应即判定断开（比等内核超时快得多）")
print("  协议设计要点：心跳与业务消息共用同一条流，避免第二条连接的认证问题")

print("\n== 小结 ==")
for line in (
    "  『粘包』不是 TCP 的 bug，是『没设计消息边界』的应用层问题",
    "  长度前缀 + 增量状态机解码器是消息协议的工业标准做法",
    "  Nagle/delayed ACK 交互是延迟毛刺的经典来源 —— 知道关哪个开关",
    "  962 课：把本章所有机制拼成迷你 TCP 模拟器",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给长度前缀协议加「消息类型字段」（1 字节 type），实现心跳/数据/控制三种消息。
# 2. 实现「转义分隔符」解析器：内容中的 | 用 \| 转义。
# 3. 用 946 课的属性测试验证解码器：任意字节流喂入不崩溃且往返一致。
# 4. 思考：HTTP/2 的帧设计如何同时解决粘包、优先级与多路复用？
