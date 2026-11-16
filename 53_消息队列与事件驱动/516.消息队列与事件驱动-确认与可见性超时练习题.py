# ===== 第516课：消息队列与事件驱动-确认与可见性超时 =====
# 知识点：
#   - ack（确认）：消费者处理完通知 broker，消息才真正删除
#   - nack（否认）：处理失败，消息重新入队（或进死信）
#   - 可见性超时（visibility timeout）：消息被取走后“隐身”一段时间，
#     超时未 ack 就重新可见，防止消费者崩溃导致消息永久卡住
#   - 超时时间要大于正常处理耗时，又不能太长（否则故障恢复慢）
#   - 重复投递是 at-least-once 的必然结果 → 消费端必须幂等（第447/515课）
#   - Kafka 用“位点提交”、RabbitMQ 用 ack、SQS 用可见性超时，思想一致
import time
from collections import deque


class FakeClock:
    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class VisibilityBroker:
    def __init__(self, clock, visibility=10.0):
        self.clock = clock
        self.visibility = visibility
        self.ready: deque[dict] = deque()
        self.inflight: dict[str, tuple[dict, float]] = {}   # msg_id -> (msg, deadline)
        self.deliveries = 0
        self.acked = 0

    def publish(self, msg_id, payload):
        self.ready.append({"id": msg_id, "payload": payload, "attempts": 0})

    def receive(self, consumer: str):
        # 先把超时未确认的消息放回队列
        self._expire_inflight()
        if not self.ready:
            return None
        msg = self.ready.popleft()
        msg["attempts"] += 1
        self.inflight[msg["id"]] = (msg, self.clock() + self.visibility)
        self.deliveries += 1
        print(f"  [{consumer}] 取到 {msg['id']}（第 {msg['attempts']} 次投递）")
        return msg

    def ack(self, msg_id):
        if msg_id in self.inflight:
            del self.inflight[msg_id]
            self.acked += 1
            print(f"  [ack] {msg_id} 确认，删除")

    def nack(self, msg_id, requeue=True):
        item = self.inflight.pop(msg_id, None)
        if item and requeue:
            msg, _ = item
            self.ready.append(msg)
            print(f"  [nack] {msg_id} 重新入队")

    def _expire_inflight(self):
        now = self.clock()
        expired = [mid for mid, (_, deadline) in self.inflight.items() if deadline <= now]
        for mid in expired:
            msg, _ = self.inflight.pop(mid)
            self.ready.append(msg)
            print(f"  [超时] {mid} 未确认，重新可见")

    def stats(self):
        return {
            "ready": len(self.ready),
            "inflight": len(self.inflight),
            "deliveries": self.deliveries,
            "acked": self.acked,
        }


clock = FakeClock()
broker = VisibilityBroker(clock, visibility=10.0)
for i in range(1, 4):
    broker.publish(f"M{i}", f"订单{i}")

print("== 正常确认 ==")
msg = broker.receive("消费者A")
broker.ack(msg["id"])

print("\n== 消费者崩溃：不 ack，超时后重投 ==")
msg = broker.receive("消费者A")
print("  消费者A 处理到一半崩溃（没有 ack）")
clock.advance(11)                       # 超过可见性超时
msg2 = broker.receive("消费者B")        # B 会重新收到同一条
print("  消费者B 收到：", msg2)
broker.ack(msg2["id"])

print("\n== nack：处理失败主动退回 ==")
msg = broker.receive("消费者A")
broker.nack(msg["id"], requeue=True)
msg = broker.receive("消费者A")
broker.ack(msg["id"])

print("\n== 统计 ==")
print("  ", broker.stats())
print("  说明：M2 被投递了两次（A 崩溃 + B 重收），ack 只算一次")

# ---- 可见性超时设置 ----
print("\n== 超时时间怎么设 ==")
for item in [
    "太短：正常处理还没完就被重投，造成重复处理",
    "太长：消费者崩溃后消息要等很久才恢复",
    "经验：P99 处理耗时的 3~5 倍；长任务用“心跳续期”",
    "SQS 支持 ChangeMessageVisibility 续期；Kafka 用消费进度提交",
]:
    print("  -", item)

# ---- 幂等兜底 ----
print("\n== 重复投递的兜底 ==")
print("  消费端用业务幂等键（订单号+事件类型）去重")
print("  处理成功与“记录已处理”要在同一事务里（第520课 Outbox 会再讲）")

# ===== 练习题 =====
# 1. 把 visibility 改成 2 秒，模拟长任务被重复投递。
# 2. 实现“最大投递次数”，超过后自动进死信（第519课）。
# 3. 给 receive 增加批量取 N 条。
# 4. 思考：为什么“先 ack 再处理”会丢消息？画出时序。
