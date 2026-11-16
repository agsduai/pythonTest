# ===== 第611课：音频与二进制数据-bytes与memoryview基础 =====
# 知识点：
#   - bytes 不可变、bytearray 可变、memoryview 是零拷贝视图（不复制底层缓冲）
#   - 三种创建方式：字面量 b""、bytes(可迭代整数)、str.encode()
#   - hex() / fromhex() 与文本的互相转换；int.from_bytes / to_bytes 处理整数
#   - memoryview.cast("B" -> "h") 可按不同类型重新解释同一段字节
#   - 大缓冲区优先用 memoryview 切片，避免反复复制（音频/图像/网络包常见）
# 依赖：无（标准库）
import array
import sys

print("== bytes 不可变 / bytearray 可变 ==")
b = b"PCM\x00\x01"
print("  字面量:", b, "长度:", len(b))
try:
    b[0] = 0x50
except TypeError as e:
    print("  bytes 赋值报错:", type(e).__name__)
ba = bytearray(b)
ba[0] = 0x50
print("  bytearray 修改后:", bytes(ba))

print("\n== 创建方式 ==")
print("  bytes([72, 105])        :", bytes([72, 105]))
print("  bytes(4)                :", bytes(4))
print("  '你好'.encode('utf-8')  :", "你好".encode("utf-8"))
print("  range 转字节            :", bytes(range(0, 16, 3)))

print("\n== hex 文本互转 ==")
data = bytes(range(16))
print("  hex()      :", data.hex())
print("  hex(' ')   :", data.hex(" "))
print("  fromhex()  :", bytes.fromhex("48 65 6c 6c 6f"))
print("  往返一致   :", bytes.fromhex(data.hex()) == data)

print("\n== 整数与字节 ==")
value = 0x12345678
for order in ("big", "little"):
    packed = value.to_bytes(4, order)
    print(f"  {order:<7}: {packed.hex(' ')} -> {int.from_bytes(packed, order):#x}")
print("  本机字节序:", sys.byteorder)
print("  带符号: (-5).to_bytes(2,'big',signed=True) =",
      (-5).to_bytes(2, "big", signed=True).hex())

print("\n== 查找与统计 ==")
buf = b"WAVEfmt \x00WAVEdata"
print("  find(b'WAVE') :", buf.find(b"WAVE"))
print("  rfind(b'WAVE'):", buf.rfind(b"WAVE"))
print("  count(b'WAVE'):", buf.count(b"WAVE"))
print("  startswith    :", buf.startswith(b"WAVE"))
print("  b'\\x00' in buf:", b"\x00" in buf)

print("\n== memoryview 零拷贝 ==")
raw = bytearray(b"\x01\x02\x03\x04\x05\x06\x07\x08")
mv = memoryview(raw)
print("  原 buffer :", raw.hex(" "))
print("  视图切片 :", mv[2:6].hex(" "))
mv[0] = 0xFF
print("  改视图后 :", raw.hex(" "), "（原 buffer 同步变化）")
print("  只读视图 :", end=" ")
ro = memoryview(b"abcd")
try:
    ro[0] = 0x41
except TypeError as e:
    print(type(e).__name__, e)

print("\n== cast 重新解释类型 ==")
samples = array.array("h", [1000, -1000, 32767, -32768])
if sys.byteorder == "big":
    samples.byteswap()
mv2 = memoryview(samples)
print("  array('h') 字节:", bytes(mv2).hex(" "))
bytes_view = mv2.cast("B")
print("  cast('B')      :", bytes_view.tolist())
print("  cast('h') 读回 :", bytes_view.cast("h").tolist(),
      "（cast 要求至少一端是字节格式）")

print("\n== 切片是否复制（性能要点）==")
big = bytearray(1_000_000)
mv3 = memoryview(big)
print("  bytearray 切片会复制，长度:", len(big[:10]))
print("  memoryview 切片共享内存:", mv3[:10].obj is big)
mv3.release()
print("  release() 后原 buffer 仍可用:", len(big))

# ===== 练习题 =====
# 1. 用 int.from_bytes 解析 4 字节大端长度头，并打印其值。
# 2. 构造 bytearray，用 memoryview 每隔 2 字节把值加 1（原地修改）。
# 3. 把一段 16 位 PCM 样本用 cast 转成字节，再还原，验证数值一致。
# 4. 思考：处理 100MB 音频数据时，为什么切片用 memoryview 更省内存？
