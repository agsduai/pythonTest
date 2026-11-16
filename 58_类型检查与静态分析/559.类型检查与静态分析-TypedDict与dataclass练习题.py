# ===== 第559课：类型检查与静态分析-TypedDict与dataclass =====
# 知识点：
#   - TypedDict：给字典的键和值类型建“契约”，mypy 能查缺键/多键/类型错
#   - NotRequired / total=False：标记可选键
#   - dataclass：类型注解 + 自动生成 __init__/__eq__/__repr__（第347课）
#   - mypy 会检查 dataclass 构造参数的类型与数量
#   - 选择：JSON/字典数据用 TypedDict；业务对象用 dataclass
#   - 与第542课描述符校验的分工：静态检查在运行前，描述符在赋值时
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
from dataclasses import dataclass
from typing import NotRequired, TypedDict

class UserDict(TypedDict):
    name: str
    age: int
    email: NotRequired[str]

@dataclass
class User:
    name: str
    age: int
    email: str = ""

u: UserDict = {"name": "小明", "age": 18}
v: UserDict = {"name": "小红", "age": 17, "email": "hong@example.com"}
print(u, v)

obj = User("小刚", 19)
print(obj.name, obj.age)
'''

BAD = '''
from dataclasses import dataclass
from typing import TypedDict

class UserDict(TypedDict):
    name: str
    age: int

@dataclass
class User:
    name: str
    age: int

missing: UserDict = {"name": "小明"}                 # 缺少 age
wrong_type: UserDict = {"name": "小明", "age": "18"} # age 类型错
extra: UserDict = {"name": "小明", "age": 18, "x": 1} # 多余键

u = User("小明", "18")                                # dataclass 参数类型错
v = User("小明")                                      # 缺少参数
'''

print("== 正确写法 ==")
print(run_mypy(GOOD))

print("\n== 错误写法 ==")
print(run_mypy(BAD))

# ---- 结构化的 JSON 数据 ----
print("\n== 嵌套 TypedDict ==")
NESTED = '''
from typing import TypedDict

class Address(TypedDict):
    city: str
    street: str

class User(TypedDict):
    name: str
    address: Address

def city_of(user: User) -> str:
    return user["address"]["city"]

print(city_of({"name": "小明", "address": {"city": "北京", "street": "长安街"}}))
print(city_of({"name": "小红", "address": {"city": "上海"}}))   # 缺少 street
'''
print(run_mypy(NESTED))

# ---- dataclass 与 frozen ----
print("\n== dataclass frozen ==")
FROZEN = '''
from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: int
    y: int

p = Point(1, 2)
p.x = 3                       # frozen 不允许修改
'''
print(run_mypy(FROZEN))

# ---- 选择建议 ----
print("\n== TypedDict vs dataclass ==")
rows = [
    ("TypedDict", "运行时就是普通 dict", "JSON/API 响应用它"),
    ("dataclass", "真正的对象，有方法与校验", "业务领域对象用它"),
    ("NamedTuple", "不可变元组 + 字段名", "轻量只读记录"),
]
print(f"  {'类型':<12}{'特点':<24}{'场景'}")
for r in rows:
    print(f"  {r[0]:<12}{r[1]:<24}{r[2]}")

# ---- 注意 ----
print("\n== 注意 ==")
for item in [
    "TypedDict 只在静态检查生效，运行时仍可塞任意键",
    "from __future__ import annotations 可延迟注解求值",
    "dataclass 默认值顺序：有默认值的字段放后面",
    "mypy 不检查运行时数据，JSON 解析后要自己校验（第542课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 用 TypedDict 描述 API 返回的 {code, message, data}。
# 2. 给 dataclass 加 __post_init__ 校验年龄范围。
# 3. 用 total=False 定义所有字段可选的配置 TypedDict。
# 4. 思考：为什么“运行时校验”和“静态类型检查”都需要？
