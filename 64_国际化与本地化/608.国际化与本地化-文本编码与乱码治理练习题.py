# ===== 第608课：国际化与本地化-文本编码与乱码治理 =====
# 知识点：
#   - str 是 Unicode 码位序列，bytes 是字节；encode/decode 在两者之间转换
#   - BOM：utf-8-sig 会写出 EF BB BF；utf-16/utf-32 用 BOM 判字节序
#   - errors 策略：strict（默认）、ignore、replace、backslashreplace、surrogateescape
#   - surrogateescape 把非法字节映射到 U+DC80~U+DCFF，可无损往返（适合文件名/日志）
#   - 乱码（mojibake）常见成因：UTF-8 字节被按 latin-1/cp1252 解码
#   - 修复思路：str.encode(误用的编码).decode(正确编码)，可用 ftfy 思路但先手工验证
#   - 编码探测没有 100% 可靠方案；协议里应显式声明 charset
# 依赖：无（标准库）
import codecs
import tempfile
from pathlib import Path

text = "中文测试 café 😀"
utf8 = text.encode("utf-8")
print("== 编码往返 ==")
print(f"  字符数={len(text)} UTF-8 字节数={len(utf8)}")
print("  往返一致:", utf8.decode("utf-8") == text)

print("\n== 常见编码的字节形态 ==")
for enc in ("utf-8", "gbk", "utf-16", "utf-32"):
    data = text.replace("😀", "中").encode(enc)   # GBK 不支持 emoji
    print(f"  {enc:<8} {len(data):>3} 字节  前 12 = {data[:12].hex(' ')}")

print("\n== BOM ==")
for enc in ("utf-8-sig", "utf-16", "utf-32"):
    data = "ABC".encode(enc)
    print(f"  {enc:<10} {data.hex(' ')}  解码={data.decode(enc)!r}")
print("  utf-8-sig 读文件会自动去掉 BOM：")
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "bom.txt"
    p.write_bytes("你好".encode("utf-8-sig"))
    print("   ", p.read_bytes().hex(" "), "->", repr(p.read_text(encoding="utf-8-sig")))
    print("   用 utf-8 读会带 \\ufeff:", repr(p.read_text(encoding="utf-8")))

print("\n== errors 策略 ==")
broken = b"abc\xff\xfe\x80def"
for err in ("strict", "ignore", "replace", "backslashreplace", "surrogateescape"):
    if err == "strict":
        try:
            broken.decode("utf-8", err)
        except UnicodeDecodeError as e:
            print(f"  {err:<18} 抛 UnicodeDecodeError: {e.reason} @ {e.start}")
        continue
    out = broken.decode("utf-8", err)
    print(f"  {err:<18} {out!r}")

print("\n== surrogateescape 无损往返 ==")
s = broken.decode("utf-8", "surrogateescape")
print("  解码后:", repr(s))
print("  再编码:", s.encode("utf-8", "surrogateescape").hex(" "))
print("  字节无损:", s.encode("utf-8", "surrogateescape") == broken)

print("\n== 乱码修复（UTF-8 被误当 latin-1 读）==")
mojibake = utf8.decode("latin-1")
print("  误读后:", repr(mojibake[:30]))
fixed = mojibake.encode("latin-1").decode("utf-8")
print("  修复后:", repr(fixed))
print("  还原一致:", fixed == text)

print("\n== cp1252 误读的细微差别（含 € 等）==")
raw = "café €".encode("utf-8")
wrong = raw.decode("cp1252", "replace")
print("  误读:", repr(wrong))

print("\n== 增量编解码（分块也能正确）==")
enc = codecs.getincrementaldecoder("utf-8")()
parts = [utf8[:3], utf8[3:8], utf8[8:]]    # 故意从多字节字符中间切开
out = "".join(enc.decode(p) for p in parts) + enc.decode(b"", final=True)
print(f"  分块 {[len(p) for p in parts]} 字节 -> 还原一致={out == text}")

print("\n== 文件读写显式指定 encoding ==")
with tempfile.TemporaryDirectory() as tmp:
    f = Path(tmp) / "note.txt"
    # 不指定 encoding 会用系统默认，跨平台可能不一致
    f.write_text("中文", encoding="utf-8")
    print("  ", repr(f.read_text(encoding="utf-8")))
    with codecs.open(f, "r", encoding="utf-8") as fh:
        print("   codecs.open:", repr(fh.read()))

print("\n== 工程建议 ==")
for line in [
    "项目内统一 UTF-8，读写文件/网络/数据库都显式传 encoding",
    "从外部收到的字节先记录来源编码，不要靠猜",
    "处理不可信文件名/日志用 surrogateescape，避免程序崩溃",
    "检测到 mojibake 先小范围验证 encode/decode 链路，再批量修复",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 把一段 GBK 字节误按 UTF-8 解码，用 errors 策略观察差异并尝试修复。
# 2. 写一个 detect_bom(data) 返回编码名与 BOM 长度。
# 3. 用增量解码器逐字节喂入一个含中文的字节串，验证输出正确。
# 4. 思考：为什么 HTTP/HTML/JSON 都应该显式声明 charset，而不是让接收方猜？
