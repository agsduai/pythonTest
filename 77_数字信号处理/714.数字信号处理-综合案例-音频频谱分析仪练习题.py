# ===== 第714课：数字信号处理-综合案例-音频频谱分析仪 =====
# 知识点：
#   - 综合串起本章：采样 -> 去直流 -> 加窗 -> FFT -> 功率谱 -> 峰值检测 -> 报表
#   - STFT：把长信号分帧、逐帧加窗做 FFT，得到时频谱图（spectrogram）
#   - Welch 平均周期图：多段谱平均，方差更小，适合噪声背景下的谱估计
#   - 峰值检测：局部极大 + 幅度阈值 + 二次插值细化频率（bin 间估计）
#   - 分帧参数：帧长 N 决定频率分辨率 fs/N，帧移 hop 决定时间分辨率
#   - 纯标准库 + 内存信号，输出文本频谱图与结构化报告，离线可运行
# 依赖：无（标准库）
import cmath
import math
import random
from dataclasses import dataclass, field

FS = 8000.0


def fft(x):
    N = len(x)
    if N == 1:
        return list(x)
    e, o = fft(x[0::2]), fft(x[1::2])
    out = [0j] * N
    for k in range(N // 2):
        t = cmath.exp(-2j * math.pi * k / N) * o[k]
        out[k], out[k + N // 2] = e[k] + t, e[k] - t
    return out


def hann(n):
    return [0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]


def frame_spectrum(frame, window=None):
    n = len(frame)
    w = window or [1.0] * n
    gain = sum(w) / n
    seg = [frame[i] * w[i] for i in range(n)]
    # 去直流
    mean = sum(seg) / n
    seg = [v - mean for v in seg]
    X = fft(seg)
    return [abs(X[k]) * 2 / (n * gain) for k in range(n // 2)]


def welch(signal, n=256, hop=128):
    """分段加 Hann 窗，平均功率谱。"""
    w = hann(n)
    acc, count = [0.0] * (n // 2), 0
    for start in range(0, len(signal) - n + 1, hop):
        mag = frame_spectrum(signal[start:start + n], w)
        for k, v in enumerate(mag):
            acc[k] += v * v
        count += 1
    return [a / count for a in acc], count


def find_peaks(power, fs=FS, n=256, threshold=0.01, top=5):
    """局部极大 + 抛物线插值细化 bin 位置。"""
    out = []
    for k in range(1, len(power) - 1):
        if power[k] > power[k-1] and power[k] > power[k+1] and power[k] > threshold:
            a, b, c = power[k-1], power[k], power[k+1]
            denom = a - 2*b + c
            delta = 0.5 * (a - c) / denom if denom else 0.0
            freq = (k + delta) * fs / n
            out.append((freq, math.sqrt(power[k])))
    return sorted(out, key=lambda x: -x[1])[:top]


def ascii_spectrum(mag, width=48, height=10):
    """用字符画粗略显示幅度谱（对数刻度）。"""
    n = len(mag)
    bars = []
    for i in range(width):
        lo, hi = int(i * n / width), max(int(i * n / width) + 1, int((i+1) * n / width))
        v = max(mag[lo:hi])
        bars.append(20 * math.log10(v + 1e-9))
    lo, hi = min(bars), max(bars)
    scale = (hi - lo) or 1
    rows = []
    for row in range(height, 0, -1):
        level = lo + scale * row / height
        rows.append("".join("#" if b >= level else " " for b in bars))
    return rows


@dataclass
class Analyzer:
    fs: float = FS
    n_fft: int = 256
    hop: int = 128
    frames: list = field(default_factory=list)

    def stft(self, signal):
        w = hann(self.n_fft)
        self.frames = []
        for start in range(0, len(signal) - self.n_fft + 1, self.hop):
            self.frames.append(frame_spectrum(signal[start:start + self.n_fft], w))
        return self.frames

    def dominant_track(self):
        """每帧最大幅度对应的频率，观察随时间变化。"""
        out = []
        for fr in self.frames:
            k = max(range(1, len(fr)), key=lambda i: fr[i])
            out.append(k * self.fs / self.n_fft)
        return out


# ---- 构造信号：前段 440Hz，后段 880Hz，叠加噪声 ----
r = random.Random(11)
signal = []
for i in range(4096):
    f = 440.0 if i < 2048 else 880.0
    signal.append(0.8 * math.sin(2 * math.pi * f * i / FS) +
                  0.25 * math.sin(2 * math.pi * 1500 * i / FS) +
                  r.gauss(0, 0.08))

print("== 信号参数 ==")
print(f"  采样率={FS:.0f}Hz 样本数={len(signal)} 时长={len(signal)/FS:.2f}s")
print(f"  成分: 0-2048 样本 440Hz，2048-4096 样本 880Hz，全程 1500Hz + 噪声")
print(f"  FFT={256} 点 -> 频率分辨率={FS/256:.1f}Hz/bin")

print("\n== STFT 分帧 ==")
a = Analyzer()
frames = a.stft(signal)
print(f"  帧数={len(frames)} 帧移={a.hop} 样本({a.hop/FS*1000:.0f}ms)")
track = a.dominant_track()
print("  各帧主导频率 (每 4 帧取 1):", [round(track[i]) for i in range(0, len(track), 4)])
print("  可见中段从 ~440Hz 跳到 ~880Hz")

print("\n== Welch 平均功率谱的峰值 ==")
power, count = welch(signal, n=256, hop=128)
print(f"  平均段数={count}")
for f, amp in find_peaks(power, fs=FS, n=256, threshold=0.002, top=5):
    print(f"    {f:>8.1f} Hz  幅度≈{amp:.4f}")
print("  440/880/1500Hz 三个成分都应被检出（440 与 880 各占一半时间，幅度约减半）")

print("\n== 单帧频谱（ASCII，对数幅度）==")
frame = frames[len(frames)//2 - 4]      # 跳变前的 440Hz 帧
for row in ascii_spectrum(frame, width=56, height=8):
    print("  |" + row + "|")
print("  +" + "-" * 56 + "+")
for hz in (0, 1000, 2000, 3000, 4000):
    pos = int(hz / (FS/2) * 56)
    print(f"  {hz}Hz 位于第 {pos} 列附近")

print("\n== 分段分析（前/后半段各自 Welch）==")
for label, seg in (("前半段", signal[:2048]), ("后半段", signal[2048:])):
    p, _ = welch(seg, n=256, hop=128)
    peaks = find_peaks(p, fs=FS, n=256, threshold=0.01, top=2)
    print(f"  {label}: {[(round(f), round(amp, 3)) for f, amp in peaks]}")

print("\n== 参数权衡 ==")
print(f"  {'N_FFT':<8}{'频率分辨率':<16}{'时间分辨率':<16}{'适用'}")
for n, note in ((128, "暂态/快速变化"), (256, "折中"), (1024, "相近频率分辨")):
    print(f"  {n:<8}{FS/n:<16.1f}{n/FS*1000:<16.1f}{note}")
print("  时频不可兼得：N 大频率准但时间糊（海森堡式权衡）")

print("\n== 流水线回顾 ==")
for line in [
    "  采样/去直流: 消除 k=0 直流峰（第707课）",
    "  分帧 + 加窗: 抑制谱泄漏（第709课）",
    "  FFT        : O(N log N) 求幅度谱（第708课）",
    "  Welch 平均 : 多段功率谱平均降方差（第680课统计思想）",
    "  峰值细化   : 抛物线插值突破 bin 分辨率",
    "  输出       : 文本频谱图 + 结构化峰值表（第665课多格式思路）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 把 ASCII 频谱图换成按频段（倍频程）聚合的柱状图。
# 2. 实现谱质心 / 谱平坦度两个音频特征，用于区分语音与音乐。
# 3. 用 STFT + 逆变换做「时变滤波」，验证能重建原信号（重叠相加）。
# 4. 思考：为什么 STFT 的帧长不能同时给最高的时间与频率分辨率？
