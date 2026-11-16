# ===== 第394课：设计模式进阶-依赖注入 =====
# 知识点：
#   - 依赖注入（DI）：对象不在内部 new 依赖，而是从外部“传进来”
#   - 好处：可替换（真库/假库）、可测试（第367课）、解耦（第256课）
#   - 构造器注入最常见：__init__(self, sender: Sender)
#   - 简单容器：登记“名字 → 工厂函数”，按需创建并缓存单例
#   - 大型框架（FastAPI 的 Depends、Spring）本质都是 DI 容器
from typing import Protocol


# ---- 抽象：只声明能力，不关心实现 ----
class MessageSender(Protocol):

    def send(self, message: str) -> str: ...


class ConsoleSender:

    def send(self, message: str) -> str:
        return f"[控制台] {message}"


class EmailSender:

    def send(self, message: str) -> str:
        return f"[邮件] {message}"


class FakeSender:
    """测试替身：记录所有消息，不产生副作用。"""

    def __init__(self):
        self.sent: list[str] = []

    def send(self, message: str) -> str:
        self.sent.append(message)
        return "fake-ok"


# ---- 业务类：依赖从构造器注入 ----
class NotificationService:

    def __init__(self, sender: MessageSender, prefix: str = ""):
        self.sender = sender
        self.prefix = prefix

    def notify(self, user: str, text: str) -> str:
        return self.sender.send(f"{self.prefix}{user}：{text}")


print("== 构造器注入：同一业务类，换 Sender 即可换通道 ==")
print(NotificationService(ConsoleSender()).notify("小明", "订单已发货"))
print(NotificationService(EmailSender()).notify("小红", "订单已发货"))

# ---- 测试友好：注入 FakeSender ----
print("\n== 测试替身 ==")
fake = FakeSender()
service = NotificationService(fake, prefix="[告警] ")
service.notify("运维", "CPU 95%")
service.notify("运维", "磁盘 92%")
print("替身记录到的消息：", fake.sent)
assert len(fake.sent) == 2                       # 浏览器/测试里可直接断言


# ---- 简单 DI 容器：按名字注册工厂，按需解析并缓存 ----
class Container:

    def __init__(self):
        self._factories: dict[str, callable] = {}
        self._instances: dict[str, object] = {}

    def register(self, name: str, factory: callable, singleton: bool = True):
        self._factories[name] = (factory, singleton)
        return self

    def resolve(self, name: str):
        if name in self._instances:
            return self._instances[name]
        if name not in self._factories:
            raise KeyError(f"未注册的依赖：{name}")
        factory, singleton = self._factories[name]
        instance = factory()
        if singleton:
            self._instances[name] = instance
        return instance


print("\n== DI 容器 ==")
container = Container()
container.register("sender", ConsoleSender, singleton=True)
container.register("notify_service", lambda: NotificationService(container.resolve("sender")))

svc1 = container.resolve("notify_service")
svc2 = container.resolve("notify_service")
print("单例复用：", svc1 is svc2)
print(svc1.notify("小刚", "欢迎注册"))

# 测试环境一键替换实现
container.register("sender", FakeSender, singleton=False)
test_svc = NotificationService(container.resolve("sender"))
print("替换后：", test_svc.notify("测试用户", "hi"))

# ===== 练习题 =====
# 1. 给 Container 增加 register_instance(name, obj) 直接注入现成对象。
# 2. 让 NotificationService 再依赖一个“格式化器”，构造器注入两个依赖。
# 3. 思考：DI 与“模块级全局变量”相比，测试时优势具体在哪？
