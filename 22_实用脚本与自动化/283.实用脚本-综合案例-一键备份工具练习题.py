# ===== 第283课：实用脚本-综合案例-一键备份工具 =====
# 知识点：
#   - 综合运用：argparse（276）+ zipfile（277）+ hashlib（265）+ logging（282）
#   - 完整 CLI：python 本文件.py 源目录 -o 备份.zip --verify
#   - 结构规范：build_parser + main(argv) + if __name__ == "__main__"
#   - 无参数运行时执行内置演示，方便直接观察效果

import argparse
import hashlib
import logging
import shutil
import sys
import zipfile
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s", force=True)
log = logging.getLogger("backup_tool")


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def make_backup(src: Path, out: Path):
    """打包目录 + 生成 sha256 清单。"""
    files = [f for f in src.rglob("*") if f.is_file()]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, arcname=f.relative_to(src))
    manifest_path = out.with_suffix(out.suffix + ".sha256")
    manifest_path.write_text(
        "\n".join(f"{file_sha256(f)}  {f.relative_to(src)}" for f in files),
        encoding="utf-8",
    )
    log.info("已备份 %d 个文件 → %s", len(files), out)
    log.info("清单 → %s", manifest_path)
    return manifest_path


def verify_backup(src: Path, manifest_path: Path):
    """逐行校验清单里的哈希。"""
    ok = True
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        if file_sha256(src / name) != digest:
            log.error("校验失败：%s", name)
            ok = False
    log.info("校验结果：%s", "全部通过" if ok else "存在失败")
    return ok


def main(argv=None):
    parser = argparse.ArgumentParser(description="一键备份工具")
    parser.add_argument("src", help="要备份的目录")
    parser.add_argument("-o", "--out", default="backup.zip", help="输出 zip 路径")
    parser.add_argument("--verify", action="store_true", help="备份后校验")
    args = parser.parse_args(argv)

    src = Path(args.src)
    if not src.is_dir():
        log.error("源目录不存在：%s", src)
        return 2
    out = Path(args.out)
    manifest_path = make_backup(src, out)
    if args.verify and not verify_backup(src, manifest_path):
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 无参数：执行内置演示（真实使用见下方注释）
        demo = Path("demo_src")
        demo.mkdir(exist_ok=True)
        (demo / "f1.txt").write_text("hello", encoding="utf-8")
        (demo / "f2.csv").write_text("a,b\n1,2", encoding="utf-8")
        code = main([str(demo), "-o", "demo_backup.zip", "--verify"])
        shutil.rmtree(demo)
        Path("demo_backup.zip").unlink()
        Path("demo_backup.zip.sha256").unlink()
    else:
        # 真实使用：python 本文件.py 目录 -o 备份.zip --verify
        code = main()
    sys.exit(code)

# ===== 练习题 =====
# 1. 增加 --exclude 参数：跳过指定后缀（如 .tmp）的文件。
# 2. 增加 --since 参数：只备份 24 小时内修改过的文件（st_mtime）。
# 3. 思考：如果要备份到远端，zip + 清单这套流程哪些步骤可以复用？
