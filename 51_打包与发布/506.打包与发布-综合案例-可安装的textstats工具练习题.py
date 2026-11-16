# ===== 第506课：打包与发布-综合案例-可安装的textstats工具 =====
# 知识点：
#   - 综合运用：项目结构（499）+ pyproject（500）+ 包组织（501）
#     + 版本（502）+ 入口点（503）+ 构建（504）+ 安装验证（505）
#   - 目标：从零做出一个可构建、可安装、可执行、可测试的 Python 包
#   - 交付物：wheel + sdist + CLI 命令 + 测试全绿
#   - 真实项目还会加：CI 流水线、类型检查、文档、许可证
# 依赖：setuptools / wheel / build / pytest（已安装）

import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PROJECT = "textstats"

PYPROJECT = f"""
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{PROJECT}"
version = "0.1.0"
description = "统计文本词频的小工具"
readme = "README.md"
requires-python = ">=3.9"
dependencies = []

[project.scripts]
textstats = "{PROJECT}.cli:main"

[project.optional-dependencies]
dev = ["pytest>=8"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
"""

INIT = '''"""textstats：文本词频统计。"""
__version__ = "0.1.0"
from .core import word_freq, top_words
__all__ = ["word_freq", "top_words", "__version__"]
'''

CORE = '''import re
from collections import Counter


def word_freq(text: str) -> Counter:
    """统计词频（英文按单词、中文按连续片段，统一小写）。"""
    tokens = re.findall(r"[A-Za-z]+|[\\u4e00-\\u9fa5]+", text.lower())
    return Counter(tokens)


def top_words(text: str, n: int = 3) -> list[tuple[str, int]]:
    if n <= 0:
        raise ValueError("n 必须为正")
    return word_freq(text).most_common(n)
'''

CLI = '''import argparse
import sys
from .core import top_words


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="textstats", description="文本词频统计")
    parser.add_argument("text", help="要统计的文本")
    parser.add_argument("-n", "--top", type=int, default=3, help="输出前 N 个词")
    args = parser.parse_args(argv)
    try:
        results = top_words(args.text, args.top)
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    for word, count in results:
        print(f"{word}\\t{count}")
    return 0
'''

MAIN = '''from .cli import main
raise SystemExit(main())
'''

README = '''# textstats

统计文本词频的小工具。

用法：textstats "hello hello world" -n 2
'''

TEST = '''import pytest
from textstats import top_words, word_freq


def test_word_freq():
    freq = word_freq("hello hello world")
    assert freq["hello"] == 2
    assert freq["world"] == 1


def test_top_words():
    assert top_words("a b b c c c", 2) == [("c", 3), ("b", 2)]


def test_invalid_n():
    with pytest.raises(ValueError):
        top_words("x", 0)
'''

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    src = root / "src" / PROJECT
    src.mkdir(parents=True)
    (src / "__init__.py").write_text(INIT, encoding="utf-8")
    (src / "core.py").write_text(CORE, encoding="utf-8")
    (src / "cli.py").write_text(CLI, encoding="utf-8")
    (src / "__main__.py").write_text(MAIN, encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_core.py").write_text(TEST, encoding="utf-8")
    (root / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    (root / "README.md").write_text(README, encoding="utf-8")

    print("== 项目结构 ==")
    for path in sorted(root.rglob("*")):
        if path.is_file():
            print("  ", path.relative_to(root))

    # ---- 1. 跑测试 ----
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    print("\n== 1. 运行测试 ==")
    test = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q"],
        cwd=root, capture_output=True, text=True, env=env,
    )
    print("  返回码：", test.returncode)
    print("  ", (test.stdout or test.stderr).strip().splitlines()[-1])

    # ---- 2. 构建 ----
    print("\n== 2. 构建产物 ==")
    build = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation"],
        cwd=root, capture_output=True, text=True,
    )
    print("  返回码：", build.returncode)
    dist = root / "dist"
    artifacts = sorted(dist.iterdir())
    for p in artifacts:
        print(f"  {p.name}（{p.stat().st_size:,} 字节）")

    wheel = next(p for p in artifacts if p.suffix == ".whl")
    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
        print("  wheel 内文件数：", len(names))
        ep = next(n for n in names if n.endswith("entry_points.txt"))
        print("  entry_points：", zf.read(ep).decode("utf-8").strip().replace("\n", " | "))

    # ---- 3. 安装到临时目录 ----
    print("\n== 3. 安装并验证 ==")
    target = root / "site"
    install = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--no-deps",
         "--target", str(target), str(wheel)],
        capture_output=True, text=True,
    )
    print("  安装返回码：", install.returncode)

    run_env = os.environ.copy()
    run_env["PYTHONPATH"] = str(target)

    # 方式 A：python -m textstats
    module_run = subprocess.run(
        [sys.executable, "-m", "textstats", "hello hello world python", "-n", "2"],
        capture_output=True, text=True, env=run_env,
    )
    print("  python -m 输出：")
    for line in module_run.stdout.strip().splitlines():
        print("    ", line)

    # 方式 B：调用 console_scripts 对应的函数
    code = (
        "from textstats.cli import main; "
        "raise SystemExit(main(['apple apple pear', '-n', '2']))"
    )
    entry_run = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=run_env,
    )
    print("  入口函数输出：")
    for line in entry_run.stdout.strip().splitlines():
        print("    ", line)

    # 方式 C：读取安装后的元数据
    meta_code = (
        "import textstats; from importlib.metadata import version; "
        "print('version', textstats.__version__); "
        "print('metadata', version('textstats'))"
    )
    meta_run = subprocess.run(
        [sys.executable, "-c", meta_code], capture_output=True, text=True, env=run_env,
    )
    print("  元数据：", meta_run.stdout.strip().replace("\n", " | "))

    # ---- 4. 错误路径 ----
    print("\n== 4. 错误路径 ==")
    bad = subprocess.run(
        [sys.executable, "-m", "textstats", "x", "-n", "0"],
        capture_output=True, text=True, env=run_env,
    )
    print("  退出码：", bad.returncode)
    print("  stderr：", bad.stderr.strip())

# ---- 交付清单 ----
print("\n== 交付清单 ==")
for item in [
    "源码：src/textstats（__init__/core/cli/__main__）",
    "配置：pyproject.toml（元数据/依赖/入口点/工具配置）",
    "测试：tests/test_core.py 全绿",
    "构建：dist/ 下有 wheel 与 sdist",
    "安装：pip install 后 python -m / console_scripts 均可用",
    "文档：README 写清安装与用法",
    "版本：0.1.0，后续按语义化版本升级",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 textstats 增加 --file 参数，从文件读取文本。
# 2. 增加 stopwords 过滤，并补测试。
# 3. 把版本改成 1.0.0，重新构建并验证 wheel 文件名。
# 4. 思考：这个项目还差哪些“生产级”要素？（CI/类型/许可/文档）
