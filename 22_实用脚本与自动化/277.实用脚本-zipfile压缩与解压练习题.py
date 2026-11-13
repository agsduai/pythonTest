# ===== 第277课：实用脚本-zipfile压缩与解压 =====
# 知识点：
#   - zipfile：打包/解压 zip；ZIP_DEFLATED 压缩算法
#   - arcname 控制包内路径；infolist 看清单；read 直接读包内文件
#   - 安全提醒：解压不可信 zip 前检查文件名，防“路径穿越”攻击

import shutil
import zipfile
from pathlib import Path

WORK = Path("zip_demo")
(WORK / "data").mkdir(parents=True, exist_ok=True)
(WORK / "data" / "a.txt").write_text("AAA" * 100, encoding="utf-8")
(WORK / "data" / "b.txt").write_text("BBB" * 100, encoding="utf-8")

# ---- 压缩：遍历目录写入 ----
zip_path = WORK / "backup.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in (WORK / "data").rglob("*"):
        if f.is_file():
            zf.write(f, arcname=f.relative_to(WORK))     # 包内保留相对路径

print("压缩包大小：", zip_path.stat().st_size, "字节")

# ---- 查看清单 + 直接读取 ----
with zipfile.ZipFile(zip_path) as zf:
    for info in zf.infolist():
        print(" ", info.filename, info.file_size, "字节")
    print("包内读取：", zf.read("data/a.txt").decode("utf-8")[:9], "...")

# ---- 解压 ----
out = WORK / "restored"
with zipfile.ZipFile(zip_path) as zf:
    zf.extractall(out)
print("解压结果：", sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()))

# ---- 安全检查：解压不可信压缩包前先看路径 ----
with zipfile.ZipFile(zip_path) as zf:
    dangerous = [n for n in zf.namelist() if n.startswith("/") or ".." in Path(n).parts]
    print("可疑路径：", dangerous or "无")

shutil.rmtree(WORK)     # 清理

# ===== 练习题 =====
# 1. 压缩整个 pyproject01 里某一章的 .py 文件，用 infolist 汇总总大小。
# 2. 只解压包内的 a.txt（用 extract 成员）到指定目录。
# 3. 编写函数 zip_dir(src, out)：自动跳过 __pycache__。
# 4. 思考：为什么从网上下载的 zip 不能直接 extractall？
