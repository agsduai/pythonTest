# ===== 第558课：类型检查与静态分析-Protocol与结构化类型 =====
# 知识点：
#   - Protocol（第351课）：按“有哪些方法/属性”判断类型，不要求继承
#   - mypy 会用 Protocol 做结构化检查：方法名、参数、返回值必须匹配
#   - runtime_checkable：允许 isinstance，但只检查方法名，不检查签名
#   - 适合第三方类、内置类型（无法继承你的基类）
#   - 与 ABC 的区别：ABC 是名义子类型（必须继承），Protocol 是结构子类型
#   - 与第394课依赖注入的配合：依赖声明为 Protocol，实现随意替换
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
from typing import Protocol

class Sender(Protocol):
    def send(self, message: str) -> str: ...

class EmailSender:
    def send(self, message: str) -> str:
        return f"邮件：{message}"

class SmsSender:
    def send(self, message: str) -> str:
        return f"短信：{message}"

def notify(sender: Sender, message: str) -> str:
    return sender.send(message)

print(notify(EmailSender(), "hello"))
print(notify(SmsSender(), "hello"))
'''

BAD = '''
from typing import Protocol

class Sender(Protocol):
    def send(self, message: str) -> str: ...

class BrokenSender:
    def send(self, message: int) -> str:      # 参数类型不匹配
        return str(message)

class MissingMethod:
    def mail(self, message: str) -> str:      # 方法名不匹配
        return message

def notify(sender: Sender, message: str) -> str:
    return sender.send(message)

notify(BrokenSender(), "hello")
notify(MissingMethod(), "hello")
'''

print("== 正确的结构化实现 ==")
print(run_mypy(GOOD))

print("\n== 不满足 Protocol ==")
print(run_mypy(BAD))

# ---- runtime_checkable ----
print("\n== runtime_checkable（运行时只查方法名）==")
RUNTIME = '''
from typing import Protocol, runtime_checkable

@runtime_checkable
class Closer(Protocol):
    def close(self) -> None: ...

class File:
    def close(self) -> None:
        print("closed")

class Wrong:
    def close(self, force: bool) -> None:   # 签名不同，但运行时只查名字
        print("wrong")

print(isinstance(File(), Closer))
print(isinstance(Wrong(), Closer))
'''
print(run_mypy(RUNTIME))
print("  注意：isinstance 为 True 不代表签名正确，mypy 才能查签名")

# ---- Protocol 继承 ----
print("\n== Protocol 组合 ==")
COMPOSE = '''
from typing import Protocol

class Reader(Protocol):
    def read(self) -> str: ...

class Writer(Protocol):
    def write(self, data: str) -> None: ...

class ReadWriter(Reader, Writer, Protocol):
    pass

class File:
    def read(self) -> str:
        return "data"
    def write(self, data: str) -> None:
        print("write", data)

def copy(src: Reader, dst: Writer) -> None:
    dst.write(src.read())

copy(File(), File())
'''
print(run_mypy(COMPOSE))

# ---- 何时用 Protocol vs ABC ----
print("\n== Protocol vs ABC ==")
rows = [
    ("ABC", "必须显式继承", "自己体系的类，强约束"),
    ("Protocol", "有方法就算", "第三方类、内置类型、跨团队接口"),
    ("runtime_checkable", "isinstance 只查名字", "动态场景，需谨慎"),
]
print(f"  {'方式':<20}{'判定':<20}{'适用'}")
for r in rows:
    print(f"  {r[0]:<20}{r[1]:<20}{r[2]}")

# ---- 注意事项 ----
print("\n== 注意事项 ==")
for item in [
    "Protocol 方法体用 ...，不要写实现",
    "属性也可以用 Protocol 声明（类变量/属性注解）",
    "回调函数可以用 Callable 而不是单方法 Protocol",
    "mypy 是结构化检查，运行时不会自动校验",
    "公开库用 Protocol 定义接口，实现者无需依赖你的包",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 定义 SupportsLen 协议（__len__），验证 list/str 都满足。
# 2. 定义 Storage 协议（get/set），写内存与文件两个实现。
# 3. 用 Protocol 给第549课的 Sender 写类型，替换具体类。
# 4. 思考：为什么 runtime_checkable 不能检查签名？
