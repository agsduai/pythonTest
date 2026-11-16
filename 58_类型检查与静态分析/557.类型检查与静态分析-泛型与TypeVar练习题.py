# ===== 第557课：类型检查与静态分析-泛型与TypeVar =====
# 知识点：
#   - 泛型：类型作为参数，写一次适配多种类型（list[int]/list[str]）
#   - TypeVar("T")：声明类型变量；函数签名表达“输入什么类型，输出同类型”
#   - bound=：限制 T 必须是某基类/协议的子类型
#   - 约束：TypeVar("T", int, str) 只能取列出的类型
#   - 泛型类：class Box(Generic[T])，属性与方法都能用 T
#   - mypy 会检查泛型调用是否一致；Any 会绕过检查
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
from typing import Generic, TypeVar

T = TypeVar("T")

def first(items: list[T]) -> T:
    return items[0]

class Box(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value

n: int = first([1, 2, 3])
s: str = first(["a", "b"])
box = Box(42)
print(n, s, box.get() + 1)
'''

BAD = '''
from typing import TypeVar

T = TypeVar("T")

def first(items: list[T]) -> T:
    return items[0]

n: str = first([1, 2, 3])          # 推断为 int，却赋给 str
x = first([])                       # 空列表无法推断
'''

print("== 正确使用泛型 ==")
print(run_mypy(GOOD))

print("\n== 错误使用 ==")
print(run_mypy(BAD))

# ---- bound 限制 ----
print("\n== TypeVar bound ==")
BOUND = '''
from typing import TypeVar

class Animal:
    def speak(self) -> str:
        return "..."

class Dog(Animal):
    def speak(self) -> str:
        return "汪汪"

A = TypeVar("A", bound=Animal)

def speak_all(animals: list[A]) -> list[str]:
    return [a.speak() for a in animals]

print(speak_all([Dog(), Dog()]))
print(speak_all([1, 2]))            # int 不是 Animal
'''
print(run_mypy(BOUND))

# ---- 约束类型 ----
print("\n== 约束类型（只能是 int 或 str）==")
CONSTRAINED = '''
from typing import TypeVar

C = TypeVar("C", int, str)

def add_one(x: C) -> C:
    return x + 1                    # 对 str 不成立，mypy 会报错

print(add_one(1))
print(add_one("a"))
'''
print(run_mypy(CONSTRAINED))
print("  约束类型要求“所有候选都支持同样的操作”，否则实现无法同时满足")

# ---- 泛型类 ----
print("\n== 泛型类 ==")
print("  class Box(Generic[T])：value 的类型与构造时一致")
print("  Box[int] 与 Box[str] 是不同类型，不能互相赋值")

# ---- 与 PEP 695 语法 ----
print("\n== 新语法（3.12+）==")
print("  def first[T](items: list[T]) -> T: ...")
print("  class Box[T]: ...")
print("  mypy 2.x 支持；老代码仍用 TypeVar 兼容性最好")

# ---- 使用建议 ----
print("\n== 使用建议 ==")
for item in [
    "函数返回“与输入同类型”时用 TypeVar",
    "需要限制类型范围时用 bound 或约束",
    "泛型容器优先用内置 list/dict（3.9+ 支持下标）",
    "不要为了泛型而泛型：具体类型更易读时直接用",
    "Any 会让泛型推断失效，尽量避免",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 写泛型函数 last(items: list[T]) -> T。
# 2. 写泛型类 Stack[T]，支持 push/pop，pop 返回 T。
# 3. 用 bound 限制 T 必须有 name 属性（或定义 Protocol）。
# 4. 思考：泛型函数与“写多个重载”相比有什么优势？
