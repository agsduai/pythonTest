# ===== 第561课：类型检查与静态分析-ruff静态检查与格式化 =====
# 知识点：
#   - ruff：Rust 写的 Python 静态检查 + 格式化工具，速度快
#   - 常用规则：F401 未使用导入、F841 未使用变量、F821 未定义名称、
#     E501 行过长、I001 导入排序、B 系列 bugbear 规则
#   - `ruff check` 查问题，`ruff check --fix` 自动修复
#   - `ruff format` 格式化（类似 black），`--check` 只检查不修改
#   - 配置放 pyproject.toml 的 [tool.ruff]
#   - 与第218课代码规范、第472课 Git Hooks、第555课 mypy 配合
# 依赖：pip install ruff（已安装）

import subprocess
import sys
import tempfile
from pathlib import Path


def run_ruff(code: str, args: list[str]) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.py"
        path.write_text(code, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "ruff", *args, str(path)],
            capture_output=True, text=True,
        )
        output = (result.stdout + result.stderr).replace(str(path), "sample.py")
        return f"返回码 {result.returncode}\n{output.strip()}"


BAD = '''import os
import sys
from typing import List


def compute(a, b):
    unused = 42
    result = a + b
    print(result)
    return result


print(undefined_name)
this_line_is_far_too_long_and_should_trigger_the_line_length_rule_which_is_configured_at_eighty_eight_characters
'''

print("== ruff check（未使用导入/变量、未定义名称、长行）==")
print(run_ruff(BAD, ["check", "--no-cache", "--select", "F401,F841,F821,E501"]))

print("\n== 只看 F 类规则 ==")
print(run_ruff(BAD, ["check", "--no-cache", "--select", "F"]))

# ---- 自动修复 ----
print("\n== --fix 自动修复 ==")
FIXABLE = '''import os
import sys

def f():
    unused = 1
    return 2
'''
print(run_ruff(FIXABLE, ["check", "--no-cache", "--select", "F401,F841", "--fix"]))

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "fixme.py"
    path.write_text(FIXABLE, encoding="utf-8")
    subprocess.run([sys.executable, "-m", "ruff", "check", "--no-cache",
                    "--select", "F401,F841", "--fix", str(path)],
                   capture_output=True, text=True)
    print("  修复后文件：")
    print("   ", path.read_text(encoding="utf-8").replace("\n", "\\n"))

# ---- 格式化 ----
print("\n== ruff format --check ==")
UGLY = '''def add(a,b):
    return a+b


x=[1,2,3]
'''
print(run_ruff(UGLY, ["format", "--check"]))

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "ugly.py"
    path.write_text(UGLY, encoding="utf-8")
    subprocess.run([sys.executable, "-m", "ruff", "format", str(path)],
                   capture_output=True, text=True)
    print("\n  格式化后：")
    print(path.read_text(encoding="utf-8"))

# ---- pyproject 配置 ----
print("== pyproject.toml 配置示例 ==")
print("""
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
""")

# ---- 规则分组 ----
print("== 常用规则前缀 ==")
rows = [
    ("E/W", "pycodestyle 风格问题"),
    ("F", "pyflakes：未使用、未定义、重复定义"),
    ("I", "isort：导入排序"),
    ("B", "bugbear：常见 bug 模式（可变默认参数等）"),
    ("UP", "pyupgrade：旧语法升级"),
    ("SIM", "简化代码"),
    ("S", "bandit 安全问题（如 assert、随机数）"),
]
print(f"  {'前缀':<6}{'含义'}")
for r in rows:
    print(f"  {r[0]:<6}{r[1]}")

# ---- 工作流 ----
print("\n== 推荐工作流 ==")
for item in [
    "编辑器保存时自动 ruff format + check --fix",
    "pre-commit 钩子跑 ruff check（第472课）",
    "CI 跑 ruff check + ruff format --check，失败即阻断",
    "新规则先观察再启用，避免一次改几千行",
    "mypy 管类型，ruff 管风格与常见 bug，两者互补",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 写一段含 5 个 ruff 问题的代码，逐条修复。
# 2. 启用 B 规则，验证 mutable default 被检出。
# 3. 给项目配置 ruff，跑全量并统计问题数。
# 4. 思考：ruff 能替代代码评审吗？为什么？
