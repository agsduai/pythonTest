# ===== 第710课：数字信号处理-卷积与线性滤波器 =====
# 知识点：
#   - 线性卷积 y[n] = Σ x[k]·h[n-k]；长度 = len(x)+len(h)-1
#   - FIR 滤波器：h 有限长，永远稳定；IIR 用反馈，可能不稳定
#   - 移动平均是最简单的低通 FIR：h[n]=1/M，平滑高频噪声
#   - 差分器 y[n]=x[n]-x[n-1] 是高通，突出突变
#   - 冲激响应 h、频率响应 H(ω) 是一对 DFT；滤波 = 频域相乘
#   - 卷积的三种实现：直接 O(NM)、用 FFT O(N log N)、递推（滑动窗口 O(N)）
# 依赖：无（标准库）
import cmath
import math
import time

FS = 8000.0


def convolve(x, h):
    """直接线性卷积。"""
    out = [0.0] * (len(x) + len(h) - 1)
    for i, xi in enumerate(x):
        for j, hj in enumerate(h):
            out[i + j] += xi * hj
    return out


def moving_average(x, m):
    """O(N) 滑动窗口实现（等价于与 1/m 矩形窗卷积）。"""
    out, acc = [], 0.0
    for i, v in enumerate(x):
        acc += v
        if i >= m:
            acc -= x[i - m]
        out.append(acc / min(i + 1, m))
    return out


def fir_apply(x, h):
    return convolve(x, h)[:len(x)]


def iir_lowpass(x, alpha):
    """一阶 IIR: y[n] = (1-α)x[n] + α·y[n-1]。"""
    out, prev = [], 0.0
    for v in x:
        prev = (1 - alpha) * v + alpha * prev
        out.append(prev)
    return out


def highpass_diff(x):
    return [x[0]] + [x[i] - x[i-1] for i in range(1, len(x))]


def freq_response(h, n_pts=64):
    """用 DTFT 采样估计频率响应幅度。"""
    out = []
    for k in range(n_pts // 2):
        w = 2 * math.pi * k / n_pts
        H = sum(hj * cmath.exp(-1j * w * n) for n, hj in enumerate(h))
        out.append((k * FS / n_pts, abs(H)))
    return out


print("== 卷积基础 ==")
x = [1, 2, 3]
h = [1, -1]
print(f"  x={x} h={h} -> {convolve(x, h)}")
print("  冲激响应 δ 卷积应还原原信号:", convolve(x, [1])[:3] == x)

print("\n== 频率响应：移动平均是低通 ==")
for m in (3, 8, 16):
    h_ma = [1 / m] * m
    resp = freq_response(h_ma)
    low, high = resp[2][1], resp[-1][1]
    print(f"  M={m:>2}: |H(250Hz)|={low:.3f} |H(3906Hz)|={high:.3f} "
          f"高频衰减={20*math.log10(high/low) if low else 0:.1f}dB")

print("\n== 差分器是高通 ==")
resp = freq_response([1, -1])
print(f"  |H(0Hz)|={resp[0][1]:.3f} |H(1000Hz)|={resp[8][1]:.3f} "
      f"|H(3906Hz)|={resp[-1][1]:.3f}")
print("  直流被完全抑制，高频被放大 -> 边缘/突变检测")

print("\n== 三种实现的结果一致性 ==")
sig = [math.sin(2 * math.pi * 200 * i / FS) +
       0.6 * math.sin(2 * math.pi * 2500 * i / FS) for i in range(200)]
h_ma = [1 / 8] * 8
direct = fir_apply(sig, h_ma)
sliding = moving_average(sig, 8)
diff = max(abs(a - b) for a, b in zip(direct[7:], sliding[7:]))
print(f"  直接卷积 vs 滑动窗口（稳态部分）最大差={diff:.2e}")
iir = iir_lowpass(sig, 0.9)
print(f"  IIR(α=0.9) 输出范围=[{min(iir):.3f}, {max(iir):.3f}]")

print("\n== 去噪效果（信噪比改善）==")
clean = [math.sin(2 * math.pi * 200 * i / FS) for i in range(500)]
import random
r = random.Random(7)
noisy = [c + r.uniform(-0.5, 0.5) for c in clean]
def snr(reference, measured):
    sig_p = sum(v*v for v in reference)
    err_p = sum((a-b)**2 for a, b in zip(reference, measured))
    return 10 * math.log10(sig_p / err_p) if err_p else float("inf")
print(f"  加噪后 SNR = {snr(clean, noisy):.2f} dB")
for method, y in (("MA(8)", moving_average(noisy, 8)),
                  ("MA(16)", moving_average(noisy, 16)),
                  ("IIR(0.9)", iir_lowpass(noisy, 0.9))):
    print(f"  {method:<10} -> SNR = {snr(clean, y):.2f} dB")
print("  平滑越强噪声越小，但信号本身也被削弱/延迟")

print("\n== 卷积与 FFT 加速 ==")
def fft_convolve(x, h):
    n = 1
    while n < len(x) + len(h) - 1:
        n *= 2
    def fft(a):
        N = len(a)
        if N == 1: return list(a)
        e, o = fft(a[0::2]), fft(a[1::2])
        out = [0j] * N
        for k in range(N//2):
            t = cmath.exp(-2j*math.pi*k/N) * o[k]
            out[k], out[k+N//2] = e[k]+t, e[k]-t
        return out
    def ifft(A):
        N = len(A)
        if N == 1: return list(A)
        e, o = ifft(A[0::2]), ifft(A[1::2])
        out = [0j] * N
        for k in range(N//2):
            t = cmath.exp(2j*math.pi*k/N) * o[k]
            out[k], out[k+N//2] = e[k]+t, e[k]-t
        return out
    X, H = fft(list(x) + [0]*(n-len(x))), fft(list(h) + [0]*(n-len(h)))
    y = ifft([a*b for a, b in zip(X, H)])
    return [v.real / n for v in y[:len(x)+len(h)-1]]

big = [math.sin(i * 0.1) for i in range(256)]
t0 = time.perf_counter(); c1 = convolve(big, h_ma); t_direct = time.perf_counter() - t0
t0 = time.perf_counter(); c2 = fft_convolve(big, h_ma); t_fft = time.perf_counter() - t0
err = max(abs(a-b) for a, b in zip(c1, c2))
print(f"  N=256, M=8: 直接={t_direct*1000:.2f}ms FFT={t_fft*1000:.2f}ms "
      f"结果最大差={err:.2e}")
print("  短滤波器直接算更快；长滤波器（M>64）才值得用 FFT")

print("\n== FIR vs IIR ==")
for line in (
    "  FIR: 有限冲激、永远稳定、可做到严格线性相位；阶数高时计算量大",
    "  IIR: 用反馈，低阶即可获得陡峭滚降；可能不稳定、相位非线性",
    "  线性相位对音频/图像重要（不产生相位失真），优先 FIR",
    "  实时性优先且相位不敏感（如仪表平滑），IIR 更省",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 设计一个简单的带通 FIR（低通减低通），并画出频率响应。
# 2. 实现「零相位滤波」：正反各滤一次（filtfilt），对比相位延迟。
# 3. 用 FFT 卷积实现长回声效果（h 含一个延迟脉冲），与第615课对比。
# 4. 思考：为什么 iir_lowpass 的 α 越接近 1 越平滑，但响应也越慢？
