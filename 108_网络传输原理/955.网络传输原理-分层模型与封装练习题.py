# ===== 第955课：网络传输原理-分层模型与封装 =====
# 知识点：
#   - 分层：链路帧 → IP 包 → TCP 段 → 应用消息 —— 每层只管自己的头
#   - 封装：应用数据向下逐层加头；解封装：接收端逐层剥头
#   - MTU（典型 1500 字节）：超过就分片 —— 分片是丢包放大的根源
#   - 头部开销：14(以太网) + 20(IP) + 20(TCP) = 54 字节/包
#   - 每层的服务由下层提供，上层不感知实现 —— 分层的价值与代价
# 依赖：无（标准库）


def build_frame(app_data, src_port, dst_port, seq, mtu=1500):
    """自顶向下封装：TCP 段 → IP 包 → 以太网帧。超过 MTU 自动分片。"""
    frames = []
    # IP 头 20 字节 + 以太网头 14 字节 = 34 字节固定开销
    overhead = 20 + 14
    payload_limit = mtu - overhead - 20        # 20 = IP 头
    if payload_limit < 0:
        raise ValueError("MTU 过小")
    for offset in range(0, len(app_data), payload_limit) or [0]:
        chunk = app_data[offset:offset + payload_limit]
        # TCP 头 20 字节：序号按字节偏移递增（重组的依据）
        tcp_header = {"sport": src_port, "dport": dst_port,
                      "seq": seq + offset}
        ip_packet = {"ip_header": {"ttl": 64, "proto": "tcp"},
                     "tcp": {**tcp_header, "payload_len": len(chunk)},
                     "payload": chunk}
        frame = {"eth_header": {"dst_mac": "AA:BB", "src_mac": "CC:DD",
                                "ethertype": 0x0800},
                 "ip": ip_packet}
        frames.append(frame)
    return frames


def unwrap_frames(frames):
    """接收端解封装：逐层剥头，按 seq 重组应用数据。"""
    payloads = []
    for frame in sorted(frames, key=lambda f: f["ip"]["tcp"]["seq"]):
        tcp = frame["ip"]["tcp"]
        payloads.append((tcp["seq"], frame["ip"]["payload"]))
    payloads.sort()
    return "".join(p for _, p in payloads)


def overhead_ratio(frames):
    total = sum(len(f["ip"]["payload"]) for f in frames)
    headers = len(frames) * (20 + 20 + 14)
    return headers / max(total + headers, 1)


print("== 封装演示 ==")
data = "X" * 100
frames = build_frame(data, src_port=52000, dst_port=443, seq=1000)
print(f"  应用数据 {len(data)} 字节 → {len(frames)} 个帧")
f0 = frames[0]
print(f"  帧结构: eth({len(f0['eth_header'])} 字段) → "
      f"ip(ttl={f0['ip']['ip_header']['ttl']}) → "
      f"tcp(seq={f0['ip']['tcp']['seq']}, payload={f0['ip']['tcp']['payload_len']}B)")

print("\n== MTU 分片 ==")
big = "Y" * 3000
frames_big = build_frame(big, 52001, 80, seq=0, mtu=1500)
print(f"  3000 字节数据，MTU=1500 → {len(frames_big)} 个帧")
for i, f in enumerate(frames_big):
    print(f"    帧{i}: seq={f['ip']['tcp']['seq']}, "
          f"payload={f['ip']['tcp']['payload_len']}B")
print(f"  每帧 IP 头带偏移信息，丢一帧 → 整包重传（分片的代价）")

print("\n== 解封装与重组 ==")
import random
rng = random.Random(155)
shuffled = frames_big[:]
rng.shuffle(shuffled)                          # 模拟乱序到达
reassembled = unwrap_frames(shuffled)
print(f"  乱序到达的帧重组成功: {reassembled == big}")
print("  重组依据 TCP 序号 —— 这就是『字节流』抽象的机械保证")

print("\n== 头部开销 ==")
for payload in (10, 100, 1000, 1460):
    fr = build_frame("Z" * payload, 1, 2, 0)
    ratio = overhead_ratio(fr)
    print(f"  payload {payload:>5}B → 头部占比 {ratio:>6.1%}")
print("  小包的头部开销可超过 70% —— Nagle 算法（961 课）因此存在")

print("\n== 分层的价值与代价 ==")
for line in (
    "  价值：每层独立演进（以太网换 Wi-Fi，TCP 不用改）；复用端口复用连接",
    "  代价：每层加头 → 带宽利用率下降；层层校验 → CPU 开销",
    "  分层是『关注点分离』在网络上的投影 —— 与软件分层同构",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  封装/解封装 = 加头/剥头 + 按 seq 重组",
    "  MTU 分片：一刀切出 N 个帧，任一丢失全包重传",
    "  头部开销与 payload 大小成反比 —— 批量化是永恒主题",
    "  956 课：帧会丢 —— 可靠传输的第一课 ARQ",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 VLAN 标签（以太网头插入 4 字节 802.1Q），并更新 MTU 与开销计算。
# 2. 实现「分片重组校验」：随机丢一帧，重组结果与原文比对并报告缺失段。
# 3. 计算 1GB 文件在 MTU=1500 下的帧数与纯头部字节数。
# 4. 思考：为什么 IP 分片被认为是『有害的』？TCP 的 MSS 如何从源头避免它？
