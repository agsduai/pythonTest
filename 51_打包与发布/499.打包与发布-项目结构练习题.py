# ===== 第499课：打包与发布-项目结构 =====
# 知识点：
#   - 可安装项目 = 源码包 + pyproject.toml + README + 测试
#   - 两种布局：flat（包在根目录）与 src（包在 src/ 下）
#   - src 布局的好处：避免“当前目录恰好有同名包”导致 import 到错误代码
#   - 包目录必须有 __init__.py；可执行入口用 __main__.py 或 console_scripts
#   - 与第218课“代码规范与项目结构”呼应，本课开始能真正“构建安装”
# 依赖：无（用 tempfile 演示）

import sys
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    # ---- 创建 src 布局的最小项目 ----
    pkg = root / "src" / "greet"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text(
        '"""greet 包：演示项目结构。"""\n'
        '__version__ = "0.1.0"\n'
        'from .core import hello\n'
        '__all__ = ["hello", "__version__"]\n',
        encoding="utf-8",
    )
    (pkg / "core.py").write_text(
        'def hello(name: str) -> str:\n'
        '    return f"你好，{name}！"\n',
        encoding="utf-8",
    )
    (pkg / "__main__.py").write_text(
        'from .core import hello\n'
        'print(hello("命令行"))\n',
        encoding="utf-8",
    )

    (root / "pyproject.toml").write_text(
        '[build-system]\n'
        'requires = ["setuptools>=68", "wheel"]\n'
        'build-backend = "setuptools.build_meta"\n\n'
        '[project]\n'
        'name = "greet-demo"\n'
        'version = "0.1.0"\n'
        'description = "演示项目"\n'
        'requires-python = ">=3.9"\n\n'
        '[tool.setuptools.packages.find]\n'
        'where = ["src"]\n',
        encoding="utf-8",
    )
    (root / "README.md").write_text("# greet-demo\n\n演示项目。\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_core.py").write_text(
        'from greet import hello\n\n'
        'def test_hello():\n'
        '    assert hello("测试") == "你好，测试！"\n',
        encoding="utf-8",
    )

    print("== 项目结构 ==")
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root)
            depth = len(rel.parts) - 1
            print("  " + "  " * depth + rel.parts[-1] + ("/" if path.is_dir() else ""))

    # ---- 直接通过 src 路径导入（未安装时也能开发）----
    sys.path.insert(0, str(root / "src"))
    try:
        import greet
        print("\n== 直接导入 ==")
        print("  版本：", greet.__version__)
        print("  调用：", greet.hello("小明"))
        print("  __all__：", greet.__all__)
    finally:
        sys.path.remove(str(root / "src"))
        sys.modules.pop("greet", None)
        sys.modules.pop("greet.core", None)

    # ---- python -m 运行包 ----
    import os
    import subprocess
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    result = subprocess.run(
        [sys.executable, "-m", "greet"],
        cwd=root, capture_output=True, text=True, env=env,
    )
    print("\n== python -m greet ==")
    print("  ", result.stdout.strip() or result.stderr.strip())

# ---- flat vs src ----
print("\n== 布局对比 ==")
for item in [
    "flat：根目录下直接放包（适合小脚本/教学）",
    "src：包放 src/ 下（推荐，避免本地同名目录干扰 import）",
    "测试放 tests/，与源码分离（第218课）",
    "README、LICENSE、pyproject.toml 放根目录",
    "构建产物 dist/、缓存 build/、*.egg-info 不提交（第297课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把示例项目改成 flat 布局，对比目录结构。
# 2. 给包增加 utils.py，并在 __init__.py 中导出。
# 3. 用 pytest 跑 tests/test_core.py（第215课）。
# 4. 思考：为什么 src 布局能减少“本地能跑、安装后报错”的问题？
