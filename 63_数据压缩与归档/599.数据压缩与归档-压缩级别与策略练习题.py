# ===== 第599课：数据压缩与归档-压缩级别与策略 =====
# 知识点：
#   - level 影响「找重复串」的力度：越高越慢、通常越小，但收益递减
#   - 数据本身决定上限：重复越多压缩率越高，随机数据几乎压不动
#   - compressobj(level, strategy=...) 可换压缩策略适配不同数据特征
#   - Z_DEFAULT_STRATEGY / Z_FILTERED / Z_HUFFMAN_ONLY / Z_RLE / Z_FIXED
#   - 实战建议：默认 level 6 通常性价比最高；只在明确场景才调策略
# 依赖：无（标准库）
import time
import zlib

texts = {
    "高重复": ("ABCD" * 5000).encode(),
    "自然文本": ("Python 是一种解释型、动态类型的高级程序设计语言。" * 300).encode("utf-8"),
}

print("== 压缩级别（DEFLATE） ==")
for name, raw in texts.items():
    print(f"\n样本「{name}」：原始 {len(raw)} 字节")
    for level in (1, 6, 9):
        t0 = time.perf_counter()
        packed = zlib.compress(raw, level)
        dt = time.perf_counter() - t0
        print(f"  level={level}: {len(packed):>5} 字节  压缩率 {len(packed) / len(raw):6.1%}  耗时 {dt * 1000:.2f}ms")

print("\n== 压缩策略（compressobj） ==")
strategies = (
    ("Z_DEFAULT_STRATEGY", zlib.Z_DEFAULT_STRATEGY),
    ("Z_FILTERED", zlib.Z_FILTERED),
    ("Z_HUFFMAN_ONLY", zlib.Z_HUFFMAN_ONLY),
    ("Z_RLE", zlib.Z_RLE),
    ("Z_FIXED", zlib.Z_FIXED),
)
raw = texts["自然文本"]
for name, strategy in strategies:
    co = zlib.compressobj(level=6, strategy=strategy)
    packed = co.compress(raw) + co.flush()
    print(f"  {name:<20} {len(packed):>5} 字节")

print("\n== 不同数据类型的压缩上限 ==")
import os
for label, data in (
    ("全零字节", b"\x00" * 20000),
    ("纯文本", ("Hello World " * 2000).encode()),
    ("随机字节", os.urandom(20000)),
):
    packed = zlib.compress(data, 9)
    print(f"  {label:<10} {len(data)} -> {len(packed)} 字节（{len(packed) / len(data):.1%}）")

print("\n== 字典压缩 zdict（小消息提速）==")
common = b"HTTP/1.1 200 OK Content-Type: application/json charset=utf-8"
msg = b"HTTP/1.1 200 OK Content-Type: application/json body={}"
plain = zlib.compressobj(level=9)
co = zlib.compressobj(level=9, zdict=common)
a = plain.compress(msg) + plain.flush()
b = co.compress(msg) + co.flush()
print(f"  无字典: {len(a)} 字节 | 带字典: {len(b)} 字节")

# ===== 练习题 =====
# 1. 画出 level 1~9 的「耗时-体积」曲线数据，找出你机器上的拐点。
# 2. 对比 Z_RLE 与 Z_DEFAULT_STRATEGY 在「大量小整数差分」数据上的表现。
# 3. 用 zdict 压缩一批结构相似的短日志，统计节省的字节数。
# 4. 思考：为什么对已加密/已压缩的数据再做 DEFLATE 可能反而变大？
