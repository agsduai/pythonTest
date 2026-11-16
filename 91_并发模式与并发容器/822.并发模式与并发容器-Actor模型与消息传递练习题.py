# ===== 第822课：并发模式与并发容器-Actor模型与消息传递 =====
# 知识点：
#   - Actor 模型：每个 Actor 有私有状态 + 信箱（mailbox），通过异步消息通信
#   - 核心规则：不共享内存，只传消息；每个 Actor 串行处理信箱
#   - 消除锁：状态私有 → 不需要锁；消息队列天然线程安全
#   - Actor 的三种能力：1) 处理消息 2) 创建新 Actor 3) 发消息给其他 Actor
#   - 与线程/锁的对比：Actor 消除锁竞争，但要处理消息丢失与顺序
#   - 本课用 threading + queue.Queue 实现一个最小 Actor 框架
# 依赖：无（标准库）
import threading
import queue
import random
import time


class Actor:
    """最小 Actor 基类：私有状态 + 信箱 + 消息处理循环。"""

    def __init__(self):
        self._mailbox = queue.Queue()
        self._thread = None
        self._running = False

    def send(self, message):
        """发送异步消息（非阻塞）。"""
        self._mailbox.put(message)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._mailbox.put(None)      # 毒丸先入队
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        while True:                  # 仅靠毒丸退出，不依赖 _running 标志
            try:
                msg = self._mailbox.get(timeout=1)
            except queue.Empty:
                if not self._running:
                    break
                continue
            if msg is None:
                break
            try:
                self.receive(msg)
            except Exception as e:
                pass                 # 防止单条消息异常杀死整个 Actor 线程

    def receive(self, msg):
        raise NotImplementedError("子类必须实现 receive")


class CounterActor(Actor):
    """计数 Actor：私有状态，只能通过消息修改。"""

    def __init__(self):
        super().__init__()
        self._count = 0
        self._lock = threading.Lock()   # 仅用于主线程读取结果

    def receive(self, msg):
        action, value, reply_to = msg
        if action == "increment":
            self._count += value
        elif action == "get":
            if reply_to:
                reply_to.put(self._count)   # reply 是 queue.Queue，用 put 不是 send


class BankAccountActor(Actor):
    """银行账户 Actor：状态私有，消息串行处理。"""

    def __init__(self, balance=0):
        super().__init__()
        self._balance = balance
        self._history = []
        self._reply_queue = queue.Queue()

    def receive(self, msg):
        action, amount, reply_to = msg
        if action == "deposit":
            self._balance += amount
            self._history.append(("deposit", amount))
        elif action == "withdraw":
            if self._balance >= amount:
                self._balance -= amount
                self._history.append(("withdraw", amount))
                if reply_to: reply_to.put(True)
            else:
                self._history.append(("withdraw_failed", amount))
                if reply_to: reply_to.put(False)
        elif action == "balance":
            if reply_to: reply_to.put(self._balance)


class SupervisorActor(Actor):
    """监督者 Actor：管理子 Actor 的生命周期。"""

    def __init__(self):
        super().__init__()
        self.workers = []
        self.results = []

    def spawn_worker(self, name):
        worker = WorkerActor(name, self)
        worker.start()
        self.workers.append(worker)
        return worker

    def receive(self, msg):
        action, data = msg
        if action == "result":
            self.results.append(data)
        elif action == "dispatch":
            # 分发任务给第一个空闲 worker
            worker = self.workers[0]
            worker.send(("process", data))


class WorkerActor(Actor):
    def __init__(self, name, supervisor):
        super().__init__()
        self.name = name
        self.supervisor = supervisor

    def receive(self, msg):
        action, data = msg
        if action == "process":
            result = f"{self.name}: {data.upper()}"
            self.supervisor.send(("result", result))


print("== CounterActor ==")
counter = CounterActor()
counter.start()
for _ in range(100):
    counter.send(("increment", 1, None))
reply = queue.Queue()
counter.send(("get", 0, reply))
time.sleep(0.1)
print(f"  最终计数 = {reply.get(timeout=2)}（期望 100）")
counter.stop()

print("\n== BankAccountActor ==")
account = BankAccountActor(balance=100)
account.start()
account.send(("deposit", 50, None))
reply = queue.Queue()
account.send(("withdraw", 30, None))
account.send(("withdraw", 500, None))
account.send(("balance", 0, reply))
time.sleep(0.1)
print(f"  最终余额 = {reply.get(timeout=2)}（期望 120）")
print(f"  历史 = {account._history}")
account.stop()

print("\n== Supervisor + Worker ==")
sup = SupervisorActor()
w1 = sup.spawn_worker("worker-1")
w2 = sup.spawn_worker("worker-2")
sup.start()
for task in ["hello", "world", "actor", "model"]:
    sup.send(("dispatch", task))
time.sleep(0.2)
print(f"  Worker 处理结果: {sup.results}")
for w in sup.workers: w.stop()
sup.stop()

print("\n== Actor vs 线程 + 锁 ==")
print(f"  {'维度':<16}{'线程 + 锁':<24}{'Actor 模型'}")
for row in (("状态", "共享 + 锁保护", "私有（无锁）"),
            ("通信", "共享内存", "消息传递"),
            ("并发粒度", "线程级", "Actor 级"),
            ("死锁风险", "有（锁顺序）", "无（无锁）"),
            ("调试难度", "高（竞态难复现）", "低（消息日志可追踪）")):
    print(f"  {row[0]:<16}{row[1]:<24}{row[2]}")

print("\n== Actor 模型的局限 ==")
for line in [
    "  消息传递有延迟：同步操作需要「发送 + 等待回复」的模式",
    "  消息可能丢失：需要确认/重试机制（与第53章消息队列同理）",
    "  Actor 之间的依赖关系需要手动管理（无自动事务）",
    "  与 Erlang/Akka 的差距：无监督树重启、无位置透明、无分布式",
]:
    print("  -", line)

print("\n== 实际应用 ==")
for line in [
    "  游戏服务器：每个玩家/房间是一个 Actor",
    "  IoT：每个设备是一个 Actor",
    "  交易系统：每个订单簿是一个 Actor",
    "  Python 生态：Pykka、Thespian、Ray 的 Actor 抽象",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给 Actor 加「请求-响应」模式：send_with_reply(msg) 返回 Future。
# 2. 实现「监督树」：子 Actor 崩溃时自动重启并通知父 Actor。
# 3. 用多个 CounterActor 实现「分布式计数器」（每个 Actor 负责部分 key）。
# 4. 思考：为什么 Actor 模型不需要锁？在什么场景下反而不如直接用锁？
