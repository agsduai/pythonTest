# ===== 第556课：类型检查与静态分析-基础类型与Optional =====
# 知识点：
#   - 容器类型：list[int]、dict[str, float]、tuple[int, str]、set[str]
#   - Optional[X] / X | None：可能为 None，使用前必须收窄
#   - Union[X, Y] / X | Y：多种类型，用 isinstance 收窄
#   - Literal["a", "b"]：限定具体字面量
#   - 收窄（narrowing）：if x is not None / isinstance(x, int) 后 mypy 知道类型
#   - 与第71/72课注解、第555课 mypy 的关系：本课练“写对类型”
# 依赖：pip install mypy（已安装）

import subprocess
import sys
import tempfile
from pathlib import Path


def run_mypy(code: str, extra: list[str] | None = None) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.py"
        path.write_text(code, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "--no-incremental",
             "--cache-dir", str(Path(tmp) / "cache"), *(extra or []), str(path)],
            capture_output=True, text=True,
        )
        return (result.stdout + result.stderr).replace(str(path), "sample.py").strip()


GOOD = '''
from typing import Optional

def total(nums: list[int]) -> int:
    return sum(nums)

def find(name: str, table: dict[str, int]) -> int | None:
    return table.get(name)

def describe(value: int | str) -> str:
    if isinstance(value, int):
        return f"整数 {value}"
    return f"字符串 {value}"

def greet(name: Optional[str]) -> str:
    if name is None:
        return "你好，陌生人"
    return f"你好，{name}"

print(total([1, 2, 3]))
print(find("a", {"a": 1}))
print(describe(1), describe("x"))
print(greet(None), greet("小明"))
'''

BAD = '''
def total(nums: list[int]) -> int:
    return sum(nums)

total([1, "2", 3])                 # 元素类型错误
total("123")                       # 参数类型整体错误

def find(name: str, table: dict[str, int]) -> int | None:
    return table.get(name)

value = find("a", {"a": 1})
print(value + 1)                   # value 可能是 None

def describe(value: int | str) -> str:
    return value.upper()           # int 没有 upper
'''

print("== 正确写法 ==")
print(run_mypy(GOOD))

print("\n== 错误写法 ==")
print(run_mypy(BAD))

# ---- 类型收窄演示 ----
print("\n== 类型收窄 ==")
NARROW = '''
def handle(value: int | str | None) -> str:
    if value is None:
        return "空"
    if isinstance(value, int):
        return str(value * 2)      # 这里 mypy 知道是 int
    return value.upper()           # 这里知道是 str
'''
print(run_mypy(NARROW))

# ---- Literal ----
print("\n== Literal 限定取值 ==")
LITERAL = '''
from typing import Literal

def set_mode(mode: Literal["dev", "prod"]) -> str:
    return f"模式：{mode}"

set_mode("dev")
set_mode("test")                   # 不在允许的字面量里
'''
print(run_mypy(LITERAL))

# ---- 容器类型注意 ----
print("\n== 容器类型注意 ==")
for item in [
    "list[int] 是可变容器，函数里修改会影响调用方",
    "tuple[int, ...] 表示不定长同类型元组",
    "dict[str, int] 的键值类型都要写",
    "空列表要标注：items: list[int] = []，否则推断为 list[Any]",
    "Any 会“污染”后续类型检查，尽量少用",
]:
    print("  -", item)

# ---- 常见坑 ----
print("\n== 常见坑 ==")
for item in [
    "Optional 不是“可选参数”，是“可能为 None”",
    "函数默认 None 时注解要写 X | None",
    "isinstance 收窄只对局部变量有效，属性可能被其他线程改",
    "dict.get 返回 Optional，直接运算前要判空",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 parse_age(text: str) -> int | None 写实现，处理非法输入。
# 2. 用 Literal 定义订单状态，限制只能传允许值。
# 3. 把 find 改成找不到时抛异常，返回类型去掉 Optional。
# 4. 思考：为什么 mypy 不把 dict.get 的返回类型直接标成 int？
