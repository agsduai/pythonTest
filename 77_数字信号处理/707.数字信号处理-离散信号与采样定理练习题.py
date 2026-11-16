# ===== 第707课：数字信号处理-离散信号与采样定理 =====
# 知识点：
#   - 连续信号 x(t) 按采样率 fs 取样得到离散序列 x[n] = x(n/fs)
#   - 奈奎斯特准则：fs > 2·f_max 才能无失真还原；否则发生混叠 aliasing
#   - 混叠：高频 f 与 f - k·fs 在离散域不可区分（折回低频）
#   - 归一化频率：f/fs（周期/样本），数字角频率 ω = 2πf/fs
#   - 常用信号：正弦、方波、冲激 δ[n]、阶跃 u[n]、指数衰减
#   - 本课用纯 Python 生成序列并打印数值/ASCII 波形，不依赖 NumPy
# 依赖：无（标准库）
import math

FS = 8000.0     # 采样率 Hz


def sine(freq, seconds, fs=FS, amp=1.0, phase=0.0):
    return [amp * math.sin(2 * math.pi * freq * n / fs + phase)
            for n in range(int(fs * seconds))]

def square(freq, seconds, fs=FS):
    return [1.0 if math.sin(2 * math.pi * freq * n / fs) >= 0 else -1.0
            for n in range(int(fs * seconds))]

def impulse(n_len, at=0):
    return [1.0 if n == at else 0.0 for n in range(n_len)]

def step(n_len, at=0):
    return [1.0 if n >= at else 0.0 for n in range(n_len)]

print("== 基本离散序列（前 12 个样本）==")
for name, sig in (("冲激 δ[n]", impulse(12, 3)), ("阶跃 u[n-3]", step(12, 3)),
                  ("1kHz 正弦", sine(1000, 0.0015)), ("1kHz 方波", square(1000, 0.0015))):
    print(f"  {name:<14}: {[round(v, 3) for v in sig[:12]]}")

print("\n== 归一化频率与数字角频率 ==")
for f in (500, 1000, 2000, 4000, 5000):
    print(f"  f={f:>5}Hz  f/fs={f/FS:.3f}  ω={2*math.pi*f/FS:.3f} rad/sample "
          f"{'（超奈奎斯特）' if f >= FS/2 else ''}")

print("\n== 混叠：不同频率采样后完全相同 ==")
# 1000Hz 与 1000+8000=9000Hz 在 fs=8000 下样本一致
x1 = sine(1000, 0.002)
x2 = sine(9000, 0.002)
maxdiff = max(abs(a - b) for a, b in zip(x1, x2))
print(f"  1000Hz vs 9000Hz: 最大样本差={maxdiff:.2e}  -> 离散域无法区分")
# 用「折回」公式求混叠后的表观频率
def alias_freq(f, fs=FS):
    k = round(f / fs)
    return abs(f - k * fs)
for f in (1000, 5000, 7000, 9000, 12000):
    print(f"  {f:>6}Hz @ fs={FS:.0f} -> 表观 {alias_freq(f):.0f}Hz")

print("\n== 采样率不足导致的信息丢失 ==")
# 用 6Hz 采样去观察 5Hz 信号，表观只有 1Hz
def sample_continuous(freq, fs, seconds=1.0):
    return [math.sin(2 * math.pi * freq * n / fs) for n in range(int(fs * seconds))]

for fs in (20, 12, 8, 6):
    seq = sample_continuous(5.0, fs, 0.5)
    apparent = alias_freq(5.0, fs)
    print(f"  fs={fs:>3}Hz 采 5Hz 信号 -> 表观 {apparent:.0f}Hz，"
          f"{'可还原' if fs > 10 else '已混叠'}")

print("\n== ASCII 波形（1kHz 正弦，fs=8000，前 40 样本）==")
x = sine(1000, 0.005)
for row in range(9):
    level = 1.0 - row / 4
    line = "".join("#" if abs(v - level) < 0.25 else " " for v in x[:40])
    print("  " + line)

print("\n== 抗混叠滤波器（采样前必做）==")
for line in (
    "  模拟低通把高于 fs/2 的成分先滤掉，再 ADC",
    "  否则高频噪声会混叠进带内，事后数字滤波救不回来",
    "  过采样（高 fs）+ 数字抽取可放宽模拟滤波器要求",
    "  音频 CD: fs=44.1kHz，模拟滤波截止约 20kHz",
):
    print(" ", line)

print("\n== 常见采样率 ==")
for name, fs, note in (("电话", 8000, "300~3400Hz 语音"),
                       ("CD", 44100, "20kHz 带宽"),
                       ("专业音频", 48000, "视频伴音"),
                       ("高清音频", 96000, "留足过渡带")):
    print(f"  {name:<10} {fs:>6} Hz  {note}")

# ===== 练习题 =====
# 1. 生成 3kHz + 7kHz 混合信号（fs=8kHz），观察 7kHz 混叠成 1kHz。
# 2. 实现 sinc 插值从离散样本还原连续曲线，验证过采样时误差更小。
# 3. 用「零阶保持」与「线性插值」重建方波，对比波形失真。
# 4. 思考：为什么抗混叠滤波必须在 ADC 之前，而不能采样后用数字滤波？
