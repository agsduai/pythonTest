# ===== 第618课：音频与二进制数据-综合案例-DTMF拨号音合成与识别 =====
# 知识点：
#   - DTMF（双音多频）：每个按键 = 1 个低频 + 1 个高频正弦叠加
#   - 低频行 697/770/852/941 Hz，高频列 1209/1336/1477/1633 Hz
#   - Goertzel 算法：比完整 FFT 更省，只算指定频率的功率，纯 Python 也够快
#   - 综合串起本章：波形生成 -> PCM 量化 -> wave 写盘 -> 读回 -> 分帧 -> 频域识别
#   - 判定：行频功率最大 + 列频功率最大 + 总功率超阈值，才认为检测到按键
#   - 采样率 8000Hz（电信标准），100ms 音 + 50ms 静音
# 依赖：无（标准库）
import array
import math
import struct
import sys
import tempfile
import wave
from pathlib import Path

RATE = 8000
TONE_MS, GAP_MS = 100, 50
LOW = (697, 770, 852, 941)
HIGH = (1209, 1336, 1477, 1633)
KEYS = (
    ("1", "2", "3", "A"),
    ("4", "5", "6", "B"),
    ("7", "8", "9", "C"),
    ("*", "0", "#", "D"),
)


def clamp16(v: float) -> int:
    return max(-32768, min(32767, int(round(v * 32767))))


def make_digit(key: str) -> array.array:
    """生成单个按键的 16 位 PCM 样本。"""
    row = col = -1
    for r in range(4):
        for c in range(4):
            if KEYS[r][c] == key:
                row, col = r, c
    if row < 0:
        raise ValueError(f"非法按键: {key}")
    n = int(RATE * TONE_MS / 1000)
    f1, f2 = LOW[row], HIGH[col]
    return array.array("h", (
        clamp16(0.4 * (math.sin(2 * math.pi * f1 * i / RATE) +
                       math.sin(2 * math.pi * f2 * i / RATE)))
        for i in range(n)
    ))


def make_sequence(number: str) -> array.array:
    """拼接「音 + 静音」，返回整段 PCM。"""
    out = array.array("h")
    gap = array.array("h", [0] * int(RATE * GAP_MS / 1000))
    for ch in number:
        out.extend(make_digit(ch))
        out.extend(gap)
    return out


def goertzel(samples, freq: float, rate: int = RATE) -> float:
    """返回信号在 freq 处的功率（标准 Goertzel）。"""
    n = len(samples)
    k = int(0.5 + n * freq / rate)
    w = 2 * math.pi * k / n
    coeff = 2 * math.cos(w)
    s1 = s2 = 0.0
    for x in samples:
        s0 = x + coeff * s1 - s2
        s2, s1 = s1, s0
    return s1 * s1 + s2 * s2 - coeff * s1 * s2


def detect(samples) -> str | None:
    """对一个音段做 DTMF 判定。"""
    f = [v / 32767 for v in samples]
    lo = [goertzel(f, hz) for hz in LOW]
    hi = [goertzel(f, hz) for hz in HIGH]
    r, c = max(range(4), key=lambda i: lo[i]), max(range(4), key=lambda i: hi[i])
    total = sum(lo) + sum(hi)
    # 有效音：主频功率显著且占比够高
    if lo[r] + hi[c] < total * 0.5 or total < 1.0:
        return None
    return KEYS[r][c]


def write_wav(path: Path, samples: array.array):
    s = array.array("h", samples)
    if sys.byteorder == "big":
        s.byteswap()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(s.tobytes())


def read_wav(path: Path) -> array.array:
    with wave.open(str(path), "rb") as w:
        raw = w.readframes(w.getnframes())
    return array.array("h", struct.unpack(f"<{len(raw) // 2}h", raw))


number = "13800138000"
print(f"== 合成拨号序列：{number} ==")
pcm = make_sequence(number)
print(f"  总样本数={len(pcm)}  时长={len(pcm) / RATE:.2f}s  "
      f"数据大小={len(pcm) * 2 / 1024:.1f}KB")

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "dtmf.wav"
    write_wav(path, pcm)
    print(f"  写入 {path.name}: {path.stat().st_size} 字节")
    back = read_wav(path)
    print(f"  读回样本数={len(back)}，与合成一致={list(back) == list(pcm)}")

    # ---- 分帧识别 ----
    tone_len = int(RATE * TONE_MS / 1000)
    gap_len = int(RATE * GAP_MS / 1000)
    stride = tone_len + gap_len
    print("\n== Goertzel 识别 ==")
    found = []
    for i in range(len(number)):
        seg = back[i * stride: i * stride + tone_len]
        key = detect(seg)
        found.append(key)
        lo = [goertzel([v / 32767 for v in seg], hz) for hz in LOW]
        hi = [goertzel([v / 32767 for v in seg], hz) for hz in HIGH]
        print(f"  段 {i + 1:>2}: {number[i]} -> {key}  "
              f"行频={LOW[max(range(4), key=lambda j: lo[j])]}Hz "
              f"列频={HIGH[max(range(4), key=lambda j: hi[j])]}Hz")
    result = "".join(k or "?" for k in found)
    print(f"\n  识别结果: {result}")
    print(f"  与原始号码一致: {result == number}")

    # ---- 静音段不应误判 ----
    silence = back[tone_len: tone_len + gap_len]
    print(f"  静音段判定: {detect(silence)}（None 表示正确抑制）")

    # ---- 频率表 ----
    print("\n== DTMF 频率矩阵 ==")
    print("        " + "".join(f"{hz:>8}" for hz in HIGH))
    for r, hz in enumerate(LOW):
        print(f"  {hz:<5} " + "".join(f"{KEYS[r][c]:>8}" for c in range(4)))

print("\n== 工程要点 ==")
for line in [
    "Goertzel 只算 8 个频点，比 N 点 FFT 更轻，适合嵌入式/纯 Python",
    "音段与静音用固定时长分帧；真实系统需做能量门限的端点检测",
    "幅度 0.4 是两路叠加后不削波的关键",
    "WAV 是 16 位小端 PCM，大端机器要 byteswap()",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给识别加「二次谐波能量」检查，区分纯正弦干扰与真实 DTMF 音。
# 2. 在信号里叠加白噪声，测试不同信噪比下的识别准确率。
# 3. 把拨号音改成 80ms 音 + 40ms 间隔，验证分帧参数需要同步修改。
# 4. 思考：为什么 Goertzel 的 k 要取 round(n·f/rate)，而不是直接用 f/rate？
