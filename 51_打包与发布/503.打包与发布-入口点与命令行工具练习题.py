# ===== 第503课：打包与发布-入口点与命令行工具 =====
# 知识点：
#   - console_scripts：安装包后生成一个可执行命令（Windows 上是 .exe 包装器）
#   - pyproject 配置：[project.scripts] 命令名 = "模块:函数"
#   - 函数签名：main(argv=None) 最友好，便于测试（第276课）
#   - 入口点写在 wheel 的 entry_points.txt 里，pip 安装时据此生成脚本
#   - 另一种入口：python -m 包（依赖 __main__.py），无需安装命令
#   - 两种方式都保留：CLI 命令给用户，python -m 给调试
# 依赖：setuptools / wheel / build（已安装）

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PROJECT_NAME = "greet-cli-demo"
PKG = "greetpkg"

PYPROJECT = f"""
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{PROJECT_NAME}"
version = "0.1.0"
description = "命令行入口演示"
requires-python = ">=3.9"

[project.scripts]
greet = "{PKG}.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
"""

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    pkg = root / "src" / PKG
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")
    (pkg / "cli.py").write_text(
        "import argparse\n\n"
        "def main(argv=None) -> int:\n"
        "    parser = argparse.ArgumentParser(prog='greet')\n"
        "    parser.add_argument('name', nargs='?', default='世界')\n"
        "    args = parser.parse_args(argv)\n"
        "    print(f'你好，{args.name}！')\n"
        "    return 0\n",
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")

    print("== 配置的入口点 ==")
    print("  [project.scripts]")
    print(f'  greet = "{PKG}.cli:main"')

    # ---- 直接调用 main（开发时）----
    sys.path.insert(0, str(root / "src"))
    try:
        from greetpkg.cli import main
        print("\n== 直接调用 main ==")
        main(["小明"])
    finally:
        sys.path.remove(str(root / "src"))
        for name in list(sys.modules):
            if name.startswith(PKG):
                del sys.modules[name]

    # ---- 构建 wheel ----
    build = subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--no-isolation"],
        cwd=root, capture_output=True, text=True,
    )
    print("\n== 构建 wheel ==")
    print("  返回码：", build.returncode)
    wheels = list((root / "dist").glob("*.whl"))
    print("  产物：", [w.name for w in wheels])

    # ---- 查看 entry_points.txt ----
    if wheels:
        with zipfile.ZipFile(wheels[0]) as zf:
            names = zf.namelist()
            ep_name = next(n for n in names if n.endswith("entry_points.txt"))
            print("\n== wheel 内的 entry_points.txt ==")
            print("  ", zf.read(ep_name).decode("utf-8").strip().replace("\n", " | "))

    # ---- 安装到临时目录并验证 ----
    target = root / "installed"
    install = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--no-deps",
         "--target", str(target), str(wheels[0])],
        capture_output=True, text=True,
    )
    print("\n== 安装到临时目录 ==")
    print("  返回码：", install.returncode)
    print("  目录内容：", sorted(p.name for p in target.iterdir())[:6])

    # Windows 下 pip --target 不保证生成可执行脚本，直接验证模块可用
    sys.path.insert(0, str(target))
    try:
        from greetpkg.cli import main as installed_main
        print("\n== 从安装目录调用 ==")
        installed_main(["小红"])
        import greetpkg
        print("  版本：", greetpkg.__version__)
    finally:
        sys.path.remove(str(target))
        for name in list(sys.modules):
            if name.startswith(PKG):
                del sys.modules[name]

# ---- 两种入口对比 ----
print("\n== 两种入口 ==")
rows = [
    ("console_scripts", "pip 安装后生成 greet 命令", "用户日常使用"),
    ("python -m 包", "__main__.py，无需安装", "调试/服务器脚本"),
    ("直接调用 main()", "import 后调用", "单元测试（第276课）"),
]
print(f"  {'方式':<18}{'前提':<28}{'场景'}")
for r in rows:
    print(f"  {r[0]:<18}{r[1]:<28}{r[2]}")

print("\n== 入口函数写法 ==")
print("  def main(argv=None) -> int:")
print("      ...")
print("      return 0        # 返回退出码，便于 sys.exit(main())")

# ===== 练习题 =====
# 1. 给 CLI 增加 --count 参数，重复输出 N 次。
# 2. 增加第二个命令入口（如 greet-upper = "greetpkg.cli:main_upper"）。
# 3. 用 subprocess 从安装目录运行 `python -m greetpkg`（需要 __main__.py）。
# 4. 思考：为什么入口函数最好接收 argv 而不是直接读 sys.argv？
