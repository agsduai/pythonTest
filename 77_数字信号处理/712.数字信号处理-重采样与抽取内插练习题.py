# ===== 第712课：数字信号处理-重采样与抽取内插 =====
# 知识点：
#   - 抽取 decimation（降采样）：先低通抗混叠，再每 D 个取 1 个
#   - 内插 interpolation（升采样）：每两点间插 L-1 个零，再低通去镜像
#   - 有理数倍重采样 L/D：先内插 L 倍、再抽取 D 倍，共用同一个低通
#   - 若不做低通，抽取会混叠、内插会留下频谱镜像（ imaging ）
#   - 多相/多级实现可避免「先插零再滤」的无效乘法（生产用 scipy.signal.resample_poly）
#   - 插值核：最近邻 / 线性 / sinc（理想但无限长），权衡质量与成本
# 依赖：无（标准库）
import math

FS = 8000.0


def lowpass(x, cutoff, M=31):
    """简化的滑动 + sinc 低通（教学用 FIR）。"""
    def sinc(v):
        return 1.0 if v == 0 else math.sin(math.pi * v) / (math.pi * v)
    fc = cutoff / FS
    mid = (M - 1) / 2
    h = [2 * fc * sinc(2 * fc * (n - mid)) for n in range(M)]
    s = sum(h)
    h = [v / s for v in h]
    out = []
    for i in range(len(x)):
        acc = 0.0
        for j, hj in enumerate(h):
            idx = i - j + M // 2
            if 0 <= idx < len(x):
                acc += x[idx] * hj
        out.append(acc)
    return out


def decimate(x, D):
    """先抗混叠低通（截止 fs/(2D)），再每 D 取 1。"""
    filtered = lowpass(x, FS / (2 * D))
    return filtered[::D]


def interpolate(x, L):
    """插零 + 低通去镜像（截止原 fs/2）。"""
    up = [0.0] * (len(x) * L)
    up[::L] = x
    return lowpass(up, FS / 2 * 0.9)


def resample(x, L, D):
    return decimate(interpolate(x, L), D)


def nearest(x, positions):
    return [x[min(len(x) - 1, round(p))] for p in positions]

def linear(x, positions):
    out = []
    for p in positions:
        lo = min(int(p), len(x) - 2)
        t = p - lo
        out.append(x[lo] * (1 - t) + x[lo + 1] * t)
    return out

def sinc_interp(x, positions, radius=8):
    out = []
    for p in positions:
        lo, acc = int(p), 0.0
        for n in range(lo - radius, lo + radius + 1):
            if 0 <= n < len(x):
                d = p - n
                w = 1.0 if d == 0 else math.sin(math.pi * d) / (math.pi * d)
                acc += x[n] * w
        out.append(acc)
    return out


print("== 生成测试信号：200Hz + 1500Hz 双音 ==")
x = [math.sin(2*math.pi*200*n/FS) + 0.7*math.sin(2*math.pi*1500*n/FS)
     for n in range(240)]
print(f"  原序列 {len(x)} 样本，fs={FS:.0f}Hz，Nyquist={FS/2:.0f}Hz")

print("\n== 抽取 D=2（新 fs=4000，Nyquist=2000）==")
y2 = decimate(x, 2)
print(f"  输出 {len(y2)} 样本，新 fs={FS/2:.0f}Hz")
print("  1500Hz 仍在新 Nyquist 内，应当保留")
# 用 DFT 找主导频率
def dominant(x, fs, n=256):
    N = min(len(x), n)
    seg = x[:N]
    import cmath
    mags = [abs(sum(seg[i]*cmath.exp(-2j*math.pi*k*i/N) for i in range(N)))
            for k in range(N//2)]
    return max(range(1, len(mags)), key=lambda k: mags[k]) * fs / N
print(f"  主导频率≈{dominant(y2, FS/2):.0f}Hz")

print("\n== 抽取 D=4（新 fs=2000，Nyquist=1000）==")
y4 = decimate(x, 4)
print(f"  输出 {len(y4)} 样本，新 fs={FS/4:.0f}Hz，Nyquist={FS/8:.0f}Hz")
print("  1500Hz 已在 Nyquist 之外，抗混叠低通应先把它滤掉")
print(f"  主导频率≈{dominant(y4, FS/4):.0f}Hz（应接近 200Hz，而不是混叠后的 500Hz）")

print("\n== 不做抗混叠直接抽取的后果 ==")
naive = x[::4]
print(f"  直接每 4 取 1 的主导频率≈{dominant(naive, FS/4):.0f}Hz")
print("  1500Hz 混叠成 |1500-2000|=500Hz，污染了频谱")

print("\n== 内插 L=3（插零 + 低通）==")
up = interpolate(x[:60], 3)
print(f"  60 -> {len(up)} 样本，新 fs={FS*3:.0f}Hz")
zero_stuffed = [0.0] * (60 * 3)
zero_stuffed[::3] = x[:60]
print(f"  插零后片段: {[round(v, 3) for v in zero_stuffed[:9]]}（零值会形成频谱镜像）")
print(f"  低通后前 6 个样本: {[round(v, 3) for v in up[:6]]}（零被平滑成真实值）")

print("\n== 有理数倍重采样 3/2 ==")
r = resample(x[:60], 3, 2)
print(f"  60 -> {len(r)} 样本（约 60*3/2=90），实际 {len(r)}")

print("\n== 三种插值核对比（在半样本位置）==")
short = [math.sin(2*math.pi*200*n/FS) for n in range(20)]
positions = [i + 0.5 for i in range(10)]
truth = [math.sin(2*math.pi*200*p/FS) for p in positions]
for name, fn in (("最近邻", lambda: nearest(short, positions)),
                 ("线性", lambda: linear(short, positions)),
                 ("sinc(r=8)", lambda: sinc_interp(short, positions))):
    vals = fn()
    err = max(abs(a-b) for a, b in zip(vals, truth))
    print(f"  {name:<12} 最大误差={err:.5f}")
print("  sinc 最接近理想重建，但计算量最大且边界需特殊处理")

print("\n== 多级抽取为何更省 ==")
for line in (
    "  单级 D=48：需要极窄过渡带的低通，阶数可能上千",
    "  分成 D=2,3,2,2,2 五级：每级过渡带都很宽，总阶数大幅下降",
    "  先在低采样率侧滤波可省掉大量乘法",
    "  CIC 滤波器专做整数倍抽取，无需乘法器，常用于 ADC 后端",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  抽取前必抗混叠、内插后必去镜像，两个低通不能省",
    "  L/D 用互质整数表示；无理数比率用多项式/样条插值近似",
    "  音频重采样要关注通带纹波与相位（线性相位 FIR 更安全）",
    "  生产用 scipy.signal.resample_poly / libsamplerate",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现多级抽取（D=8 拆成 2×2×2），对比单级的计算量。
# 2. 给 sinc_interp 加 Lanczos 窗，观察边界振铃是否减弱。
# 3. 重采样一个扫频信号（chirp），检查各频段是否保持幅度。
# 4. 思考：为什么「先插零再低通」比「先低通再插零」便宜得多？
