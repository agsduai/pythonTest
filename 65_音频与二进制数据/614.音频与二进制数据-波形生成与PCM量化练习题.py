# ===== 第614课：音频与二进制数据-波形生成与PCM量化 =====
# 知识点：
#   - 采样：每秒取 RATE 个样本；奈奎斯特准则：RATE 必须 > 2 × 最高频率
#   - 正弦 / 方波 / 三角 / 锯齿：同一个频率，不同谐波，音色不同
#   - 浮点归一化 [-1, 1] -> 16 位 PCM 量化：round(v × 32767)，再 clamp
#   - 量化误差：位深越低噪声越大；8 位约 -48dB，16 位约 -96dB
#   - 包络 ADSR：Attack/Decay/Sustain/Release，避免「咔哒」爆音
#   - 幅度叠加多路时要先降增益再限幅，否则削波失真
# 依赖：无（标准库）
import array
import math
import struct
import sys


def clamp16(v: float) -> int:
    """把 [-1,1] 浮点量化成 16 位有符号整数并限幅。"""
    return max(-32768, min(32767, int(round(v * 32767))))


def osc(kind: str, phase: float) -> float:
    """phase 为 0~1 的归一化相位，返回 [-1,1] 波形值。"""
    if kind == "sine":
        return math.sin(2 * math.pi * phase)
    if kind == "square":
        return 1.0 if phase < 0.5 else -1.0
    if kind == "triangle":
        return 4 * abs(phase - 0.5) - 1.0     # 从 -1 起
    if kind == "saw":
        return 2 * phase - 1.0
    raise ValueError(kind)


def generate(kind: str, freq: float, duration: float, rate: int = 8000, amp: float = 0.8):
    """生成 16 位 PCM 样本（array('h')）。"""
    n = int(rate * duration)
    out = array.array("h")
    for i in range(n):
        phase = (i * freq / rate) % 1.0
        out.append(clamp16(amp * osc(kind, phase)))
    return out


RATE, FREQ, DUR = 8000, 440.0, 0.1
print(f"== 四种波形（{FREQ}Hz，{RATE}Hz 采样，{DUR}s）==")
for kind in ("sine", "square", "triangle", "saw"):
    s = generate(kind, FREQ, DUR, RATE)
    peak = max(abs(v) for v in s)
    print(f"  {kind:<9} 样本数={len(s)} 峰值={peak} 前 8 个={list(s[:8])}")

print("\n== 奈奎斯特准则 ==")
for freq in (1000, 3500, 4000, 5000):
    ok = freq < RATE / 2
    print(f"  {freq:>5}Hz @ {RATE}Hz 采样: {'可表示' if ok else '会混叠（aliasing）'}")

print("\n== 量化误差（位深对比）==")
# 把同一个浮点值量化到不同位深再还原
v = 0.123456
for bits in (4, 8, 12, 16, 24):
    levels = (1 << (bits - 1)) - 1
    q = round(v * levels) / levels
    print(f"  {bits:>2} 位: 量化={q:.6f} 误差={abs(v - q):.2e}")

print("\n== ADSR 包络（Attack/Decay/Sustain/Release）==")
def adsr(i: int, n: int, a=0.1, d=0.1, sustain=0.6, r=0.3) -> float:
    t = i / n
    if t < a:
        return t / a
    if t < a + d:
        return 1 - (1 - sustain) * (t - a) / d
    if t < 1 - r:
        return sustain
    return sustain * max(0.0, (1 - t) / r)

s = generate("sine", 440, 0.5, RATE, amp=1.0)
enveloped = array.array("h", (clamp16(s[i] / 32767 * adsr(i, len(s))) for i in range(len(s))))
print("  包络采样点（前/中/末）:", [round(adsr(i, len(s)), 2) for i in (0, 400, 2000, 3999)])
print(f"  加包络前首尾: {s[0]}, {s[-1]}  -> 加包络后: {enveloped[0]}, {enveloped[-1]}")
print("  首尾趋近 0，可有效消除爆音")

print("\n== 幅度叠加与削波 ==")
a = generate("sine", 440, 0.1, RATE, amp=0.8)
b = generate("sine", 660, 0.1, RATE, amp=0.8)
mixed_bad = array.array("h", (clamp16((x + y) / 32767) for x, y in zip(a, b)))
mixed_ok = array.array("h", (clamp16((x + y) / 32767 * 0.5) for x, y in zip(a, b)))
print(f"  直接相加峰值: {max(abs(v) for v in mixed_bad)}（触顶削波）")
print(f"  先降增益峰值: {max(abs(v) for v in mixed_ok)}（保留波形）")

print("\n== PCM 字节流 ==")
s = generate("sine", 440, 0.01, RATE, amp=0.5)
if sys.byteorder == "big":
    s.byteswap()
raw = s.tobytes()
print("  前 16 字节:", raw[:16].hex(" "))
print("  struct 解回:", struct.unpack("<8h", raw[:16]))

# ===== 练习题 =====
# 1. 生成 220/440/880Hz 三个八度的正弦波，对比一个周期的样本数。
# 2. 实现带线性淡入（前 10% 增益 0->1）的 generate 变体。
# 3. 计算 16 位量化的信噪比理论值（约 6.02×bit + 1.76 dB）并与实测误差比较。
# 4. 思考：为什么采样率固定时，频率越高的音色越「粗糙」？
