# ===== 第501课：打包与发布-包与模块组织 =====
# 知识点：
#   - 包 = 带 __init__.py 的目录；模块 = 单个 .py 文件
#   - __init__.py 决定“对外暴露什么”：导入、__all__、版本号
#   - __all__ 控制 from pkg import * 导出哪些名字
#   - __main__.py 让包可以用 python -m pkg 运行
#   - 相对导入 from .core import ... 只能在包内使用
#   - 延迟导入：__getattr__ 让重依赖按需加载（加快启动）
# 依赖：无（tempfile + subprocess）

import os
import subprocess
import sys
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    pkg = root / "mathkit"
    pkg.mkdir()

    # ---- 包内模块 ----
    (pkg / "core.py").write_text(
        'def add(a, b):\n'
        '    return a + b\n\n'
        'def multiply(a, b):\n'
        '    return a * b\n',
        encoding="utf-8",
    )
    (pkg / "text.py").write_text(
        'def shout(text):\n'
        '    return text.upper() + "!"\n',
        encoding="utf-8",
    )

    # ---- __init__：对外接口 ----
    (pkg / "__init__.py").write_text(
        '__version__ = "1.0.0"\n'
        'from .core import add, multiply\n'
        '__all__ = ["add", "multiply", "__version__"]\n',
        encoding="utf-8",
    )

    # ---- __main__：python -m mathkit ----
    (pkg / "__main__.py").write_text(
        'from .core import add\n'
        'print(f"1 + 2 = {add(1, 2)}")\n',
        encoding="utf-8",
    )

    sys.path.insert(0, str(root))
    try:
        import mathkit
        print("== 导入包 ==")
        print("  版本：", mathkit.__version__)
        print("  add(2, 3) =", mathkit.add(2, 3))
        print("  直接访问子模块：", mathkit.text.shout("hello") if hasattr(mathkit, "text") else "未导入")

        # __all__ 影响 star import
        namespace = {}
        exec("from mathkit import *", namespace)
        exported = sorted(k for k in namespace if not k.startswith("__"))
        print("  from mathkit import * 拿到：", exported)
        print("  text 是否被导出：", "text" in exported)

        # 显式导入子模块仍然可以
        from mathkit.text import shout
        print("  显式导入 text.shout：", shout("hi"))
    finally:
        sys.path.remove(str(root))
        for name in list(sys.modules):
            if name == "mathkit" or name.startswith("mathkit."):
                del sys.modules[name]

    # ---- python -m 运行 ----
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    result = subprocess.run(
        [sys.executable, "-m", "mathkit"], cwd=root,
        capture_output=True, text=True, env=env,
    )
    print("\n== python -m mathkit ==")
    print("  ", result.stdout.strip() or result.stderr.strip())

# ---- 延迟导入示例 ----
print("\n== 延迟导入（重依赖按需加载）==")


class LazyDemo:
    """模块级 __getattr__ 的简化演示：第一次访问才导入。"""

    def __getattr__(self, name):
        if name == "json":
            print("  [延迟导入] 现在才 import json")
            import json
            return json
        raise AttributeError(name)


demo = LazyDemo()
print("  对象已创建，还没导入 json")
print("  使用：", demo.json.dumps({"ok": True}))

# ---- 组织建议 ----
print("\n== 组织建议 ==")
for item in [
    "__init__.py 只放“对外接口”，别塞业务逻辑",
    "__all__ 明确公共 API，内部函数用 _ 前缀",
    "子模块职责单一（core/text/io/cli）",
    "重依赖（numpy/pandas）延迟到函数内导入，加快 CLI 启动",
    "循环导入：把共享类型放到 types.py，或用 TYPE_CHECKING",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 mathkit 增加 io.py（读写 JSON），并决定是否在 __init__ 中导出。
# 2. 模拟循环导入（a 导入 b、b 导入 a），用延迟导入解决。
# 3. 用 __getattr__ 实现“访问 mathkit.pandas 时才导入 pandas”。
# 4. 思考：__all__ 与“下划线命名”各解决什么问题？
