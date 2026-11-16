# ===== 第615课：音频与二进制数据-混音与音频效果 =====
# 知识点：
#   - 混音：多路样本按权重相加，先降增益再 clamp，避免削波
#   - 归一化：先求峰值，再整体缩放到目标电平（如 -1dBFS）
#   - 淡入淡出：逐样本乘线性/指数增益曲线
#   - 延迟/回声：y[n] = x[n] + a·x[n-d]；反馈型 echo 用 y[n] = x[n] + a·y[n-d]
#   - 低通滤波：一阶 IIR y[n] = (1-α)x[n] + α·y[n-1]，α 越大越平滑
#   - 所有处理都在 int16 域操作时，中间结果先转 float 再限幅
# 依赖：无（标准库）
import array
import math
import sys


def clamp16(v: float) -> int:
    return max(-32768, min(32767, int(round(v * 32767))))


def tone(freq, dur, rate=8000, amp=0.5):
    return array.array("h", (
        clamp16(amp * math.sin(2 * math.pi * freq * i / rate))
        for i in range(int(rate * dur))
    ))


def to_float(s):
    return [v / 32767 for v in s]


def to_pcm(values):
    return array.array("h", (clamp16(v) for v in values))


RATE = 8000
x = tone(440, 0.3, RATE)
y = tone(660, 0.3, RATE)

print("== 混音（加权相加）==")
mixed = to_pcm([(a + b) * 0.5 for a, b in zip(to_float(x), to_float(y))])
print(f"  路 A 峰值={max(abs(v) for v in x)} 路 B 峰值={max(abs(v) for v in y)}")
print(f"  混音峰值={max(abs(v) for v in mixed)}（各降 50% 后不削波）")

print("\n== 归一化到目标峰值 ==")
def normalize(s, target=0.9):
    f = to_float(s)
    peak = max(abs(v) for v in f) or 1.0
    return to_pcm([v / peak * target for v in f]), peak

quiet = tone(440, 0.1, RATE, amp=0.05)
loud, before = normalize(quiet)
print(f"  归一化前峰值={before:.3f} -> 后峰值={max(abs(v) for v in loud) / 32767:.3f}")

print("\n== 淡入淡出 ==")
def fade(s, fade_len, fade_out=True):
    f = to_float(s)
    n = len(f)
    out = []
    for i, v in enumerate(f):
        gain = min(1.0, i / fade_len)
        if fade_out:
            gain = min(gain, max(0.0, (n - 1 - i) / fade_len))
        out.append(v * gain)
    return to_pcm(out)

faded = fade(x, int(RATE * 0.05))
print(f"  首样本={faded[0]} 中段={faded[len(faded)//2]} 末样本={faded[-1]}")

print("\n== 单次回声：y[n] = x[n] + a·x[n-d] ==")
def echo_once(s, delay_s=0.08, a=0.5, rate=RATE):
    f = to_float(s)
    d = int(rate * delay_s)
    out = list(f)
    for i in range(d, len(f)):
        out[i] += a * f[i - d]
    return to_pcm(out)

e1 = echo_once(x)
print(f"  延迟 {0.08}s，衰减 0.5；前 {int(RATE * 0.08)} 个样本与原音相同")
print(f"  第 {int(RATE * 0.08) + 1} 个样本: 原={x[int(RATE*0.08)+1]} -> 回声={e1[int(RATE*0.08)+1]}")

print("\n== 反馈回声：y[n] = x[n] + a·y[n-d] ==")
def echo_feedback(s, delay_s=0.08, a=0.5, rate=RATE):
    f = to_float(s)
    d = int(rate * delay_s)
    out = list(f)
    for i in range(d, len(out)):
        out[i] += a * out[i - d]
    return to_pcm(out)

e2 = echo_feedback(x)
print("  多次重复衰减；注意 a 必须 < 1，否则会发散溢出")
print(f"  a=0.5 峰值={max(abs(v) for v in e2)}；a=0.9 会更响更绵长")

print("\n== 一阶低通 IIR：y[n]=(1-α)x[n]+α·y[n-1] ==")
def lowpass(s, alpha=0.9):
    out, prev = [], 0.0
    for v in to_float(s):
        prev = (1 - alpha) * v + alpha * prev
        out.append(prev)
    return to_pcm(out)

noisy = array.array("h", (clamp16(math.sin(2*math.pi*200*i/RATE) * 0.5 +
                                  (0.3 if i % 7 < 3 else -0.3)) for i in range(800)))
for alpha in (0.0, 0.7, 0.95):
    filtered = lowpass(noisy, alpha)
    energy = sum(v * v for v in filtered) / len(filtered)
    print(f"  α={alpha:<5} 平均能量={energy:>10.0f}（越大越平滑）")

print("\n== 效果链：生成 -> 淡入淡出 -> 回声 -> 归一化 ==")
chain = normalize(echo_once(fade(tone(523.25, 0.4, RATE, 0.7), 200)), target=0.85)[0]
print(f"  最终样本数={len(chain)} 峰值={max(abs(v) for v in chain)}")
if sys.byteorder == "big":
    chain.byteswap()
print(f"  可写 WAV 字节数={len(chain.tobytes())}")

# ===== 练习题 =====
# 1. 实现线性交叉淡化 crossfade(a, b, n)：a 尾部与 b 头部重叠混合。
# 2. 给低通滤波加一个「截止频率 -> α」的换算（α = exp(-2πf/RATE)）。
# 3. 把 3 路不同频率的音混合，用归一化保证不削波，观察峰值变化。
# 4. 思考：为什么效果链中间要转 float，而不能一直用 int16 累加？
