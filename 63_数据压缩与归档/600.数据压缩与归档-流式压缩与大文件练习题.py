# ===== 第600课：数据压缩与归档-流式压缩与大文件 =====
# 知识点：
#   - 大文件不能一次性读进内存：分块 compress / decompress，边读边写
#   - compressobj / decompressobj 维护跨块的状态，必须最后 flush()
#   - 解压端可用任意大小的块喂入，跨块边界也能正确还原
#   - unused_data / unconsumed_tail：处理拼接流时判断是否有多余数据
#   - gzip.open 配合 for line in f 可逐行处理压缩日志，内存恒定
# 依赖：无（标准库）
import gzip
import tempfile
import zlib
from pathlib import Path


def gen_chunks(n, size=40):
    """模拟源源不断产生的数据块。"""
    for i in range(n):
        yield (f"第{i:04d}行 " + "数据" * size + "\n").encode("utf-8")


original = b"".join(gen_chunks(50))
print("== zlib 流式压缩 ==")
co = zlib.compressobj(level=6)
out = bytearray()
for chunk in gen_chunks(50):
    out += co.compress(chunk)
out += co.flush()
print(f"  输入 {len(original)} 字节 -> 输出 {len(out)} 字节（{len(out) / len(original):.1%}）")

print("\n== 小块喂入解压 ==")
dco = zlib.decompressobj()
back = bytearray()
for i in range(0, len(out), 97):        # 故意用与压缩时不同的块大小
    back += dco.decompress(out[i:i + 97])
back += dco.flush()
print(f"  还原 {len(back)} 字节，一致={bytes(back) == original}")
print(f"  unused_data 长度={len(dco.unused_data)}，eof={dco.eof}")

print("\n== 拼接流：一个压缩包后面还有别的数据 ==")
trailing = b"TRAILING-BYTES"
combined = bytes(out) + trailing
dco2 = zlib.decompressobj()
restored = dco2.decompress(combined) + dco2.flush()
print(f"  还原一致={restored == original}")
print(f"  剩余未消费数据={dco2.unused_data!r}")

print("\n== gzip 逐行处理压缩日志 ==")
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "big.log.gz"
    with gzip.open(path, "wb") as f:
        for chunk in gen_chunks(200):
            f.write(chunk)
    with gzip.open(path, "rt", encoding="utf-8") as f:
        lines = sum(1 for _ in f)
        f.seek(0)
        first = f.readline().strip()
    print(f"  {path.name}: {path.stat().st_size} 字节，{lines} 行")
    print("  首行:", first[:24], "...")

    # 追加模式再写一段
    with gzip.open(path, "ab") as f:
        f.write(b"APPENDED LINE\n")
    with gzip.open(path, "rt", encoding="utf-8") as f:
        print("  追加后总行数:", sum(1 for _ in f))

print("\n== 恒定内存复制压缩流 ==")
with tempfile.TemporaryDirectory() as tmp:
    src = Path(tmp) / "src.bin"
    dst = Path(tmp) / "dst.gz"
    src.write_bytes(b"".join(gen_chunks(100)))
    with src.open("rb") as fin, gzip.open(dst, "wb") as fout:
        while True:
            block = fin.read(4096)
            if not block:
                break
            fout.write(block)
    print(f"  {src.stat().st_size} -> {dst.stat().st_size} 字节")

# ===== 练习题 =====
# 1. 把压缩块大小从 1KB 改到 1MB，观察总耗时与压缩率是否变化。
# 2. 用 decompressobj 的 max_length 参数限制单次输出，写出限速版解压器。
# 3. 处理一个「压缩数据 + 明文尾部」的混合文件，正确分离两部分。
# 4. 思考：为什么流式压缩必须调用 flush()，漏掉会丢什么？
