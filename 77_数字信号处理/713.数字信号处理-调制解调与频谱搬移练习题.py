# ===== 第713课：数字信号处理-调制解调与频谱搬移 =====
# 知识点：
#   - 调制：把低频基带信号搬移到高频载波附近，便于天线辐射/频分复用
#   - AM: s(t) = (1 + k·m(t))·cos(2πf_c t)，包络检波即可解调
#   - DSB-SC / 相干解调：乘同频同相载波再低通，要求载波相位同步
#   - FM/PM：信息藏在频率/相位里，抗幅度噪声但占带宽
#   - IQ 调制：s = I·cos(ωt) - Q·sin(ωt)，可同时传两路，复包络是通用表示
#   - 频谱搬移性质：乘 cos(ωc t) = 频谱左右各移 fc 并减半
# 依赖：无（标准库）
import cmath
import math

FS = 8000.0
N = 512
FC = 1000.0        # 载波
FM = 100.0         # 基带（消息）频率


def carrier(n, fc=FC, fs=FS, phase=0.0):
    return math.cos(2 * math.pi * fc * n / fs + phase)

def baseband(n, fm=FM, fs=FS):
    return math.sin(2 * math.pi * fm * n / fs)

def dft_mag(x, n_pts=None):
    n = n_pts or len(x)
    seg = x[:n]
    return [abs(sum(seg[i] * cmath.exp(-2j * math.pi * k * i / n)
                    for i in range(n))) * 2 / n for k in range(n // 2)]

def peaks(mag, fs=FS, top=4):
    n = len(mag) * 2
    idx = sorted(range(len(mag)), key=lambda k: -mag[k])[:top]
    return [(round(k * fs / n, 1), round(mag[k], 3)) for k in idx]


def lowpass(x, cutoff=300.0, M=41):
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


m = [baseband(n) for n in range(N)]
c = [carrier(n) for n in range(N)]

print("== 基带与载波的频谱 ==")
print("  基带峰值:", peaks(dft_mag(m)))
print("  载波峰值:", peaks(dft_mag(c)))

print("\n== AM 调制（带载波，k=0.6）==")
k = 0.6
am = [(1 + k * m[n]) * c[n] for n in range(N)]
print("  已调信号峰值:", peaks(dft_mag(am), top=5))
print("  应出现载波 fc 与两个边带 fc±fm")
print(f"  理论边带: {FC-FM:.0f}Hz / {FC:.0f}Hz / {FC+FM:.0f}Hz")

print("\n== AM 包络检波（整流 + 低通）==")
rectified = [abs(v) for v in am]
env = lowpass(rectified, cutoff=300)
# 去掉直流并缩放
dc = sum(env) / len(env)
demod = [(v - dc) / (k * 0.5) for v in env]
err = max(abs(a - b) for a, b in zip(demod[100:-100], m[100:-100]))
print(f"  解调波形与基带最大误差≈{err:.3f}（包络检波有纹波与相位延迟）")
print(f"  前 6 点对比: 原={[round(v,2) for v in m[:6]]} "
      f"解调={[round(v,2) for v in demod[:6]]}")

print("\n== DSB-SC 与相干解调 ==")
dsb = [m[n] * c[n] for n in range(N)]
print("  DSB-SC 峰值（无载波峰）:", peaks(dft_mag(dsb), top=4))
# 同频同相相乘，再低通，乘 2 补回幅度
product = [2 * dsb[n] * c[n] for n in range(N)]
recovered = lowpass(product, cutoff=300)
err2 = max(abs(a - b) for a, b in zip(recovered[100:-100], m[100:-100]))
print(f"  相干解调误差≈{err2:.3f}")

print("\n== 相位失步的影响（相干解调的痛点）==")
for phase_deg in (0, 30, 60, 90):
    ph = math.radians(phase_deg)
    c2 = [carrier(n, phase=ph) for n in range(N)]
    prod = [2 * dsb[n] * c2[n] for n in range(N)]
    rec = lowpass(prod, cutoff=300)
    amp = max(rec[100:-100]) - min(rec[100:-100])
    print(f"  相位差 {phase_deg:>3}° -> 解调信号峰峰值={amp:.3f}")
print("  90° 时几乎为零 -> 需要 PLL / Costas 环恢复载波相位")

print("\n== FM：信息在瞬时频率里 ==")
beta = 5.0     # 调制指数
fm_sig = []
phase = 0.0
for n in range(N):
    inst = FC + beta * FM * m[n]           # 瞬时频率随 m 变化
    phase += 2 * math.pi * inst / FS
    fm_sig.append(math.cos(phase))
print(f"  FM 峰值（边带更多、带宽更宽）: {peaks(dft_mag(fm_sig), top=5)}")
print(f"  Carson 规则带宽 ≈ 2(Δf+fm) = 2({beta*FM:.0f}+{FM:.0f}) = {2*(beta*FM+FM):.0f}Hz")
print("  AM 带宽仅 2·fm=200Hz，FM 用带宽换抗噪性")

print("\n== IQ 调制：一路载波传两路数据 ==")
I = [0.8 * math.sin(2*math.pi*100*n/FS) for n in range(N)]
Q = [0.6 * math.cos(2*math.pi*200*n/FS) for n in range(N)]
iq = [I[n]*math.cos(2*math.pi*FC*n/FS) - Q[n]*math.sin(2*math.pi*FC*n/FS)
      for n in range(N)]
# 相干解调恢复 I/Q
rI = lowpass([2*iq[n]*math.cos(2*math.pi*FC*n/FS) for n in range(N)], cutoff=400)
rQ = lowpass([-2*iq[n]*math.sin(2*math.pi*FC*n/FS) for n in range(N)], cutoff=400)
print(f"  I 路恢复误差≈{max(abs(a-b) for a,b in zip(rI[100:-100], I[100:-100])):.3f}")
print(f"  Q 路恢复误差≈{max(abs(a-b) for a,b in zip(rQ[100:-100], Q[100:-100])):.3f}")
print("  复包络 I+jQ 是 QAM/OFDM 的数学基础")

print("\n== 调制方式速查 ==")
print(f"  {'方式':<10}{'信息载体':<14}{'带宽':<12}{'抗噪':<8}{'解调'}")
for row in (("AM", "幅度", "2·fm", "弱", "包络检波(简单)"),
            ("DSB-SC", "幅度", "2·fm", "中", "相干(需同步)"),
            ("FM", "频率", "宽", "强", "鉴频/PLL"),
            ("QAM", "幅度+相位", "2·fm", "中", "IQ 相干")):
    print(f"  {row[0]:<10}{row[1]:<14}{row[2]:<12}{row[3]:<8}{row[4]}")

# ===== 练习题 =====
# 1. 实现 Costas 环的简化版，从 DSB-SC 信号里恢复载波相位。
# 2. 用 IQ 调制实现 QPSK：把比特对映射成 4 个星座点并解调。
# 3. 给 AM 加过调制（k>1），观察包络检波失真（过调幅）。
# 4. 思考：为什么数字通信普遍用 IQ/复包络，而不是直接调制实数载波？
