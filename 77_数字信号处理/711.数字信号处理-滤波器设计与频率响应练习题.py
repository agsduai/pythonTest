# ===== 第711课：数字信号处理-滤波器设计与频率响应 =====
# 知识点：
#   - 由「理想频率响应」反推 FIR 系数：窗函数法（windowed-sinc）
#   - 理想低通冲激响应 h[n] = 2fc/fs · sinc(2fc·n/fs)，无限长且非因果
#   - 截断 + 加窗 + 移位（群延迟 = (M-1)/2）得到可用 FIR
#   - 四种基本响应：低通 / 高通 / 带通 / 带阻，可由低通变换得到
#   - 过渡带宽度与窗长成反比；阻带衰减由窗类型决定（第709课）
#   - 频率响应 H(ω)=Σ h[n]e^(-jωn)，用 DTFT 采样评估设计是否达标
# 依赖：无（标准库）
import cmath
import math

FS = 8000.0


def sinc(x):
    return 1.0 if x == 0 else math.sin(math.pi * x) / (math.pi * x)


def window(kind, n):
    if kind == "rect":
        return [1.0] * n
    if kind == "hann":
        return [0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]
    if kind == "hamming":
        return [0.54 - 0.46 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]
    if kind == "blackman":
        return [0.42 - 0.59 * math.cos(2 * math.pi * i / (n - 1)) +
                0.08 * math.cos(4 * math.pi * i / (n - 1)) for i in range(n)]
    raise ValueError(kind)


def design_lowpass(cutoff, M=31, win="hamming"):
    """窗函数法设计低通 FIR，返回 M 个系数。"""
    fc = cutoff / FS
    mid = (M - 1) / 2
    w = window(win, M)
    h = [2 * fc * sinc(2 * fc * (n - mid)) * w[n] for n in range(M)]
    s = sum(h)
    return [v / s for v in h]          # 归一化使 H(0)=1


def spectral_inversion(h):
    """高通 = δ - 低通（频谱反转）。"""
    out = [-v for v in h]
    out[len(h) // 2] += 1.0
    return out


def freq_response(h, n_pts=256):
    out = []
    for k in range(n_pts // 2 + 1):
        w = 2 * math.pi * k / n_pts
        H = sum(hj * cmath.exp(-1j * w * n) for n, hj in enumerate(h))
        out.append((k * FS / n_pts, abs(H)))
    return out


def db(v):
    return 20 * math.log10(max(v, 1e-12))


def report(name, h, bands):
    resp = freq_response(h)
    print(f"  {name}")
    for lo, hi, label in bands:
        vals = [v for f, v in resp if lo <= f <= hi]
        print(f"    {label:<10} [{lo:>5.0f},{hi:>5.0f}]Hz  "
              f"平均增益={db(sum(vals)/len(vals)):>7.1f}dB  "
              f"最小={db(min(vals)):>7.1f}dB")


print("== 低通 FIR：31 阶，截止 1000Hz ==")
lp = design_lowpass(1000, M=31, win="hamming")
print("  系数前 8 个:", [round(v, 4) for v in lp[:8]])
print(f"  系数和={sum(lp):.6f}（DC 增益归一化）")
report("低通 h[n]", lp, [(0, 800, "通带"), (1000, 1400, "过渡带"),
                          (2000, 4000, "阻带")])

print("\n== 窗长 M 对过渡带的影响 ==")
for M in (11, 21, 41, 81):
    h = design_lowpass(1000, M=M)
    resp = freq_response(h)
    # 找 -3dB 点
    cut = next((f for f, v in resp if v < 0.7079), FS/2)
    stop = max(v for f, v in resp if f > 1500)
    print(f"  M={M:>3}: -3dB 点≈{cut:>6.1f}Hz  阻带峰值={db(stop):>7.1f}dB  "
          f"群延迟={(M-1)/2/FS*1000:.2f}ms")
print("  M 越大过渡带越窄，但延迟与计算量线性增加")

print("\n== 窗类型对阻带衰减的影响 ==")
for win in ("rect", "hann", "hamming", "blackman"):
    h = design_lowpass(1000, M=41, win=win)
    stop = max(v for f, v in freq_response(h) if f > 1500)
    print(f"  {win:<10}: 阻带峰值={db(stop):>7.1f}dB")
print("  与第709课结论一致：Blackman 旁瓣最低，但主瓣最宽")

print("\n== 高通：频谱反转 ==")
hp = spectral_inversion(lp)
report("高通 h[n]", hp, [(0, 500, "阻带"), (1500, 4000, "通带")])

print("\n== 带通 / 带阻（由两个低通组合）==")
# 带通 = 低通(f2) - 低通(f1)
lp1, lp2 = design_lowpass(800, 41), design_lowpass(2000, 41)
bp = [a - b for a, b in zip(lp2, lp1)]
# 带阻 = 低通(f1) + 高通(f2) = δ - 带通
bs = [-v for v in bp]
bs[len(bs)//2] += 1.0
report("带通 800~2000Hz", bp, [(0, 500, "低阻带"), (1200, 1600, "通带"),
                                (2500, 4000, "高阻带")])
report("带阻 800~2000Hz", bs, [(0, 500, "通带"), (1200, 1600, "阻带"),
                                (2500, 4000, "通带")])

print("\n== 设计规格表 ==")
print(f"  {'参数':<14}{'影响':<28}{'代价'}")
for row in (("截止频率 fc", "通带范围", "—"),
            ("阶数 M", "过渡带宽度 ∝ 1/M", "延迟与乘法次数 ↑"),
            ("窗类型", "阻带衰减 / 旁瓣", "主瓣宽度 ↑"),
            ("采样率 fs", "可表示最高频率 fs/2", "数据量 ↑")):
    print(f"  {row[0]:<14}{row[1]:<28}{row[2]}")

print("\n== 工程要点 ==")
for line in [
    "  设计前先明确：通带纹波、阻带衰减、过渡带宽、允许延迟",
    "  FIR 系数量化到定点时要注意精度损失与 DC 增益漂移",
    "  IIR 设计（Butterworth/Chebyshev）用 scipy.signal.butter 更省阶数",
    "  实时滤波用环形缓冲区保存最近 M 个样本，避免每帧复制",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现等纹波（Parks-McClellan）设计的思路对比，说明与窗函数法的差异。
# 2. 给 FIR 加线性相位验证：检查系数是否关于中心对称。
# 3. 设计一个 50Hz 陷波滤波器，演示滤除工频干扰。
# 4. 思考：为什么理想低通滤波器物理上不可实现（非因果 + 无限长）？
