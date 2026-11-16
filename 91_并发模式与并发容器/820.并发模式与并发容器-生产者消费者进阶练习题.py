# ===== 第820课：并发模式与并发容器-生产者消费者进阶 =====
# 知识点：
#   - 生产者-消费者进阶：多生产者→多消费者、优先级队列、毒丸关闭
#   - queue.PriorityQueue：按优先级出队而非 FIFO
#   - 毒丸（poison pill）：往队列放哨兵值，消费者收到后退出
#   - 有界队列：queue.Queue(maxsize=n) 提供背压（生产者阻塞）
#   - 与第12章的基础版对比：12 章用 Queue 做简单 FIFO，本课加优先级/毒丸/多阶段
#   - 毒丸数量 = 消费者数量，否则有消费者永远不退出
# 依赖：无（标准库）
import queue
import threading
import random
import time
from dataclasses import dataclass, field


@dataclass(order=True)
class Task:
    priority: int
    payload: str = field(compare=False)


def multi_producer_consumer():
    """2 生产者 + 3 消费者，毒丸关闭。"""
    q = queue.Queue(maxsize=20)
    results = []
    result_lock = threading.Lock()
    NUM_CONSUMERS = 3
    POISON = None

    def producer(producer_id, items):
        for item in items:
            q.put(item)
        # 每个生产者发 NUM_CONSUMERS // 生产者数 个毒丸
        for _ in range(NUM_CONSUMERS // 2):
            q.put(POISON)

    def consumer(consumer_id):
        processed = 0
        while True:
            item = q.get()
            if item is POISON:
                q.put(POISON)              # 把毒丸传给下一个消费者
                break
            with result_lock:
                results.append((consumer_id, item))
            processed += 1

    producers = [
        threading.Thread(target=producer, args=(0, [f"P0-task{i}" for i in range(20)])),
        threading.Thread(target=producer, args=(1, [f"P1-task{i}" for i in range(20)])),
    ]
    consumers = [threading.Thread(target=consumer, args=(i,)) for i in range(NUM_CONSUMERS)]
    for t in producers + consumers: t.start()
    for t in producers: t.join()
    for t in consumers: t.join()
    return results


print("== 多生产者→多消费者（毒丸关闭）==")
results = multi_producer_consumer()
print(f"  共处理 {len(results)} 个任务")
consumer_counts = {}
for cid, _ in results:
    consumer_counts[cid] = consumer_counts.get(cid, 0) + 1
print(f"  消费者分布: {consumer_counts}")
print("  毒丸只发 NUM_CONSUMERS 个，但只有最后一个消费者会把多余的毒丸传下去")
print("  关键：收到毒丸后再放回队列，让其他消费者也能退出")


class PriorityQueueDemo:
    """优先级队列：高优先级任务先处理。"""

    def __init__(self):
        self.pq = queue.PriorityQueue()
        self.results = []

    def produce(self):
        tasks = [
            Task(priority=3, payload="清理缓存"),
            Task(priority=1, payload="支付回调"),
            Task(priority=2, payload="发送邮件"),
            Task(priority=1, payload="退款处理"),
            Task(priority=3, payload="日志压缩"),
            Task(priority=2, payload="推送通知"),
        ]
        for t in tasks:
            self.pq.put(t)
        for _ in range(len(tasks)):
            self.pq.put(None)              # 毒丸

    def consume(self):
        while True:
            task = self.pq.get()
            if task is None:
                break
            self.results.append((task.priority, task.payload))

    def run(self):
        p = threading.Thread(target=self.produce)
        c = threading.Thread(target=self.consume)
        p.start(); c.start()
        p.join(); c.join()
        return self.results


print("\n== 优先级队列 ==")
demo = PriorityQueueDemo()
for pr, payload in demo.run():
    print(f"    priority={pr} {payload}")
print("  优先级 1（支付/退款）先于 3（清理/日志）处理")


print("\n== 有界队列提供背压 ==")
def test_backpressure(maxsize, items, producer_speed=0):
    q = queue.Queue(maxsize=maxsize)
    produced, blocked = 0, 0
    for item in items:
        try:
            q.put(item, block=False)
            produced += 1
        except queue.Full:
            blocked += 1
    return produced, blocked, q.qsize()

for maxsize in (5, 10, 50):
    p, b, qs = test_backpressure(maxsize, list(range(30)))
    print(f"  maxsize={maxsize:>3}: 放入={p} 阻塞拒绝={b} 队列当前={qs}")
print("  有界队列在消费跟不上时自然产生背压，防止生产者无限膨胀")

print("\n== 多阶段流水线 ==")
def pipeline_demo():
    """阶段1: 生成数字 → 阶段2: 平方 → 阶段3: 累加"""
    stage1 = queue.Queue()
    stage2 = queue.Queue()
    results = []

    def stage1_producer():
        for i in range(20):
            stage1.put(i)
        stage1.put(None)

    def stage2_square():
        while True:
            v = stage1.get()
            if v is None:
                stage2.put(None); break
            stage2.put(v * v)

    def stage3_sum():
        total = 0
        while True:
            v = stage2.get()
            if v is None: break
            total += v
        results.append(total)

    threads = [
        threading.Thread(target=stage1_producer),
        threading.Thread(target=stage2_square),
        threading.Thread(target=stage3_sum),
    ]
    for t in threads: t.start()
    for t in threads: t.join()
    return results

r = pipeline_demo()
print(f"  流水线结果: Σi² for i in 0..19 = {r[0]}")
print(f"  验证: {sum(i*i for i in range(20))}")

print("\n== 模式对比 ==")
for line in (
    "  简单 FIFO: queue.Queue() — 一对一或一对多",
    "  优先级: PriorityQueue — 任务有轻重缓急",
    "  LIFO: LifoQueue — 撤销/栈语义",
    "  多阶段: 多个 Queue 串联 — 每阶段独立线程池",
    "  背压: maxsize 限制 — 防止生产过快内存爆炸",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  毒丸数量必须 = 消费者数量，否则有消费者永远不退出",
    "  更优雅的关闭：消费者检查「毒丸计数 + 队列空」而不是等毒丸",
    "  超时 get(timeout=n) 可以加「取消标志」实现优雅关闭",
    "  与第68章调度器结合：优先级队列就是调度器的核心数据结构",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「可取消的消费者」：加一个 threading.Event 控制取消标志。
# 2. 实现多阶段流水线的「错误传播」：阶段 2 失败时阶段 3 不再处理后续项。
# 3. 用 queue.LifoQueue 实现「撤销栈」：最新操作优先撤销。
# 4. 思考：为什么毒丸方案在「消费者数量动态变化」时会出问题？
