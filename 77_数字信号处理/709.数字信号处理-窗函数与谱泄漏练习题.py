# ===== 第709课：数字信号处理-窗函数与谱泄漏 =====
# 知识点：
#   - 有限长截取 = 乘矩形窗；时域截断让频谱产生旁瓣，能量漏到邻近 bin
#   - 加窗（ taper ）压低旁瓣，代价是主瓣变宽（频率分辨率略降）
#   - 常用窗：矩形 / Hann / Hamming / Blackman / Bartlett，旁瓣依次更低
#   - 幅度需归一化（相干增益 correction），否则加窗后峰值偏低
#   - 窗选择权衡：检测弱信号要低旁瓣，分辨相近频率要窄主瓣
#   - 本课用 DFT 直接量化「旁瓣电平」与「主瓣宽度」
# 依赖：无（标准库）
import cmath
import math

FS, N = 8000.0, 64


def window(kind, n):
    if kind == "rect":
        return [1.0] * n
    if kind == "bartlett":
        return [1 - abs(2 * i / (n - 1) - 1) for i in range(n)]
    if kind == "hann":
        return [0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]
    if kind == "hamming":
        return [0.54 - 0.46 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]
    if kind == "blackman":
        return [0.42 - 0.59 * math.cos(2 * math.pi * i / (n - 1)) +
                0.08 * math.cos(4 * math.pi * i / (n - 1)) for i in range(n)]
    raise ValueError(kind)


def dft_mag(x):
    n = len(x)
    return [abs(sum(x[i] * cmath.exp(-2j * math.pi * k * i / n)
                    for i in range(n))) * 2 / n for k in range(n // 2)]


def analyze_window(kind, f_off=1125.0):
    w = window(kind, N)
    gain = sum(w) / N                 # 相干增益
    x = [math.sin(2 * math.pi * f_off * i / FS) * w[i] for i in range(N)]
    mag = [m / gain for m in dft_mag(x)]   # 幅度校正
    peak = max(range(len(mag)), key=lambda k: mag[k])
    peak_val = mag[peak]
    # 旁瓣：峰值两侧，跳过主瓣附近 3 个 bin
    sidelobes = [m for k, m in enumerate(mag) if abs(k - peak) > 3]
    return {
        "gain": gain,
        "peak_bin": peak,
        "peak": peak_val,
        "max_sidelobe": max(sidelobes) if sidelobes else 0,
        "sidelobe_db": 20 * math.log10(max(sidelobes) / peak_val) if sidelobes and peak_val else 0,
    }


print("== 窗函数形状（N=16，归一化到 0~1）==")
for kind in ("rect", "bartlett", "hann", "hamming", "blackman"):
    w = window(kind, 16)
    bars = "".join("▁▂▃▄▅▆▇█"[min(7, int(v * 7.99))] for v in w)
    print(f"  {kind:<10} {bars}  端点={w[0]:.2f}/{w[-1]:.2f}")

print("\n== 相干增益（加窗后峰值会变低，需校正）==")
for kind in ("rect", "bartlett", "hann", "hamming", "blackman"):
    r = analyze_window(kind)
    print(f"  {kind:<10} 增益={r['gain']:.3f} 校正后峰值={r['peak']:.4f}")

print("\n== 谱泄漏：非整周期 1125Hz 的旁瓣电平 ==")
print(f"  {'窗':<12}{'峰值bin':>9}{'峰值':>10}{'最大旁瓣':>11}{'旁瓣(dB)':>11}")
for kind in ("rect", "bartlett", "hann", "hamming", "blackman"):
    r = analyze_window(kind)
    print(f"  {kind:<12}{r['peak_bin']:>9}{r['peak']:>10.4f}"
          f"{r['max_sidelobe']:>11.4f}{r['sidelobe_db']:>11.1f}")
print("  矩形窗旁瓣最高（-13dB 量级），Blackman 最低，但主瓣更宽")

print("\n== 两个相近频率的分辨能力 ==")
def can_resolve(kind, f1=1000.0, f2=1125.0):
    w = window(kind, N)
    gain = sum(w) / N
    x = [(math.sin(2 * math.pi * f1 * i / FS) +
          math.sin(2 * math.pi * f2 * i / FS)) * w[i] for i in range(N)]
    mag = [m / gain for m in dft_mag(x)]
    # 看两个目标 bin(8 和 9) 附近是否形成两个局部峰
    peaks = [k for k in range(1, len(mag) - 1)
             if mag[k] > mag[k-1] and mag[k] > mag[k+1] and mag[k] > 0.15]
    return peaks, [round(mag[k], 3) for k in peaks]

for kind in ("rect", "hann", "blackman"):
    peaks, vals = can_resolve(kind)
    print(f"  {kind:<10} 检出峰 bin={peaks} 幅度={vals}")
print("  强窗把主瓣展宽，两个靠得近的峰可能粘成一个 -> 分辨率换动态范围")

print("\n== 窗选择速查 ==")
print(f"  {'窗':<12}{'旁瓣':<12}{'主瓣宽度':<14}{'典型用途'}")
for row in (("rect", "-13 dB", "最窄(2 bins)", "整周期采样、暂态"),
            ("bartlett", "-26 dB", "4 bins", "一般用途"),
            ("hann", "-31 dB", "4 bins", "通用谱分析"),
            ("hamming", "-43 dB", "4 bins", "语音/窄带"),
            ("blackman", "-58 dB", "6 bins", "检测弱信号")):
    print(f"  {row[0]:<12}{row[1]:<12}{row[2]:<14}{row[3]}")

print("\n== 幅度/功率校正 ==")
for line in (
    "  相干增益 CG = mean(w)，单频幅度读数除以 CG",
    "  噪声功率要除以 非相干增益 mean(w²)（ENBW）",
    "  用错校正系数会让不同窗的谱没法直接比较",
    "  scipy.signal.get_window / flattop 窗可做更精确的幅值测量",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  先去直流（减均值），否则 k=0 的直流峰会压住其他成分",
    "  整周期采样时矩形窗反而最准，不必盲目加窗",
    "  加窗 + 补零 + 平均（Welch）是谱估计的标准组合",
    "  窗只缓解泄漏，不能消除采样率不足造成的真实混叠",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Welch 方法：分段加窗 + 平均周期图，观察噪声谱变平滑。
# 2. 用 flat-top 窗测量幅度，对比 Hann 窗的幅值误差。
# 3. 画出各窗的频谱（对窗本身做 DFT），实测主瓣宽度与旁瓣电平。
# 4. 思考：为什么「压低旁瓣」和「窄主瓣」不可兼得？
