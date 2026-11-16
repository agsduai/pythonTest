# ===== 第518课：消息队列与事件驱动-延迟队列 =====
# 知识点：
#   - 延迟队列：消息不是立刻可见，而是到指定时间才投递
#   - 场景：30 分钟未支付自动取消、定时提醒、重试退避（第443课）
#   - 实现：最小堆（due_time, seq, message），poll 时弹出到期的
#   - seq 防止同一时刻的消息比较 dict 报错（堆要求可比较）
#   - 大规模系统用“时间轮”或多级时间轮，O(1) 插入
#   - 与第331课堆、第443课退避、第484课 TTL 的联系
import heapq
import itertools
import time


class FakeClock:
    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class DelayQueue:
    def __init__(self, clock):
        self.clock = clock
        self.heap = []                 # (due, seq, msg_id, payload)
        self.seq = itertools.count()
        self.delivered = []

    def publish(self, msg_id, payload, delay):
        if delay < 0:
            raise ValueError("delay 不能为负")
        due = self.clock() + delay
        heapq.heappush(self.heap, (due, next(self.seq), msg_id, payload))
        print(f"  [入队] {msg_id}，{delay:.1f}s 后可见（due={due:.1f}）")

    def poll(self):
        """取出所有到期消息。"""
        now = self.clock()
        ready = []
        while self.heap and self.heap[0][0] <= now:
            due, _, msg_id, payload = heapq.heappop(self.heap)
            ready.append((msg_id, payload))
            self.delivered.append((now, msg_id))
        return ready

    def pending(self):
        return len(self.heap)

    def next_due(self):
        return self.heap[0][0] if self.heap else None


clock = FakeClock()
dq = DelayQueue(clock)

print("== 入队 ==")
dq.publish("M1", "立即", delay=0)
dq.publish("M2", "5 秒后", delay=5)
dq.publish("M3", "3 秒后", delay=3)
dq.publish("M4", "10 秒后", delay=10)
print("  当前待投递：", dq.pending(), "| 最近到期：", dq.next_due())

print("\n== t=0 poll ==")
print("  到期：", dq.poll())

print("\n== 时间推进 ==")
for t in (3, 5, 10):
    clock.now = t
    print(f"  t={t}s poll → {dq.poll()}")

print("\n== 投递记录 ==")
for t, msg_id in dq.delivered:
    print(f"  t={t}s 投递 {msg_id}")

# ---- 应用 1：30 分钟未支付自动取消 ----
print("\n== 应用：订单超时取消 ==")
clock2 = FakeClock()
queue2 = DelayQueue(clock2)
orders = [("O1", 30 * 60), ("O2", 30 * 60), ("O3", 5 * 60)]
for order_id, delay in orders:
    queue2.publish(order_id, f"取消 {order_id}", delay=delay)

clock2.now = 5 * 60
print("  5 分钟时：", queue2.poll())
clock2.now = 30 * 60
print("  30 分钟时：", queue2.poll())

# ---- 应用 2：重试退避 ----
print("\n== 应用：失败重试退避 ==")
clock3 = FakeClock()
retry_queue = DelayQueue(clock3)
attempts = {}
retry_queue.publish("T1", "发送短信", delay=2)
for t in (0, 1, 2, 3):
    clock3.now = t
    ready = retry_queue.poll()
    for msg_id, payload in ready:
        attempts[msg_id] = attempts.get(msg_id, 0) + 1
        if attempts[msg_id] < 3:
            backoff = 2 ** attempts[msg_id]
            print(f"  t={t}s {payload} 失败，{backoff}s 后重试")
            retry_queue.publish(msg_id, payload, delay=backoff)
        else:
            print(f"  t={t}s {payload} 成功")

# ---- 实现要点 ----
print("\n== 实现要点 ==")
for item in [
    "用最小堆按 due 排序；同 due 用自增 seq 稳定排序",
    "poll 只取 <= now 的，不要阻塞扫描整个堆",
    "消息要持久化（否则重启丢失），Kafka/RabbitMQ 有插件支持",
    "大规模用时间轮：插入 O(1)，适合百万级定时任务",
    "延迟时间用“业务时间”还是“处理时间”要明确",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 DelayQueue 增加 cancel(msg_id)。
# 2. 实现“每次失败延迟翻倍，最多 5 次”的完整重试队列。
# 3. 用 time.monotonic 替换 FakeClock，做一次真实 2 秒延迟演示。
# 4. 思考：为什么延时消息不能简单地 sleep 在消费者线程里？
