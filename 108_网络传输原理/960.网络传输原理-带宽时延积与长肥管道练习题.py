# ===== 第960课：网络传输原理-带宽时延积与长肥管道 =====
# 知识点：
#   - 带宽时延积 BDP = 带宽 × RTT：管道里同时飞行的数据总量
#   - 窗口 < BDP → 链路必然跑不满（管道没充满）
#   - 长肥管道（LFN）：BDP 巨大的网络（洲际 10Gbps）→ 需要巨窗口
#   - Mathis 公式：吞吐 ≈ MSS / (RTT × √p) —— 丢包率对吞吐的硬约束
#   - TCP 头部窗口字段 16 位 → 窗口缩放选项（window scaling）的由来
# 依赖：无（标准库）
import math


def bdp_bytes(bandwidth_bps, rtt_seconds):
    return bandwidth_bps * rtt_seconds / 8


def throughput_window(window_bytes, rtt_seconds):
    return window_bytes / rtt_seconds


def mathis_throughput(mss_bytes, rtt_seconds, loss_rate):
    """Mathis et al.：吞吐 ≈ MSS / (RTT·√p)，常数约 1.22。"""
    return 1.22 * mss_bytes / (rtt_seconds * math.sqrt(loss_rate))


print("== 带宽时延积：管道里有多少数据 ==")
print(f"  {'链路':<26}{'带宽':>12}{'RTT':>8}{'BDP':>14}")
scenarios = [
    ("家庭宽带", 100e6, 0.01),
    ("跨城专线", 1e9, 0.02),
    ("洲际 10Gbps", 10e9, 0.15),
    ("卫星链路", 50e6, 0.6),
]
for name, bw, rtt in scenarios:
    b = bdp_bytes(bw, rtt)
    unit = "KB" if b < 1e6 else "MB"
    value = b / 1024 if b < 1e6 else b / 1e6
    print(f"  {name:<26}{bw / 1e9:>10.1f}G{rtt:>7.2f}s{value:>12.1f} {unit}")

print("\n== 窗口不足 = 链路跑不满 ==")
print(f"  {'链路':<20}{'BDP':>10}{'TCP默认窗口(64KB)':>18}{'实际吞吐':>12}")
for name, bw, rtt in scenarios:
    b = bdp_bytes(bw, rtt)
    window = 64 * 1024
    actual = throughput_window(window, rtt)
    print(f"  {name:<20}{b / 1e6:>8.1f}MB{window / 1024:>14.0f}KB"
          f"{actual / 1e6:>10.1f}MB/s")
print("  洲际链路：64KB 窗口只能跑 ~0.4MB/s，而管道能容纳 187MB ——")
print("  这是『长肥管道』问题的本质，窗口缩放选项因此而生")

print("\n== Mathis 公式：丢包率的吞吐税 ==")
print(f"  {'丢包率 p':>10}{'1Gbps/20ms 链路吞吐':>22}")
mss = 1460
for p in (1e-8, 1e-6, 1e-4, 1e-2):
    t = mathis_throughput(mss, 0.02, p)
    print(f"  {p:>10.0e}{t / 1e9:>18.2f} Gbps")
print("  p = 1e-6 时 10Gbps 链路理论上限仅 ~1.7Gbps ——")
print("  高带宽网络必须把丢包率压到 1e-8 以下，或换算法（BBR 不看丢包）")

print("\n== 窗口缩放选项 ==")
print(f"  {'字段':<24}{'说明'}")
for row in (("窗口字段 16 位", "最大 65535 字节"),
            ("缩放因子 0~14", "实际窗口 = 字段值 << 缩放因子"),
            ("最大窗口", "65535 × 2^14 ≈ 1GB"),
            ("协商时机", "三次握手中双方交换各自的缩放因子")):
    print(f"  {row[0]:<24}{row[1]}")

print("\n== BDP 对缓冲区设计的指导 ==")
print("  路由器缓冲太小 → 频繁丢包；太大 → bufferbloat（排队延迟爆炸）")
print("  经典规则：缓冲 ≈ BDP —— 但现代观点（CoDel）认为按『时间』缓冲更对")
print("  10Gbps × 250ms RTT 的 BDP ≈ 312MB —— 巨大缓冲配上 AIMD 就是延迟灾难")

print("\n== 长肥管道的调优清单 ==")
for line in (
    "  1. 开启窗口缩放（默认已开，检查中间盒子是否剥掉）",
    "  2. 端点缓冲 ≥ BDP：send/recv buffer 调大",
    "  3. 拥塞算法换 CUBIC/BBR（传统 AIMD 在 LFN 上爬升太慢）",
    "  4. 监控丢包率：Mathis 曲线告诉你瓶颈在丢包还是在窗口",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  BDP 是网络管道的『容积』：窗口低于它就永远跑不满",
    "  Mathis 公式给出 AIMD 时代的吞吐天花板 —— 丢包即代价",
    "  长肥管道的所有怪问题（慢启动慢、窗口不够、缓冲膨胀）都源于 BDP 巨大",
    "  961 课：回到应用层 —— TCP 字节流的粘包与拆包",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 计算你自己的网络 BDP：测速 + ping RTT，给出推荐缓冲区大小。
# 2. 实现「慢启动爬升到 BDP 所需轮数」计算器（cwnd 指数增长到 BDP/MSS）。
# 3. 绘制 Mathis 曲线：丢包率 1e-8~1e-3 的吞吐对数图（文本刻度）。
# 4. 思考：BBR 为什么把『丢包』换成『带宽与 RTT 的测量』作为拥塞信号？
#    它在拥塞的哪一阶段占优、哪一阶段吃亏？
