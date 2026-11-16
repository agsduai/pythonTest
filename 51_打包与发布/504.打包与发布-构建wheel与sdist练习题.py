# ===== 第504课：打包与发布-构建wheel与sdist =====
# 知识点：
#   - sdist（源码包）：.tar.gz，含源码与构建配置，pip 安装时现场构建
#   - wheel（二进制分发）：.whl，已构建好，安装快、无需编译（纯 Python）
#   - python -m build 一次生成两种产物到 dist/
#   - wheel 内部结构：包代码 + *.dist-info（METADATA/WHEEL/RECORD/entry_points）
#   - RECORD 记录每个文件的哈希与大小，安装时可校验
#   - 命名规则：包名-版本-py3-none-any.whl（纯 Python、跨平台）
# 依赖：setuptools / wheel / build（已安装）

import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

PYPROJECT = """
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pack-demo"
version = "1.0.0"
description = "构建产物演示"
readme = "README.md"
requires-python = ">=3.9"
authors = [{name = "课程学员"}]
dependencies = []

[tool.setuptools.packages.find]
where = ["src"]
"""

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    pkg = root / "src" / "packdemo"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text(
        '__version__ = "1.0.0"\n'
        'def greet():\n'
        '    return "hello from packdemo"\n',
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    (root / "README.md").write_text("# pack-demo\n\n构建演示。\n", encoding="utf-8")

    # ---- 构建 ----
    result = subprocess.run(
        [sys.executable, "-m", "build", "--sdist", "--wheel", "--no-isolation"],
        cwd=root, capture_output=True, text=True,
    )
    print("== 构建 ==")
    print("  返回码：", result.returncode)
    dist = root / "dist"
    artifacts = sorted(dist.iterdir())
    for path in artifacts:
        print(f"  {path.name}（{path.stat().st_size:,} 字节）")

    # ---- 查看 wheel 内容 ----
    wheel = next(p for p in artifacts if p.suffix == ".whl")
    print("\n== wheel 内容 ==")
    with zipfile.ZipFile(wheel) as zf:
        for name in zf.namelist():
            print("  ", name)

        metadata_name = next(n for n in zf.namelist() if n.endswith("METADATA"))
        metadata = zf.read(metadata_name).decode("utf-8")
        print("\n== METADATA（前 8 行）==")
        for line in metadata.splitlines()[:8]:
            print("  ", line)

        print("\n== WHEEL ==")
        wheel_meta = next(n for n in zf.namelist() if n.endswith("/WHEEL"))
        for line in zf.read(wheel_meta).decode("utf-8").splitlines()[:4]:
            print("  ", line)

        print("\n== RECORD（前 4 行）==")
        record = next(n for n in zf.namelist() if n.endswith("/RECORD"))
        for line in zf.read(record).decode("utf-8").splitlines()[:4]:
            print("  ", line)

    # ---- 查看 sdist 内容 ----
    sdist = next(p for p in artifacts if p.name.endswith(".tar.gz"))
    print("\n== sdist 内容（前 8 项）==")
    with tarfile.open(sdist, "r:gz") as tf:
        for member in tf.getmembers()[:8]:
            print("  ", member.name)

# ---- wheel 命名规则 ----
print("\n== wheel 文件名规则 ==")
name = "pack_demo-1.0.0-py3-none-any.whl"
parts = name[:-4].split("-")
print("  ", name)
print("  {distribution}-{version}(-{build})?-{python}-{abi}-{platform}.whl")
print("  解析：", dict(zip(["包名", "版本", "Python", "ABI", "平台"], parts)))
print("  py3-none-any = 纯 Python、无 C 扩展、跨平台")

# ---- 产物用途 ----
print("\n== 产物用途 ==")
rows = [
    ("sdist (.tar.gz)", "源码 + 构建配置", "审计、从源码安装、发布必备"),
    ("wheel (.whl)", "已构建的包", "pip 优先安装，快"),
]
print(f"  {'格式':<18}{'内容':<18}{'用途'}")
for r in rows:
    print(f"  {r[0]:<18}{r[1]:<18}{r[2]}")

# ---- 构建检查 ----
print("\n== 构建检查清单 ==")
for item in [
    "dist/ 里同时有 sdist 与 wheel",
    "wheel 里包含所有子包（检查 packages.find）",
    "METADATA 的 Name/Version/Requires-Python 正确",
    "entry_points.txt 存在（如果配置了 scripts）",
    "RECORD 完整（不要手工修改 wheel）",
    "构建前清理旧 dist/ 与 build/，避免混入旧产物",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给项目增加第二个模块，确认 wheel 里包含它。
# 2. 用 zipfile 读取 RECORD，验证某个文件的哈希格式。
# 3. 故意删除 packages.find 配置，观察 wheel 是否缺少代码。
# 4. 思考：为什么 pip 优先装 wheel，而不是 sdist？
