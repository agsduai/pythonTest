# ===== 第263课：设计模式-章综合案例-通知系统 =====
# 知识点：
#   - 综合运用：工厂（造渠道）+ 策略（定格式）+ 观察者（做分发）
#   - 场景：告警事件发生时，按订阅渠道发送不同格式通知
#   - 体会三个模式各管一段：创建、算法、协作

import time
from abc import ABC, abstractmethod
from datetime import datetime


# ---- 策略：消息格式化 ----
class Formatter(ABC):

    @abstractmethod
    def format(self, title, detail) -> str: ...


class PlainFormatter(Formatter):

    def format(self, title, detail):
        return f"[{title}] {detail}"


class TimestampFormatter(Formatter):

    def format(self, title, detail):
        now = datetime.now().strftime("%H:%M:%S")
        return f"{now} 【{title}】{detail}"


FORMATTERS = {"plain": PlainFormatter, "timestamp": TimestampFormatter}


# ---- 工厂：创建发送渠道 ----
class Channel(ABC):

    @abstractmethod
    def send(self, message: str): ...


class ConsoleChannel(Channel):

    def send(self, message):
        print(f"控制台 → {message}")


class FileChannel(Channel):

    def __init__(self, path):
        self.path = path

    def send(self, message):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(message + "\n")


class SmsChannel(Channel):
    """模拟短信：只打印不真发。"""

    def send(self, message):
        print(f"短信(模拟) → {message[:20]}...")


CHANNELS = {"console": ConsoleChannel, "sms": SmsChannel, "file": FileChannel}


def create_channel(kind, **kwargs) -> Channel:
    cls = CHANNELS.get(kind)
    if cls is None:
        raise ValueError(f"未知渠道：{kind}")
    return cls(**kwargs)


# ---- 观察者：事件分发 ----
class Notifier:
    """被观察者：告警事件广播给所有订阅的渠道。"""

    def __init__(self, formatter: Formatter):
        self.formatter = formatter
        self.channels = []

    def add_channel(self, kind, **kwargs):
        self.channels.append(create_channel(kind, **kwargs))

    def alert(self, title, detail):
        message = self.formatter.format(title, detail)
        for channel in self.channels:
            channel.send(message)


# ---- 组装使用 ----
notifier = Notifier(TimestampFormatter())
notifier.add_channel("console")
notifier.add_channel("sms")
notifier.add_channel("file", path="notify_log.txt")

notifier.alert("CPU告警", "使用率 95%")
time.sleep(0.1)
notifier.alert("磁盘告警", "C盘剩余 5GB")

print("--- 文件渠道的记录 ---")
with open("notify_log.txt", encoding="utf-8") as f:
    print(f.read(), end="")

import os
os.remove("notify_log.txt")

# 换格式化策略：不改任何发送代码
notifier2 = Notifier(PlainFormatter())
notifier2.add_channel("console")
notifier2.alert("上线通知", "v2.0 已发布")

# ===== 练习题 =====
# 1. 新增 WebhookChannel：把消息“POST”到记录列表（模拟）。
# 2. 给 Notifier 加渠道级异常隔离：某渠道失败不影响其他渠道。
# 3. 把“创建通知器”的过程封装成 build_notifier(config_dict) 工厂。
# 4. 思考：这个系统里如果渠道多了、事件多了，还需要引入什么？
