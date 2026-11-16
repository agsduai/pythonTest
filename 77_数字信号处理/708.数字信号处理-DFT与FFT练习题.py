# ===== 第708课：数字信号处理-DFT与FFT =====
# 知识点：
#   - DFT: X[k] = Σ x[n]·e^(-j2πkn/N)，把时域序列变成频域复数谱
#   - 逆 DFT: x[n] = (1/N)·Σ X[k]·e^(+j2πkn/N)
#   - 幅度谱 |X[k]|、相位谱 arg(X[k])；k 对应频率 k·fs/N
#   - 朴素 DFT 是 O(N²)；Cooley-Tukey FFT 递归分治降到 O(N log N)
#   - 栅栏效应：只看到 N 个离散频点；谱泄漏靠加窗缓解（第709课）
#   - Python 内置 complex + cmath，无需 NumPy；本课手写两种实现并对比
# 依赖：无（标准库）
import cmath
import math
import time

FS = 8000.0


def dft(x):
    """朴素 DFT，O(N²)。"""
    N = len(x)
    return [sum(x[n] * cmath.exp(-2j * math.pi * k * n / N) for n in range(N))
            for k in range(N)]


def idft(X):
    N = len(X)
    return [sum(X[k] * cmath.exp(2j * math.pi * k * n / N)
                for k in range(N)) / N for n in range(N)]


def fft(x):
    """基 2 Cooley-Tukey FFT（要求 len(x) 为 2 的幂）。"""
    N = len(x)
    if N <= 1:
        return list(x)
    if N % 2:
        raise ValueError("FFT 长度必须是 2 的幂")
    even, odd = fft(x[0::2]), fft(x[1::2])
    out = [0j] * N
    for k in range(N // 2):
        t = cmath.exp(-2j * math.pi * k / N) * odd[k]
        out[k] = even[k] + t
        out[k + N // 2] = even[k] - t
    return out


def spectrum(X, fs=FS):
    """返回前一半的 (频率, 幅度, 相位)。"""
    N = len(X)
    return [(k * fs / N, abs(X[k]) * 2 / N, cmath.phase(X[k]))
            for k in range(N // 2)]


print("== 单频正弦的频谱 ==")
N = 64
f0 = 1000.0
x = [math.sin(2 * math.pi * f0 * n / FS) for n in range(N)]
X_dft, X_fft = dft(x), fft(x)
print(f"  N={N}, f0={f0:.0f}Hz, 频率分辨率={FS/N:.1f}Hz/bin")
maxdiff = max(abs(a - b) for a, b in zip(X_dft, X_fft))
print(f"  DFT 与 FFT 最大差={maxdiff:.2e}（应接近 0）")

peaks = sorted(spectrum(X_fft), key=lambda r: -r[1])[:4]
print("  幅度最大的 4 个频点:")
for f, amp, phase in peaks:
    print(f"    {f:>7.1f}Hz  幅度={amp:.4f}  相位={phase:+.3f} rad")

print("\n== 两个频率叠加 ==")
x2 = [math.sin(2 * math.pi * 1000 * n / FS) +
      0.5 * math.sin(2 * math.pi * 2000 * n / FS) for n in range(N)]
for f, amp, _ in sorted(spectrum(fft(x2)), key=lambda r: -r[1])[:3]:
    print(f"  {f:>7.1f}Hz  幅度={amp:.4f}")
print("  1000Hz≈1.0、2000Hz≈0.5，与构造时一致")

print("\n== 频率不对齐 bin 时：谱泄漏 ==")
f_off = 1125.0       # 不是 125Hz 的整数倍
x3 = [math.sin(2 * math.pi * f_off * n / FS) for n in range(N)]
top = sorted(spectrum(fft(x3)), key=lambda r: -r[1])[:5]
print(f"  真实频率={f_off}Hz，能量散到多个 bin:")
for f, amp, _ in top:
    print(f"    {f:>7.1f}Hz  幅度={amp:.4f}")

print("\n== IDFT 往返 ==")
back = idft(X_fft)
err = max(abs(a.real - b) for a, b in zip(back, x))
print(f"  最大重建误差={err:.2e}（虚部≈0）")

print("\n== 复杂度与实测耗时 ==")
for n in (64, 128, 256, 512, 1024):
    sig = [math.sin(2 * math.pi * 440 * i / FS) for i in range(n)]
    t0 = time.perf_counter(); fft(sig); t_fft = time.perf_counter() - t0
    t0 = time.perf_counter(); dft(sig); t_dft = time.perf_counter() - t0
    print(f"  N={n:>5}: FFT={t_fft*1000:>7.2f}ms  DFT={t_dft*1000:>8.2f}ms  "
          f"加速≈{t_dft/t_fft if t_fft else 0:>5.1f}×")
print("  N=1024 时 O(N²) 已明显变慢；真实音频用 NumPy/SciPy 的 C 实现")

print("\n== 频谱对称性 ==")
X = fft(x)
print(f"  实信号频谱共轭对称: X[1]={X[1]:.3f}, X[N-1]={X[N-1]:.3f}, "
      f"共轭={abs(X[1] - X[N-1].conjugate()) < 1e-9}")
print("  因此只画前 N/2 个点即可（单边谱）")

print("\n== 常见应用 ==")
for line in [
    "  音频均衡/频谱可视化、振动故障诊断、电力系统谐波分析",
    "  OFDM 调制（Wi-Fi/4G/5G）本质就是 IFFT/FFT",
    "  快速卷积：时域卷积 = 频域相乘（第710课）",
    "  谱估计前先加窗、去均值，避免直流与泄漏干扰",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现迭代版（非递归）FFT，避免 Python 递归深度限制。
# 2. 给非 2 的幂长度补零到下一个 2 的幂，观察补零对频谱的影响。
# 3. 用频域相乘实现两个序列的循环卷积，与直接卷积对比。
# 4. 思考：为什么「补零」只能让谱更密，却不能提高真实频率分辨率？
