# ===== 第522课：消息队列与事件驱动-综合案例-迷你消息代理 =====
# 知识点：
#   - 综合运用：分区（517）+ 可见性超时（516）+ 重试/死信（519）+ 指标
#   - 迷你 Broker：publish / poll / ack / nack / tick / stats
#   - 消费组：每个分区只分配给一个消费者；同一 key 同分区
#   - 失败重试到上限 → DLQ；重放后恢复
#   - 指标：投递次数、确认数、重投数、DLQ 数、积压量
#   - 这是 Kafka/RabbitMQ 核心语义的最小模型
import hashlib
import heapq
import itertools
import time
from collections import deque


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, s):
        self.now += s


class Message:
    _seq = itertools.count(1)

    def __init__(self, key, payload, delay=0.0):
        self.id = f"msg-{next(self._seq):03d}"
        self.key = key
        self.payload = payload
        self.attempts = 0
        self.created_at = 0.0
        self.delay = delay


class MiniBroker:
    def __init__(self, partitions=3, visibility=5.0, max_attempts=3, clock=None):
        self.partitions = partitions
        self.visibility = visibility
        self.max_attempts = max_attempts
        self.clock = clock or FakeClock()
        self.queues = [deque() for _ in range(partitions)]
        self.delayed: list = []                # (due, seq, msg)
        self.delay_seq = itertools.count()
        self.inflight: dict[str, tuple[Message, float, int, str]] = {}
        self.dlq: list[Message] = []
        self.metrics = {"published": 0, "delivered": 0, "acked": 0,
                        "redelivered": 0, "dlq": 0}

    def _partition(self, key):
        digest = hashlib.sha256(key.encode()).hexdigest()
        return int(digest[:8], 16) % self.partitions

    def publish(self, key, payload, delay=0.0):
        msg = Message(key, payload, delay)
        msg.created_at = self.clock()
        if delay > 0:
            heapq.heappush(self.delayed, (self.clock() + delay, next(self.delay_seq), msg))
        else:
            self.queues[self._partition(key)].append(msg)
        self.metrics["published"] += 1
        return msg

    def tick(self):
        """把到期的延迟消息放入分区；把超时未确认的消息重新入队。"""
        now = self.clock()
        while self.delayed and self.delayed[0][0] <= now:
            _, _, msg = heapq.heappop(self.delayed)
            self.queues[self._partition(msg.key)].append(msg)

        expired = [mid for mid, (_, deadline, _, _) in self.inflight.items()
                   if deadline <= now]
        for mid in expired:
            msg, _, attempts, consumer = self.inflight.pop(mid)
            if attempts >= self.max_attempts:
                self._to_dlq(msg, "可见性超时且达到最大重试")
            else:
                self.queues[self._partition(msg.key)].append(msg)
                self.metrics["redelivered"] += 1
                print(f"  [重投] {mid}（消费者 {consumer} 未确认）")

    def poll(self, consumer, partition):
        self.tick()
        if not self.queues[partition]:
            return None
        msg = self.queues[partition].popleft()
        msg.attempts += 1
        self.inflight[msg.id] = (msg, self.clock() + self.visibility,
                                 msg.attempts, consumer)
        self.metrics["delivered"] += 1
        print(f"  [{consumer}] 分区{partition} 取到 {msg.id} {msg.payload} "
              f"（第 {msg.attempts} 次）")
        return msg

    def ack(self, msg_id):
        if msg_id in self.inflight:
            del self.inflight[msg_id]
            self.metrics["acked"] += 1
            print(f"  [ack] {msg_id}")

    def nack(self, msg_id):
        item = self.inflight.pop(msg_id, None)
        if not item:
            return
        msg, _, attempts, _ = item
        if attempts >= self.max_attempts:
            self._to_dlq(msg, "处理失败且达到最大重试")
        else:
            self.queues[self._partition(msg.key)].append(msg)
            self.metrics["redelivered"] += 1
            print(f"  [nack] {msg_id} 重新入队")

    def _to_dlq(self, msg, reason):
        self.dlq.append(msg)
        self.metrics["dlq"] += 1
        print(f"  [DLQ] {msg.id} {msg.payload}：{reason}")

    def backlog(self):
        return sum(len(q) for q in self.queues) + len(self.inflight) + len(self.delayed)

    def stats(self):
        return {**self.metrics, "backlog": self.backlog(), "dlq_size": len(self.dlq)}


class Consumer:
    def __init__(self, name, broker, fail_payloads=()):
        self.name = name
        self.broker = broker
        self.fail_payloads = set(fail_payloads)

    def work(self, partition, max_messages=5):
        for _ in range(max_messages):
            msg = self.broker.poll(self.name, partition)
            if msg is None:
                return
            if msg.payload in self.fail_payloads:
                print(f"    {self.name} 处理失败：{msg.payload}")
                self.broker.nack(msg.id)
            else:
                self.broker.ack(msg.id)


clock = FakeClock()
broker = MiniBroker(partitions=3, visibility=5, max_attempts=2, clock=clock)

print("== 发布 8 条消息（其中 1 条延迟 3 秒，1 条会失败）==")
for i in range(1, 8):
    broker.publish(f"user-{i % 4}", f"order-{i}")
delayed = broker.publish("user-9", "reminder", delay=3)
print("  立即积压：", broker.backlog())

print("\n== 消费者 A/B 各处理两个分区 ==")
a = Consumer("A", broker)
b = Consumer("B", broker, fail_payloads={"order-3"})
for p in (0, 1):
    a.work(p)
for p in (2,):
    b.work(p)

print("\n== 时间推进 3 秒：延迟消息可见 ==")
clock.advance(3)
for p in range(3):
    a.work(p)
    b.work(p)

print("\n== 时间推进 5 秒：未确认消息重投 ==")
# 直接取一条但不确认，模拟消费者挂掉
msg = broker.poll("A", 0)
if msg:
    clock.advance(6)
    broker.tick()
    for p in range(3):
        a.work(p)
        b.work(p)

print("\n== 指标 ==")
for key, value in broker.stats().items():
    print(f"  {key}: {value}")

print("\n== 死信 ==")
for msg in broker.dlq:
    print(f"  {msg.id} {msg.payload}（尝试 {msg.attempts} 次）")

print("\n== 重放死信（修复失败逻辑）==")
b.fail_payloads.clear()
for msg in broker.dlq:
    # 重新入队并处理
    broker.queues[broker._partition(msg.key)].append(msg)
broker.dlq.clear()
for p in range(3):
    a.work(p)
    b.work(p)
print("  重放后指标：", broker.stats())

# ---- 对照真实系统 ----
print("\n== 对照真实系统 ==")
rows = [
    ("本课 MiniBroker", "分区/ack/可见性/DLQ/延迟", "Kafka + RabbitMQ 语义简化"),
    ("Kafka", "高吞吐、分区、消费组、位点", "日志型，适合流处理"),
    ("RabbitMQ", "灵活路由、ack、延迟插件", "消息型，适合任务"),
    ("SQS", "托管、可见性超时、DLQ", "免运维，语义简单"),
]
print(f"  {'系统':<18}{'核心能力':<30}{'定位'}")
for r in rows:
    print(f"  {r[0]:<18}{r[1]:<30}{r[2]}")

# ===== 练习题 =====
# 1. 给 MiniBroker 增加“消费组自动分配分区”。
# 2. 实现批量 ack（一次确认多条）。
# 3. 增加“消息 TTL”，过期未消费直接进 DLQ。
# 4. 思考：为什么“ack 后处理”会丢失消息，而“处理后 ack”会重复？
