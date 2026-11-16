# ===== 第517课：消息队列与事件驱动-消费组与分区 =====
# 知识点：
#   - 分区（partition）：把一个主题拆成多个有序队列，提升并行度
#   - 分区键：同一业务键（如 user_id/order_id）落到同一分区 → 局部有序
#   - 消费组：组内每个消费者负责部分分区，一条消息只被组内一个消费者处理
#   - 再均衡（rebalance）：消费者加入/退出时重新分配分区
#   - 顺序保证：只保证“单分区内有序”，不保证全局有序
#   - 与第240课并发服务端、第515课队列模型的区别：这里是“并行 + 顺序”的折中
import hashlib
from collections import deque


def partition_of(key: str, partitions: int) -> int:
    """稳定分区：同一 key 永远同一分区。"""
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % partitions


class PartitionedTopic:
    def __init__(self, name: str, partitions: int):
        self.name = name
        self.partitions = [deque() for _ in range(partitions)]
        self.offsets = [0] * partitions

    def publish(self, key: str, payload):
        p = partition_of(key, len(self.partitions))
        self.partitions[p].append((key, payload))
        return p

    def poll(self, partition: int):
        if self.partitions[partition]:
            return self.partitions[partition].popleft()
        return None

    def sizes(self):
        return [len(q) for q in self.partitions]


class ConsumerGroup:
    def __init__(self, name: str, topic: PartitionedTopic, consumers: list[str]):
        self.name = name
        self.topic = topic
        self.consumers = consumers
        self.assignment: dict[str, list[int]] = {}
        self.rebalance()

    def rebalance(self):
        """轮询分配分区给组内消费者。"""
        n = len(self.topic.partitions)
        self.assignment = {c: [] for c in self.consumers}
        for p in range(n):
            owner = self.consumers[p % len(self.consumers)]
            self.assignment[owner].append(p)
        print(f"  [rebalance] {self.name} 分配：{self.assignment}")

    def leave(self, consumer: str):
        self.consumers.remove(consumer)
        self.rebalance()

    def join(self, consumer: str):
        self.consumers.append(consumer)
        self.rebalance()

    def run_once(self):
        """每个消费者处理自己负责的分区各一条消息。"""
        processed = []
        for consumer, partitions in self.assignment.items():
            for p in partitions:
                item = self.topic.poll(p)
                if item:
                    processed.append((consumer, p, item))
        return processed


topic = PartitionedTopic("orders", partitions=4)
print("== 发布消息 ==")
for i in range(1, 13):
    key = f"user-{i % 5}"                 # 5 个用户，映射到 4 个分区
    p = topic.publish(key, f"订单{i}（{key}）")
    print(f"  {key} → 分区 {p}")
print("  各分区消息数：", topic.sizes())

print("\n== 消费组（2 个消费者）==")
group = ConsumerGroup("order-group", topic, ["消费者A", "消费者B"])

for round_no in range(1, 4):
    print(f"\n  第 {round_no} 轮：")
    processed = group.run_once()
    for consumer, p, item in processed:
        print(f"    {consumer} 处理分区{p}：{item[1]}")
    if not processed:
        print("    （队列已空）")

print("\n== 分区内有序，分区之间无序 ==")
topic2 = PartitionedTopic("events", partitions=2)
for i in range(1, 5):
    topic2.publish("user-A", f"A-{i}")     # 同一 key → 同一分区
    topic2.publish("user-B", f"B-{i}")
print("  分区消息：", topic2.sizes())
for p in range(2):
    seq = []
    while True:
        item = topic2.poll(p)
        if item is None:
            break
        seq.append(item[1])
    print(f"  分区{p} 顺序：{seq}")

print("\n== 消费者退出 → 再均衡 ==")
group.leave("消费者B")
group.run_once()

print("\n== 消费者加入 → 再均衡 ==")
group.join("消费者C")
group.join("消费者D")
group.run_once()

# ---- 关键结论 ----
print("\n== 关键结论 ==")
for item in [
    "分区数决定最大并行度（消费者多于分区会闲置）",
    "同一 key 固定同分区 → 同一用户的订单有序",
    "跨分区不保证顺序，业务要接受或做全局排序",
    "再均衡期间可能重复消费/短暂停顿 → 消费端幂等",
    "分区数一般提前规划，扩容分区会破坏 key 的映射",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把分区数改成 2，观察同一用户的顺序与并行度变化。
# 2. 实现“按 key 哈希 + 增加分区”后的重新映射，说明为什么会乱序。
# 3. 模拟消费者处理很慢，观察其他消费者是否能分担。
# 4. 思考：为什么 Kafka 的消费者数通常不超过分区数？
