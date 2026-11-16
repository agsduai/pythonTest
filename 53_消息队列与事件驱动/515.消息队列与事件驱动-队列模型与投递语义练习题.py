# ===== 第515课：消息队列与事件驱动-队列模型 =====
# 知识点：
#   - 消息队列：生产者发消息、消费者取消息，双方解耦、可异步削峰
#   - 投递语义：
#     - at-most-once：先删后处理，失败就丢（最多一次）
#     - at-least-once：先处理后删，失败会重投（至少一次，可能重复）
#     - exactly-once：靠幂等消费实现“效果上只一次”（第447课）
#   - 队列（点对点）vs 主题（发布订阅）：一条消息给一个还是给所有订阅者
#   - 现实系统：Kafka/RabbitMQ/Redis Streams，本课用内存队列讲清语义
#   - 与第199课进程 Queue、第355课 asyncio.Queue 的区别：这里强调投递保证
from collections import deque


class InMemoryQueue:
    def __init__(self):
        self.items = deque()
        self.published = 0
        self.acked = 0

    def publish(self, message):
        self.items.append(message)
        self.published += 1

    def size(self):
        return len(self.items)


# ---------------- 1. at-most-once ----------------
def process_at_most_once(queue):
    """先出队再处理：处理失败，消息就丢了。"""
    while queue.items:
        msg = queue.items.popleft()
        try:
            if msg == "bad":
                raise RuntimeError("处理失败")
            print(f"  [at-most-once] 处理成功：{msg}")
            queue.acked += 1
        except Exception as exc:
            print(f"  [at-most-once] {msg} 失败：{exc} → 消息丢失")


print("== at-most-once ==")
q1 = InMemoryQueue()
for m in ("A", "bad", "C"):
    q1.publish(m)
process_at_most_once(q1)
print(f"  发布 {q1.published}，成功 {q1.acked}，丢失 {q1.published - q1.acked}")

# ---------------- 2. at-least-once ----------------
def process_at_least_once(queue, max_attempts=3):
    """处理成功才删；失败放回队尾，可能重复消费。"""
    attempts = {}
    while queue.items:
        msg = queue.items.popleft()
        attempts[msg] = attempts.get(msg, 0) + 1
        try:
            if msg == "bad" and attempts[msg] < 2:
                raise RuntimeError("第一次失败")
            print(f"  [at-least-once] 处理成功：{msg}（第 {attempts[msg]} 次）")
            queue.acked += 1
        except Exception as exc:
            if attempts[msg] >= max_attempts:
                print(f"  [at-least-once] {msg} 达到最大重试，进入死信")
            else:
                print(f"  [at-least-once] {msg} 失败：{exc} → 重新入队")
                queue.items.append(msg)


print("\n== at-least-once ==")
q2 = InMemoryQueue()
for m in ("A", "bad", "C"):
    q2.publish(m)
process_at_least_once(q2)
print(f"  发布 {q2.published}，成功 {q2.acked}")

# ---------------- 3. 重复消费与幂等 ----------------
print("\n== at-least-once 的重复问题 ==")
processed = set()
order_events = ["order-1", "order-2", "order-1"]     # 重复投递
for event in order_events:
    if event in processed:
        print(f"  {event}: 已处理，跳过（幂等）")
    else:
        processed.add(event)
        print(f"  {event}: 处理并记录")
print("  消费端用幂等键去重，才能把 at-least-once 变成“效果 exactly-once”")

# ---------------- 4. 队列 vs 主题 ----------------
print("\n== 队列 vs 主题 ==")
rows = [
    ("队列", "一条消息一个消费者", "任务分发、削峰"),
    ("主题", "一条消息广播给所有订阅者", "事件通知、状态同步"),
]
print(f"  {'模式':<6}{'投递':<24}{'场景'}")
for r in rows:
    print(f"  {r[0]:<6}{r[1]:<24}{r[2]}")

# ---------------- 5. 队列的价值 ----------------
print("\n== 为什么用消息队列 ==")
for item in [
    "解耦：下单不需要等发短信/加积分完成",
    "削峰：突发流量先入队，消费者按能力处理",
    "异步：慢操作不阻塞主链路（第449课舱壁）",
    "缓冲：消费者宕机，消息还在（持久化时）",
    "代价：最终一致、重复消费、顺序问题、运维复杂度",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 InMemoryQueue 增加“最大容量”，满了 publish 阻塞或报错。
# 2. 实现一个简单的发布订阅主题（多个订阅者各收到一份）。
# 3. 用 set 实现幂等消费，统计重复消息数量。
# 4. 思考：at-most-once 适合什么场景？为什么大多数业务选 at-least-once？
