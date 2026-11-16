# ===== 第616课：音频与二进制数据-base64与二进制编码 =====
# 知识点：
#   - 二进制不能直接塞进 JSON/URL/文本协议，要编码成安全字符
#   - base64：3 字节 -> 4 字符，体积 +33%；urlsafe 变体把 +/ 换成 -_
#   - b32 全大写+数字，b16 即 hex（最长但最易读）
#   - binascii.hexlify / unhexlify / crc32 / a2b_base64 是底层工具
#   - padding：'=' 补足 4 的倍数；解码时可补回或设 validate
#   - 编码 ≠ 加密：base64 只是表示法，任何人都能还原
# 依赖：无（标准库）
import base64
import binascii
import json
import tempfile
from pathlib import Path

data = b"\x00\x01\xfe\xffPCM\x80\x7f" + bytes(range(8))
print("== 原始字节 ==")
print("  ", data.hex(" "), f"({len(data)} 字节)")

print("\n== 四种文本编码对比 ==")
encodings = {
    "hex": binascii.hexlify(data).decode(),
    "base16": base64.b16encode(data).decode(),
    "base32": base64.b32encode(data).decode(),
    "base64": base64.b64encode(data).decode(),
    "urlsafe_b64": base64.urlsafe_b64encode(data).decode(),
}
for name, encoded in encodings.items():
    print(f"  {name:<12} 长度={len(encoded):>3}  {encoded[:56]}")

print("\n== 体积膨胀 ==")
n = len(data)
for name, encoded in encodings.items():
    print(f"  {name:<12} {n} -> {len(encoded)} 字节（×{len(encoded)/n:.2f}）")

print("\n== 解码往返 ==")
pairs = [
    (base64.b64decode, encodings["base64"]),
    (base64.urlsafe_b64decode, encodings["urlsafe_b64"]),
    (base64.b32decode, encodings["base32"]),
    (base64.b16decode, encodings["base16"]),
    (binascii.unhexlify, encodings["hex"]),
]
for fn, text in pairs:
    print(f"  {fn.__name__:<24} 一致={fn(text) == data}")

print("\n== padding 与 validate ==")
for raw in (b"a", b"ab", b"abc", b"abcd"):
    enc = base64.b64encode(raw)
    print(f"  {raw!r:<8} -> {enc!r:<14} 解码={base64.b64decode(enc)!r}")
try:
    base64.b64decode("YWJj!!!", validate=True)
except binascii.Error as e:
    print("  validate=True 拒绝非法字符:", type(e).__name__, e)

print("\n== URL 安全变体（含 + / 的典型字节）==")
tricky = b"\xfb\xff\xfe"
std = base64.b64encode(tricky).decode()
safe = base64.urlsafe_b64encode(tricky).decode()
print(f"  标准   : {std}（含 + /，放进 URL 会被转义）")
print(f"  urlsafe: {safe}")
print("  urlsafe 解码一致:", base64.urlsafe_b64decode(safe) == tricky)

print("\n== 二进制塞进 JSON ==")
payload = {"name": "clip.wav", "rate": 8000, "pcm": base64.b64encode(data).decode()}
text = json.dumps(payload, ensure_ascii=False)
back = json.loads(text)
print("  JSON:", text[:72], "...")
print("  还原一致:", base64.b64decode(back["pcm"]) == data)

print("\n== 分块编码 / 解码流式数据 ==")
chunks = [b"hello ", b"world ", b"binary\x00"]
enc = base64.b64encode(b"".join(chunks))
print("  一次性:", enc)
# 每 3 字节一块喂给增量编码器
enc64 = base64.b64encode(b"")
parts = [data[i:i + 3] for i in range(0, len(data), 3)]
rebuilt = b"".join(base64.b64decode(base64.b64encode(p)) for p in parts)
print("  逐 3 字节分块往返一致:", rebuilt == data)

print("\n== binascii.crc32 与 hexlify ==")
crc = binascii.crc32(data)
print(f"  crc32={crc:08x} hexlify={binascii.hexlify(data[:8]).decode()}")
print("  a2b_base64:", binascii.a2b_base64(encodings["base64"]) == data)

print("\n== 小文件编码写盘 ==")
with tempfile.TemporaryDirectory() as tmp:
    b64path = Path(tmp) / "clip.b64"
    b64path.write_text(encodings["base64"], "ascii")
    restored = base64.b64decode(b64path.read_text("ascii"))
    print(f"  {b64path.name} {b64path.stat().st_size} 字节 -> 还原一致={restored == data}")

print("\n== 编码不是加密 ==")
print("  base64 只是把字节改写成可打印字符，没有密钥、没有保密性")
print("  要保密用 cryptography / hashlib+hmac，要压缩用 zlib（顺序：先压缩再编码）")

# ===== 练习题 =====
# 1. 把一个 WAV 文件的字节 base64 编码后写入 JSON，再还原成文件并比对哈希。
# 2. 实现「先 zlib 压缩再 base64」，比较与直接 base64 的长度差异。
# 3. 用 urlsafe_b64encode 编码一段含 +/ 的字节，验证可直接放进 URL 查询参数。
# 4. 思考：为什么 base64 每 3 字节产生 4 个字符？padding 的作用是什么？
