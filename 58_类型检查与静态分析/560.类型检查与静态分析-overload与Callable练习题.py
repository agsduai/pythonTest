# ===== 第560课：类型检查与静态分析-overload与Callable =====
# 知识点：
#   - @overload：为同一个函数声明多个签名，按参数类型返回不同类型
#   - 实现函数必须兼容所有重载；mypy 会检查调用点匹配哪个签名
#   - Callable[[参数类型], 返回类型]：描述函数参数（高阶函数）
#   - Callable[..., T]：参数任意、返回 T
#   - 回调、策略、依赖注入都用 Callable 表达
#   - 与第259课策略、第394课依赖注入、第557课泛型的配合
# 依赖：pip install mypy（已安装）

import subprocess
import sys
import tempfile
from pathlib import Path


def run_mypy(code: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.py"
        path.write_text(code, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "--no-incremental",
             "--cache-dir", str(Path(tmp) / "cache"), str(path)],
            capture_output=True, text=True,
        )
        return (result.stdout + result.stderr).replace(str(path), "sample.py").strip()


GOOD = '''
from typing import Callable, overload

@overload
def parse(value: int) -> str: ...

@overload
def parse(value: str) -> int: ...

def parse(value: int | str) -> int | str:
    if isinstance(value, int):
        return str(value)
    return int(value)

a: str = parse(1)
b: int = parse("2")
print(a, b)

def apply(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

def add(a: int, b: int) -> int:
    return a + b

print(apply(add, 1, 2))
'''

BAD = '''
from typing import Callable, overload

@overload
def parse(value: int) -> str: ...

@overload
def parse(value: str) -> int: ...

def parse(value: int | str) -> int | str:
    if isinstance(value, int):
        return str(value)
    return int(value)

wrong: str = parse("2")            # 重载返回 int，赋给 str

def apply(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

def bad(x: str) -> str:
    return x

apply(bad, 1, 2)                   # 函数类型不匹配
'''

print("== 正确使用 overload / Callable ==")
print(run_mypy(GOOD))

print("\n== 错误使用 ==")
print(run_mypy(BAD))

# ---- 实现不兼容重载 ----
print("\n== 实现与重载不一致 ==")


IMPL_BAD = '''
from typing import overload

@overload
def area(width: int) -> int: ...

@overload
def area(width: str) -> str: ...

def area(width: int | str) -> int | str:
    return width * 2                 # str * 2 是 str，但 int 分支语义可能不同
'''
print(run_mypy(IMPL_BAD))

# ---- Callable 进阶 ----
print("\n== Callable 写法 ==")
rows = [
    ("Callable[[int, str], bool]", "两个参数，返回 bool"),
    ("Callable[..., int]", "任意参数，返回 int"),
    ("Callable[[], None]", "无参数、无返回"),
    ("Callable[[Item], float]", "策略/打分函数"),
]
print(f"  {'写法':<32}{'含义'}")
for r in rows:
    print(f"  {r[0]:<32}{r[1]}")

# ---- 回调与策略 ----
print("\n== 实际用法 ==")
CALLBACK = '''
from typing import Callable

def retry(func: Callable[[], str], times: int = 3) -> str:
    last = ""
    for _ in range(times):
        try:
            return func()
        except Exception as exc:
            last = str(exc)
    raise RuntimeError(last)

def flaky() -> str:
    return "ok"

print(retry(flaky))
'''
print(run_mypy(CALLBACK))

# ---- 注意 ----
print("\n== 注意 ==")
for item in [
    "overload 只用于类型声明，不能写实现（用 ...）",
    "实现签名要能覆盖所有重载，否则 mypy 报错",
    "调用点按参数类型选签名，返回值类型随之确定",
    "Callable 不检查参数名，只检查类型与数量",
    "复杂回调可用 Protocol 表达（第558课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 format_value 写三个重载：int→str、float→str、str→str。
# 2. 用 Callable 定义一个“重试装饰器”的类型签名。
# 3. 用 Protocol 替代 Callable[[int], str]，比较可读性。
# 4. 思考：overload 与 isinstance 分支，哪个更适合复杂逻辑？
