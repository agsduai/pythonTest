# ===== 第613课：音频与二进制数据-wave模块读写WAV =====
# 知识点：
#   - wave 模块读写未压缩 PCM WAV（RIFF/WAVE 容器），不需第三方库
#   - 写：setnchannels / setsampwidth / setframerate，再 writeframes(字节)
#   - 读：getparams() 返回 namedtuple；readframes(n) 返回原始字节帧
#   - 关键换算：帧 = 所有声道在同一时刻的样本集合；字节数 = 帧数 × 声道 × 采样宽度
#   - 采样宽度 2 字节 = 16 位 PCM，范围 -32768~32767；8 位是无符号 0~255
#   - 数据大小估算：时长(s) × 采样率 × 声道 × 采样宽度；CD 音质约 176KB/s
# 依赖：无（标准库）
import struct
import tempfile
import wave
from pathlib import Path

RATE = 8000
SECONDS = 0.25
N = int(RATE * SECONDS)

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "tone.wav"

    # ---- 写 WAV ----
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)          # 单声道
        w.setsampwidth(2)          # 16 位 = 2 字节
        w.setframerate(RATE)       # 每秒 8000 帧
        frames = b"".join(struct.pack("<h", 0) for _ in range(N))  # 静音
        w.writeframes(frames)

    print("== 写入完成 ==")
    print(f"  文件：{path.name}，{path.stat().st_size} 字节")
    print(f"  理论数据大小 = {N} 帧 × 1 声道 × 2 字节 = {N * 2} 字节")
    print(f"  头部开销 = {path.stat().st_size - N * 2} 字节")

    # ---- 读 WAV ----
    with wave.open(str(path), "rb") as w:
        p = w.getparams()
        print("\n== getparams() ==")
        print("  ", p)
        print(f"  声道={p.nchannels} 采样宽度={p.sampwidth} 帧率={p.framerate} "
              f"总帧数={p.nframes} 压缩={p.comptype}")
        print(f"  时长 = {p.nframes / p.framerate:.3f} 秒")
        raw = w.readframes(w.getnframes())
        print(f"  读回字节数={len(raw)}，与理论一致={len(raw) == p.nframes * p.nchannels * p.sampwidth}")

    # ---- 把原始字节解成数值样本 ----
    samples = struct.unpack(f"<{len(raw) // 2}h", raw)
    print("\n== 字节 -> 样本 ==")
    print("  样本数:", len(samples), "前 8 个:", samples[:8])

    # ---- 8 位 PCM 的差异 ----
    p8 = Path(tmp) / "eight.wav"
    with wave.open(str(p8), "wb") as w:
        w.setnchannels(1); w.setsampwidth(1); w.setframerate(RATE)
        w.writeframes(bytes([128] * N))
    with wave.open(str(p8), "rb") as w:
        print("\n== 8 位 PCM ==")
        print("  采样宽度:", w.getsampwidth(), "字节；静音中心值是 128（无符号）")
        print("  与 16 位有符号不同，8 位 WAV 用 0~255，中点 128 表示 0")

    # ---- 常见采样率与体积 ----
    print("\n== 不同配置的 1 秒数据量（16 位）==")
    for rate, ch in ((8000, 1), (16000, 1), (44100, 1), (44100, 2), (48000, 2)):
        size = rate * ch * 2
        print(f"  {rate:>5} Hz × {ch} 声道: {size / 1024:7.1f} KB/s")

# ===== 练习题 =====
# 1. 生成一个 440Hz 正弦波 WAV（16 位单声道 8000Hz，1 秒），用 wave 写盘。
# 2. 读取该 WAV，用 struct.unpack 还原样本并找出最大值与最小值。
# 3. 写一个双声道 WAV，左右声道分别放不同频率，验证帧数计算。
# 4. 思考：为什么 WAV 体积远大于 MP3？压缩音频与 PCM 的本质区别是什么？
