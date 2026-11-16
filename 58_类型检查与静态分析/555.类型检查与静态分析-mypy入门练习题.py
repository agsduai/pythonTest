# ===== 第555课：类型检查与静态分析-mypy入门 =====
# 知识点：
#   - 类型注解（第71/72课）不只是文档：mypy 会在运行前检查类型一致性
#   - mypy 是静态类型检查器：读代码、推断类型、报告不匹配，不执行代码
#   - 常见错误：参数类型不符、返回值类型不符、可能为 None、属性不存在
#   - 渐进式：可以只给部分函数加注解，逐步收紧
#   - 配置：pyproject.toml 的 [tool.mypy]；CI 里跑 mypy 阻止类型错误合入
#   - 与第211课断言、第14/34章测试的分工：测试查行为，mypy 查类型
# 依赖：pip install mypy（已安装）

import subprocess
import sys
import tempfile
from pathlib import Path


def run_mypy(code: str, filename: str = "sample.py", extra: list[str] | None = None) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / filename
        path.write_text(code, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "--no-incremental",
             "--cache-dir", str(Path(tmp) / "cache"), *(extra or []), str(path)],
            capture_output=True, text=True,
        )
        output = (result.stdout + result.stderr).replace(str(path), filename)
        return f"返回码 {result.returncode}\n{output.strip()}"


GOOD = '''
def add(a: int, b: int) -> int:
    return a + b

x: int = add(1, 2)
name: str = "小明"
'''


BAD = '''
def add(a: int, b: int) -> int:
    return a + b

x: int = add(1, "2")          # 参数类型错误
y: str = add(1, 2)            # 返回值类型错误
z: int = "hello"              # 赋值类型错误
'''


print("== 正确代码 ==")
print(run_mypy(GOOD))

print("\n== 错误代码 ==")
print(run_mypy(BAD))

# ---- 常见错误类型 ----
print("\n== 常见 mypy 报错 ==")
CASES = {
    "可能为 None": '''
def length(s: str | None) -> int:
    return len(s)          # s 可能为 None
''',
    "属性不存在": '''
class User:
    def __init__(self, name: str) -> None:
        self.name = name

u = User("小明")
print(u.age)               # User 没有 age
''',
    "列表元素类型": '''
nums: list[int] = [1, 2, 3]
nums.append("4")           # 不能 append str
''',
}
for title, code in CASES.items():
    print(f"\n-- {title} --")
    print(run_mypy(code))

# ---- 类型注解的价值 ----
print("\n== 为什么值得加类型 ==")
for item in [
    "编辑器补全与跳转更准（IDE 靠类型推断）",
    "重构时提前发现调用点不匹配",
    "接口契约清晰，新人少踩坑",
    "mypy 在 CI 里拦住低级错误，比线上事故便宜",
    "配合 dataclass/Protocol 表达力更强（后续课）",
]:
    print("  -", item)

# ---- 渐进式落地 ----
print("\n== 渐进式落地 ==")
for item in [
    "1. 先给公共 API/核心模块加注解",
    "2. mypy 只检查已注解函数（默认行为）",
    "3. 逐步开启 --disallow-untyped-defs",
    "4. 最后开 --strict，存量用 # type: ignore 标注",
    "5. pyproject 固定配置，CI 与本地一致",
]:
    print("  -", item)

# ---- 配置示例 ----
print("\n== pyproject.toml 配置示例 ==")
print("""
[tool.mypy]
python_version = "3.11"
warn_unused_configs = true
disallow_untyped_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_return_any = true
""")

# ===== 练习题 =====
# 1. 给一个返回 str 的函数故意返回 int，看 mypy 报错。
# 2. 用 --strict 跑本课正确代码，修复所有提示。
# 3. 在项目里挑一个模块加注解，统计 mypy 报错数量变化。
# 4. 思考：类型检查能替代单元测试吗？为什么？
