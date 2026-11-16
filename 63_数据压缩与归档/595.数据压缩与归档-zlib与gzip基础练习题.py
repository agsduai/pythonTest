# ===== 第595课：数据压缩与归档-zlib与gzip基础 =====
# 知识点：
#   - zlib：DEFLATE 算法，compress/decompress 直接在内存里压缩字节
#   - level 0~9：0 不压缩，1 最快，9 压缩比最高（默认 -1 约等于 6）
#   - gzip：在 DEFLATE 外加文件头与 CRC 校验，常用于 .gz 文件
#   - gzip.open(path, "wb"/"rb")：像普通文件一样读写压缩文件
#   - crc32 / adler32：快速校验和，用于发现意外损坏（不是安全哈希）
# 依赖：无（标准库）
import gzip
import tempfile
import zlib
from pathlib import Path

# ---- 内存压缩 ----
text = "Python 压缩与归档 " * 200
raw = text.encode("utf-8")
print("== zlib 内存压缩 ==")
print(f"  原始大小：{len(raw)} 字节")
for level in (0, 1, 6, 9):
    packed = zlib.compress(raw, level)
    print(f"  level={level}: {len(packed)} 字节，压缩率 {len(packed) / len(raw):.1%}")
    assert zlib.decompress(packed) == raw

# ---- 校验和 ----
print("\n== 校验和 ==")
print("  crc32   :", zlib.crc32(raw))
print("  adler32 :", zlib.adler32(raw))

# ---- gzip 文件读写 ----
with tempfile.TemporaryDirectory() as tmp:
    gz_path = Path(tmp) / "demo.txt.gz"
    with gzip.open(gz_path, "wb") as f:
        f.write(raw)
    with gzip.open(gz_path, "rb") as f:
        back = f.read()
    print("\n== gzip 文件 ==")
    print(f"  文件名：{gz_path.name}")
    print(f"  压缩后：{gz_path.stat().st_size} 字节")
    print(f"  解压一致：{back == raw}")
    print(f"  内容预览：{back.decode('utf-8')[:8]} ...")

# ---- 校验和用于发现篡改/损坏 ----
print("\n== CRC 检测数据变化 ==")
a = b"important data"
b = b"important dxta"
print(f"  原始 crc32: {zlib.crc32(a):08x}")
print(f"  变化 crc32: {zlib.crc32(b):08x}")
print("  是否相同：", zlib.crc32(a) == zlib.crc32(b))

# ===== 练习题 =====
# 1. 比较不同 level 下「高度重复文本」与「随机字节」的压缩率差异。
# 2. 用 gzip 把一个字符串写成 .gz 再读回，验证内容完全一致。
# 3. 把 zlib 压缩数据中间改一个字节，观察 decompress 抛出的异常类型。
# 4. 思考：为什么 crc32 能查意外损坏，却不能防恶意篡改？
