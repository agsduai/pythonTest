# ===== 第597课：数据压缩与归档-zipfile读写 =====
# 知识点：
#   - zipfile：读写 ZIP 归档，一个包里可放多个文件与目录
#   - ZipFile(path, "w", ZIP_DEFLATED) 写；writestr / write 添加条目
#   - infolist() 看每个条目的大小、压缩后大小与 CRC；testzip() 校验完整性
#   - extract / extractall 解压；read(name) 直接读某条目的字节
#   - 中文文件名会自动带 UTF-8 标志位，跨平台可读
# 依赖：无（标准库）
import tempfile
import zipfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    zpath = root / "demo.zip"

    files = {
        "readme.txt": "项目说明\n第二行",
        "src/main.py": "print('hello')\n",
        "src/utils.py": "def add(a, b): return a + b\n",
        "空目录/": "",
    }

    # ---- 写归档 ----
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content)
        z.comment = b"demo archive"          # 注释必须是 bytes

    # ---- 读归档 ----
    with zipfile.ZipFile(zpath) as z:
        print("== 条目列表 ==")
        for info in z.infolist():
            print(f"  {info.filename:<16} {info.file_size:>4}B -> {info.compress_size:>4}B "
                  f"CRC={info.CRC:08x} 目录={info.is_dir()}")
        print("\n== 读取内容 ==")
        print(" ", repr(z.read("readme.txt").decode("utf-8")))
        print("  注释:", z.comment.decode())
        print("\n== 完整性 ==")
        print("  testzip():", z.testzip(), "（None 表示全部通过）")

        # ---- 解压到目录 ----
        dest = root / "out"
        z.extractall(dest)
        print("\n== 解压结果 ==")
        for p in sorted(dest.rglob("*")):
            print(f"  {p.relative_to(dest)}  {'目录' if p.is_dir() else str(p.stat().st_size) + 'B'}")

    # ---- 追加模式 ----
    with zipfile.ZipFile(zpath, "a", zipfile.ZIP_DEFLATED) as z:
        z.writestr("new.txt", "追加的内容")
    with zipfile.ZipFile(zpath) as z:
        print("\n== 追加后 ==")
        print("  条目数:", len(z.namelist()), z.namelist())

# ---- 压缩方式对比 ----
print("\n== 存储 vs 压缩 ==")
data = b"A" * 10000
with tempfile.TemporaryDirectory() as tmp:
    for method, label in ((zipfile.ZIP_STORED, "STORED"), (zipfile.ZIP_DEFLATED, "DEFLATED")):
        p = Path(tmp) / (label + ".zip")
        with zipfile.ZipFile(p, "w", method) as z:
            z.writestr("a.bin", data)
        print(f"  {label:<9}: {p.stat().st_size} 字节")

# ===== 练习题 =====
# 1. 把一个真实目录（含子目录）整体打包成 zip，保留相对路径。
# 2. 用 testzip() 找出归档中 CRC 校验失败的条目名。
# 3. 读取 zip 中某个文本文件并按行打印，不解压到磁盘。
# 4. 思考：ZIP_STORED 在什么场景下反而比 ZIP_DEFLATED 更合适？
