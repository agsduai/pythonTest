# ===== 第596课：数据压缩与归档-bz2与lzma =====
# 知识点：
#   - bz2：BWT + 哈夫曼，压缩比通常优于 zlib，但更慢
#   - lzma / xz：LZMA2 算法，压缩比最高，preset 0~9 控制强度
#   - 三者都提供 compress/decompress（内存）与 open（文件）两套接口
#   - 选型：追求速度用 zlib，追求体积用 lzma，bz2 介于两者之间
#   - .tar.gz / .tar.bz2 / .tar.xz 就是 tar 归档再套不同压缩算法
# 依赖：无（标准库）
import bz2
import lzma
import tempfile
import zlib
from pathlib import Path

raw = ("可压缩文本 " * 500 + "END\n").encode("utf-8")
print(f"== 三种算法对比 ==\n  原始大小：{len(raw)} 字节")
for name, comp, decomp in (
    ("zlib(6)", lambda d: zlib.compress(d, 6), zlib.decompress),
    ("bz2", bz2.compress, bz2.decompress),
    ("lzma", lzma.compress, lzma.decompress),
):
    packed = comp(raw)
    print(f"  {name:<10}: {len(packed):>5} 字节，压缩率 {len(packed) / len(raw):.1%}")
    assert decomp(packed) == raw

# ---- lzma preset：越高越慢、越小 ----
print("\n== lzma preset ==")
for preset in (0, 3, 6, 9):
    packed = lzma.compress(raw, preset=preset)
    print(f"  preset={preset}: {len(packed)} 字节")

# ---- 文件格式读写 ----
print("\n== 文件接口 ==")
with tempfile.TemporaryDirectory() as tmp:
    for mod, ext in ((bz2, ".bz2"), (lzma, ".xz")):
        path = Path(tmp) / ("demo" + ext)
        with mod.open(str(path), "wb") as f:
            f.write(raw)
        with mod.open(str(path), "rb") as f:
            back = f.read()
        print(f"  {ext:<5}: {path.stat().st_size:>5} 字节，读回一致={back == raw}")

# ---- 自定义过滤器（进阶）----
print("\n== lzma 自定义 filter chain ==")
filters = [{"id": lzma.FILTER_LZMA2, "preset": 6}]
packed = lzma.compress(raw, format=lzma.FORMAT_RAW, filters=filters)
back = lzma.decompress(packed, format=lzma.FORMAT_RAW, filters=filters)
print(f"  FORMAT_RAW: {len(packed)} 字节，还原一致={back == raw}")

# ===== 练习题 =====
# 1. 分别压缩一段 JSON 文本和一段随机 os.urandom 字节，比较三种算法的压缩率。
# 2. 用 lzma 的 preset 0/6/9 压缩同一份大文本，记录各自耗时与体积。
# 3. 把同一批数据分别写成 .gz / .bz2 / .xz，对比最终文件大小。
# 4. 思考：为什么压缩「已经压缩过的图片/视频」几乎不会再变小？
