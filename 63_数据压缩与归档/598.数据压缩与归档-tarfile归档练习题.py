# ===== 第598课：数据压缩与归档-tarfile归档 =====
# 知识点：
#   - tar：只「打包」不压缩；配合 gz/bz2/xz 得到 .tar.gz / .tar.bz2 / .tar.xz
#   - 模式： "w" 纯打包、"w:gz" gzip、"w:bz2" bzip2、"w:xz" lzma；"r:*" 自动识别
#   - TarInfo 描述一个成员（名字、大小、mtime、权限）；addfile 用 BytesIO 写入内存数据
#   - add(path, arcname) 直接把磁盘文件/目录加入归档
#   - getmembers / extractfile / extractall 遍历与读取
#   - ZIP 适合跨平台交换，TAR 更贴合 Linux 权限与流式管道
# 依赖：无（标准库）
import io
import tarfile
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    tgz = root / "demo.tar.gz"

    payloads = {
        "docs/说明.txt": "TAR 归档示例\n支持中文路径\n".encode("utf-8"),
        "data.csv": "id,name\n1,张三\n2,李四\n".encode("utf-8"),
        "empty/": b"",
    }

    # ---- 写归档（内存数据 -> tar 成员）----
    with tarfile.open(tgz, "w:gz") as t:
        for name, data in payloads.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mtime = 1700000000
            info.mode = 0o644
            if name.endswith("/"):
                info.type = tarfile.DIRTYPE
            t.addfile(info, io.BytesIO(data))

    print("== 归档信息 ==")
    print(f"  {tgz.name}: {tgz.stat().st_size} 字节")

    # ---- 读归档 ----
    with tarfile.open(tgz, "r:*") as t:
        for m in t.getmembers():
            print(f"  {m.name:<16} {m.size:>4}B 类型={'目录' if m.isdir() else '文件'} mode={oct(m.mode)}")
        print("\n== 读回 data.csv ==")
        with t.extractfile("data.csv") as f:
            print(f.read().decode("utf-8"), end="")

        # ---- 解压 ----
        dest = root / "out"
        t.extractall(dest, filter="data")
        print("\n== 解压结果 ==")
        for p in sorted(dest.rglob("*")):
            print("  ", p.relative_to(dest))

    # ---- 用 add() 直接打包磁盘目录 ----
    src = root / "src"
    src.mkdir()
    (src / "a.txt").write_text("hello", "utf-8")
    (src / "sub").mkdir()
    (src / "sub" / "b.txt").write_text("world", "utf-8")
    plain = root / "plain.tar"
    with tarfile.open(plain, "w") as t:
        t.add(src, arcname="project")
    with tarfile.open(plain) as t:
        print("\n== add() 打包目录 ==")
        print("  ", t.getnames())

# ===== 练习题 =====
# 1. 把同一批文件分别打成 .tar、.tar.gz、.tar.xz，对比体积。
# 2. 用 "r:*" 打开一个未知压缩格式的 tar，打印它识别到的模式。
# 3. 遍历 tar 所有成员，只解压大小小于 1KB 的文件。
# 4. 思考：为什么 tarfile.extractall 在 Python 3.12+ 建议传 filter="data"？
