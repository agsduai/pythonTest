# ===== 第823课：并发模式与并发容器-CSP与通道模式 =====
# 知识点：
#   - CSP（Communicating Sequential Processes）：通过通道通信而非共享状态
#   - 与 Actor 的区别：通道是「一等公民」，可以被多个发送者/接收者共享
#   - Go 语言的 goroutine + channel 就是 CSP；Python 用 queue.Queue 模拟
#   - select 模式：同时监听多个通道（Go 的 select），Python 用轮询或 queue.Queue
#   - 工作池 worker pool via channels：N 个 worker 共享一个输入通道
#   - 扇入 fan-in：多个生产者的输出合并到一个通道；扇出 fan-out：分发到多个消费者
# 依赖：无（标准库）
import queue
import threading
import random
import time
from collections import Counter


class Channel:
    """简化通道：包装 queue.Queue，提供 close 语义。"""

    def __init__(self, maxsize=0):
        self._q = queue.Queue(maxsize=maxsize)
        self._closed = False
        self._lock = threading.Lock()

    def send(self, item):
        with self._lock:
            if self._closed:
                raise ValueError("通道已关闭")
        self._q.put(item)

    def recv(self, timeout=None):
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self):
        with self._lock:
            self._closed = True
            # 发送哨兵唤醒等待的接收者
            try: self._q.put(None, block=False)
            except queue.Full: pass

    @property
    def closed(self):
        with self._lock:
            return self._closed

    def __len__(self):
        return self._q.qsize()


def fan_in(channels, output):
    """扇入：多个通道合并到一个输出通道。"""
    def worker(ch):
        while True:
            item = ch.recv(timeout=1)
            if item is None:
                break
            output.send(item)
    threads = [threading.Thread(target=worker, args=(ch,)) for ch in channels]
    for t in threads: t.start()
    return threads


def fan_out(input_ch, outputs):
    """扇出：把输入通道的数据轮流分发到多个输出通道。"""
    def worker():
        idx = 0
        while True:
            item = input_ch.recv(timeout=1)
            if item is None:
                for o in outputs: o.close()
                break
            outputs[idx % len(outputs)].send(item)
            idx += 1
    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return t


print("== Channel 基本操作 ==")
ch = Channel(maxsize=3)
for i in range(3):
    ch.send(f"msg{i}")
print(f"  队列长度={len(ch)}")
ch.close()
print(f"  closed={ch.closed}")
try:
    ch.send("after-close")
except ValueError as e:
    print(f"  关闭后发送: {e}")

print("\n== 扇入 Fan-in：3 个生产者 -> 1 个消费者 ==")
inputs = [Channel() for _ in range(3)]
output = Channel()
threads = fan_in(inputs, output)
results = []
for i, ch in enumerate(inputs):
    threading.Thread(
        target=lambda ch=ch, tag=i: [ch.send(f"src{tag}-msg{j}") for j in range(5)]
    ).start()
for _ in range(15):
    item = output.recv(timeout=2)
    if item: results.append(item)
for t in threads: t.join()
print(f"  收到 {len(results)} 条消息（期望 15）")
print(f"  来源分布: {Counter(s.split('-')[0] for s in results)}")

print("\n== 扇出 Fan-out：1 个生产者 -> N 个消费者 ==")
input_ch = Channel()
outputs = [Channel() for _ in range(3)]
fan_out(input_ch, outputs)
collector_results = [[] for _ in outputs]
collector_threads = []
for i, o in enumerate(outputs):
    def collect(idx=i, ch=o):
        while True:
            item = ch.recv(timeout=1)
            if item is None: break
            collector_results[idx].append(item)
    t = threading.Thread(target=collect)
    t.start(); collector_threads.append(t)

for i in range(12):
    input_ch.send(f"task{i}")
input_ch.close()
for t in collector_threads: t.join()
print(f"  分发结果: {[r for r in collector_results]}")
print("  每个 worker 只处理分给它的部分 -> 天然负载均衡（如果按队列语义）")

print("\n== 工作池 via Channels ==")
def worker_pool_via_channels(tasks, n_workers=3):
    task_ch = Channel()
    result_ch = Channel()
    for t in tasks: task_ch.send(t)
    task_ch.close()

    def worker(wid):
        while True:
            task = task_ch.recv(timeout=1)
            if task is None: break
            result_ch.send(f"worker{wid}:{task}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_workers)]
    for t in threads: t.start()
    results = []
    while True:
        r = result_ch.recv(timeout=2)
        if r is None: break
        results.append(r)
    for t in threads: t.join()
    return results

tasks = [f"job{i}" for i in range(15)]
results = worker_pool_via_channels(tasks, n_workers=3)
print(f"  15 个任务 3 个 worker: 完成 {len(results)} 个")
worker_counts = Counter(r.split(":")[0] for r in results)
print(f"  Worker 负载: {dict(worker_counts)}")

print("\n== CSP vs Actor vs 线程+锁 ==")
print(f"  {'维度':<16}{'CSP（通道）':<22}{'Actor':<22}{'线程+锁'}")
for row in (("通信", "通道（可共享）", "信箱（Actor 私有）", "共享内存"),
            ("耦合度", "松（只依赖通道）", "松（只依赖消息）", "紧（共享状态）"),
            ("关闭语义", "显式 close", "毒丸/stop", "线程 join"),
            ("典型语言", "Go / Clojure", "Erlang / Akka", "Java / Python")):
    print(f"  {row[0]:<16}{row[1]:<22}{row[2]:<22}{row[3]}")

print("\n== 工程要点 ==")
for line in [
    "  通道关闭后应通知接收方（发哨兵或让 recv 返回 None）",
    "  扇入/扇出是构建数据流管道的基础算子",
    "  Python 的 asyncio.Queue 是异步版的 Channel（第32章）",
    "  CSP 消除锁竞争，但通道本身可能有瓶颈（单一序列化点）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「select」模式：同时监听多个通道，任一有数据就处理。
# 2. 实现带缓冲的通道（有容量限制），发送端在满时阻塞或丢弃。
# 3. 用 Channel 构建三阶段流水线：读取 → 转换 → 写入。
# 4. 思考：CSP 的「通道共享」与 Actor 的「信箱私有」各有什么优缺点？
