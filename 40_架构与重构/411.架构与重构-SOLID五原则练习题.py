# ===== 第411课：架构与重构-SOLID五原则 =====
# 知识点：
#   - S 单一职责：一个类只因为“一个原因”变化
#   - O 开闭原则：对扩展开放（加新类），对修改关闭（不改旧代码）
#   - L 里氏替换：子类必须能无缝替换父类，不破坏调用方预期
#   - I 接口隔离：接口要小而专，别逼实现方实现用不到的方法
#   - D 依赖倒置：依赖抽象（Protocol/ABC），不依赖具体实现
# 依赖：无

from abc import ABC, abstractmethod
from typing import Protocol


# ---------------- S：单一职责 ----------------
class ReportFormatter:
    def format(self, rows):
        return "\n".join(f"{k}: {v}" for k, v in rows.items())


class ReportSaver:
    def save(self, text, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path


print("== S 单一职责 ==")
text = ReportFormatter().format({"销售额": 1200, "订单数": 8})
print("格式化与保存各司其职，保存函数不关心格式")


# ---------------- O：开闭原则 ----------------
class Shape(ABC):
    @abstractmethod
    def area(self): ...


class Rectangle(Shape):
    def __init__(self, w, h):
        self.w, self.h = w, h

    def area(self):
        return self.w * self.h


class Circle(Shape):
    def __init__(self, r):
        self.r = r

    def area(self):
        return 3.14159 * self.r ** 2


def total_area(shapes):
    return sum(s.area() for s in shapes)      # 新增形状不用改这里


print("\n== O 开闭原则 ==")
print("总面积：", round(total_area([Rectangle(2, 3), Circle(1)]), 2))


# ---------------- L：里氏替换 ----------------
class Bird(ABC):
    @abstractmethod
    def move(self): ...


class Sparrow(Bird):
    def move(self):
        return "飞翔"


class Penguin(Bird):
    def move(self):
        return "游泳"


def let_it_move(bird: Bird) -> str:
    return bird.move()


print("\n== L 里氏替换 ==")
for bird in (Sparrow(), Penguin()):
    print(f"  {type(bird).__name__}：{let_it_move(bird)}")
print("  反例：给 Penguin 强行实现 fly() 抛异常，会让调用方意外 —— 应拆接口")


# ---------------- I：接口隔离 ----------------
class Printer(Protocol):
    def print_doc(self, doc): ...


class Scanner(Protocol):
    def scan(self): ...


class SimplePrinter:
    def print_doc(self, doc):
        return f"打印：{doc}"


class MultiFunction:
    def print_doc(self, doc):
        return f"多功能打印：{doc}"

    def scan(self):
        return "扫描完成"


def print_only(device: Printer, doc):
    return device.print_doc(doc)


print("\n== I 接口隔离 ==")
print(" ", print_only(SimplePrinter(), "合同"))
print(" ", print_only(MultiFunction(), "合同"))     # 不需要被迫实现 scan


# ---------------- D：依赖倒置 ----------------
class Sender(Protocol):
    def send(self, msg): ...


class EmailSender:
    def send(self, msg):
        return f"邮件：{msg}"


class SmsSender:
    def send(self, msg):
        return f"短信：{msg}"


class Notifier:
    def __init__(self, sender: Sender):          # 依赖抽象
        self.sender = sender

    def notify(self, msg):
        return self.sender.send(msg)


print("\n== D 依赖倒置 ==")
print(" ", Notifier(EmailSender()).notify("订单已发货"))
print(" ", Notifier(SmsSender()).notify("订单已发货"))

# ===== 练习题 =====
# 1. 找出第403课 ConfigCenter 里违反 SRP 的地方并拆类。
# 2. 给 Shape 增加 Triangle，验证 total_area 一行都不用改。
# 3. 思考：LSP 与“鸭子类型”冲突吗？Python 里怎么避免违反 LSP？
