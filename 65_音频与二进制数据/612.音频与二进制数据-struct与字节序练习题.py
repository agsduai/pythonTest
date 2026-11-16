# ===== 第612课：音频与二进制数据-struct与字节序 =====
# 知识点：
#   - struct.pack(fmt, ...) / unpack(fmt, bytes)：Python 值 <-> C 风格二进制
#   - 常用格式符：b B h H i I f d s（小写有符号，大写无符号，数字表字节数）
#   - 字节序前缀：< 小端、> 大端、! 网络序(=大端)、= 本机标准、@ 本机对齐
#   - 网络协议与 WAV/PNG 用小端，多数文件格式头部用大端，务必显式写前缀
#   - calcsize 看长度；pack_into / unpack_from 可写入指定偏移而不切片
#   - iter_unpack 高效遍历重复结构（如一批定长样本点）
# 依赖：无（标准库）
import struct
import sys

print("== 格式符与 calcsize ==")
for fmt in ("<b", "<B", "<h", "<H", "<i", "<I", "<f", "<d", "<10s"):
    print(f"  {fmt:<6} {struct.calcsize(fmt)} 字节")

print("\n== 小端 vs 大端（同一个数）==")
n = 0x12345678
for prefix in ("<", ">", "!", "=", "@"):
    data = struct.pack(prefix + "I", n)
    print(f"  {prefix}I : {data.hex(' ')}  -> {struct.unpack(prefix + 'I', data)[0]:#x}")
print("  本机字节序:", sys.byteorder)

print("\n== 多字段一次打包 ==")
# 自定义二进制头：magic(4s) + version(B) + flags(B) + count(H) + length(I)
header_fmt = "<4sBBHI"
header = struct.pack(header_fmt, b"WAV1", 2, 0b0000_0101, 3, 8000)
print("  头部字节:", header.hex(" "), f"共 {len(header)} 字节")
magic, version, flags, count, length = struct.unpack(header_fmt, header)
print(f"  解出: magic={magic!r} version={version} flags={flags:08b} count={count} length={length}")

print("\n== pack_into / unpack_from（按偏移读写）==")
buf = bytearray(struct.calcsize(header_fmt) + 16)
struct.pack_into("<4sBBHI", buf, 0, b"WAV1", 2, 1, 3, 8000)
struct.pack_into("<4f", buf, struct.calcsize(header_fmt), 1.0, 2.0, 3.5, -4.25)
print("  缓冲区:", buf.hex(" "))
print("  偏移读回:", struct.unpack_from("<4f", buf, struct.calcsize(header_fmt)))

print("\n== iter_unpack 遍历定长记录 ==")
# 每条记录：<H f（温度整数 + 权重浮点）
records = struct.pack("<HfHfHf", 21, 0.5, 23, 1.5, 19, 2.5)
for i, (temp, weight) in enumerate(struct.iter_unpack("<Hf", records), 1):
    print(f"  记录 {i}: temp={temp} weight={weight:.1f}")

print("\n== 对齐差异：@ 会填充，< 不会 ==")
for fmt in ("<BI", "@BI", ">BI"):
    print(f"  {fmt:<4} calcsize={struct.calcsize(fmt)}")

print("\n== 字节串与字符串 ==")
print("  pack('<5s', b'hi'):", struct.pack("<5s", b"hi"))
print("  unpack 后:", struct.unpack("<5s", struct.pack("<5s", b"hi"))[0])

print("\n== 解析 WAV 的 RIFF 头（真实格式）==")
# RIFF: 'RIFF' + size(4,小端) + 'WAVE' + 'fmt ' + subchunk1size(4) + audiofmt(2) ...
import tempfile
import wave
from pathlib import Path
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "t.wav"
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000)
        w.writeframes(b"\x00\x00" * 100)
    raw = p.read_bytes()
    riff, size, wave_tag = struct.unpack_from("<4sI4s", raw, 0)
    fmt_tag, fmt_size = struct.unpack_from("<4sI", raw, 12)
    print(f"  {riff!r} size={size} {wave_tag!r}")
    print(f"  {fmt_tag!r} fmt_size={fmt_size}")
    print(f"  文件实际大小={len(raw)}，头里记录={size + 8}")

# ===== 练习题 =====
# 1. 用 struct 解析一个 PNG 文件头（8 字节签名 + IHDR 的宽高，大端）。
# 2. 把 100 个 (id, x, y) 三元组打包成定长记录，再用 iter_unpack 读回。
# 3. 用 pack_into 在缓冲区第 8 字节处写入一个小端 double，并读回验证。
# 4. 思考：为什么网络协议基本都用「! 大端」，而 WAV 文件用「< 小端」？
