# ===== 第601课：数据压缩与归档-校验和与完整性 =====
# 知识点：
#   - CRC32 / Adler32：快、短，用于检测传输/存储中的意外位翻转
#   - hashlib：md5/sha256/blake2b 摘要，适合做内容指纹与去重
#   - hmac：带密钥的摘要，可同时验证「完整 + 来源」，CRC 做不到
#   - ZIP 每个条目自带 CRC，testzip() / read() 会自动校验
#   - gzip 尾部存 CRC 与 ISIZE，读坏文件会抛 BadGzipFile / EOFError
#   - 关键区分：校验和 ≠ 安全哈希 ≠ 数字签名
# 依赖：无（标准库）
import hashlib
import hmac
import tempfile
import zipfile
import zlib
from pathlib import Path

raw = b"backup payload 2026\n" * 100

print("== 常用摘要长度 ==")
for name in ("md5", "sha1", "sha256", "sha512", "blake2b"):
    h = hashlib.new(name)
    h.update(raw)
    print(f"  {name:<8} {h.digest_size:>2} 字节  {h.hexdigest()[:32]}...")

print("\n== 分段 update 等价于一次性 ==")
h = hashlib.sha256()
for i in range(0, len(raw), 37):
    h.update(raw[i:i + 37])
print("  一致:", h.hexdigest() == hashlib.sha256(raw).hexdigest())

print("\n== 附带 CRC 的完整性检查 ==")
stored_crc = zlib.crc32(raw)
received = bytearray(raw)
received[10] ^= 0x01              # 模拟某一位翻转
print(f"  附带值   : {stored_crc:08x}")
print(f"  收到数据 : {zlib.crc32(bytes(received)):08x}")
print("  校验通过 :", zlib.crc32(bytes(received)) == stored_crc)

print("\n== HMAC：带密钥的完整性 ==")
key = b"shared-secret"
tag = hmac.new(key, raw, hashlib.sha256).hexdigest()
print("  标签:", tag[:32], "...")
print("  原文验签:", hmac.compare_digest(tag, hmac.new(key, raw, hashlib.sha256).hexdigest()))
tampered = bytearray(raw)
tampered[0] ^= 0x01
print("  篡改验签:", hmac.compare_digest(tag, hmac.new(key, bytes(tampered), hashlib.sha256).hexdigest()))

print("\n== ZIP 条目自带 CRC ==")
with tempfile.TemporaryDirectory() as tmp:
    zp = Path(tmp) / "archive.zip"
    payload = b"important content" * 50
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("data.bin", payload)
    with zipfile.ZipFile(zp) as z:
        info = z.infolist()[0]
        print(f"  条目 CRC : {info.CRC:08x}")
        print(f"  手工计算 : {zlib.crc32(payload):08x}")
        print(f"  testzip(): {z.testzip()}")

    # 定位并篡改压缩数据区，让 read() 报 CRC 错误
    with zipfile.ZipFile(zp) as z:
        info = z.infolist()[0]
        with zp.open("r+b") as f:
            f.seek(info.header_offset + 26)
            name_len = int.from_bytes(f.read(2), "little")
            extra_len = int.from_bytes(f.read(2), "little")
            data_start = info.header_offset + 30 + name_len + extra_len
            f.seek(data_start + 3)
            byte = f.read(1)
            f.seek(data_start + 3)
            f.write(bytes([byte[0] ^ 0xFF]))
    with zipfile.ZipFile(zp) as z:
        try:
            z.read(info.filename)
            print("  篡改后仍可读（数据区未被破坏）")
        except (zipfile.BadZipFile, EOFError, zlib.error) as e:
            print(f"  篡改后读取失败: {type(e).__name__}: {e}")

print("\n== 用摘要做内容去重 ==")
blocks = [b"alpha", b"beta", b"alpha", b"gamma", b"beta"]
seen = {}
for b in blocks:
    seen.setdefault(hashlib.sha256(b).hexdigest()[:8], b)
print("  唯一块:", list(seen.values()))
print(f"  {len(blocks)} 块 -> 存 {len(seen)} 块")

# ===== 练习题 =====
# 1. 对一份大文件分块计算 sha256，与一次性 hashlib.sha256(data) 对比。
# 2. 用 CRC32 与 SHA256 各做一次「改一个字节」检测，比较差异表现。
# 3. 用 hmac 为一段压缩数据生成标签，验证方先解压再验签。
# 4. 思考：攻击者同时改了数据和 CRC，接收方为什么察觉不到？
