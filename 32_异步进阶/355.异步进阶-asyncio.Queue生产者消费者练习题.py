# ===== 第355课：异步进阶-asyncio.Queue生产者消费者 =====
# 知识点：
#   - asyncio.Queue：协程间的“传送带”（对照第199课进程 Queue）
#   - maxsize 限容：生产过快自动背压（put 等待有空位）
#   - get/task_done：多消费者并发取活，互不重复
#   - 生产/消费速度解耦：各自按自己的节奏干活
import asyncio
import time


async def producer(queue, n):
    for i in range(n):
        await asyncio.sleep(0.03)          # 模拟生产耗时
        await queue.put(f"数据{i}")
        print(f"[生产] 数据{i}（队列长度 {queue.qsize()}）")
    for _ in range(2):                     # 两个消费者各发一个结束哨兵
        await queue.put(None)


async def consumer(name, queue):
    while True:
        item = await queue.get()
        if item is None:                   # 收到哨兵，下班
            break
        await asyncio.sleep(0.1)           # 模拟处理耗时
        print(f"[{name}] 处理完 {item}")
        queue.task_done()


async def main():
    queue = asyncio.Queue(maxsize=3)       # 限容 3：生产太快会自动等待
    start = time.perf_counter()
    await asyncio.gather(
        producer(queue, 6),
        consumer("消费者A", queue),
        consumer("消费者B", queue),
    )
    print(f"总耗时 {time.perf_counter() - start:.2f} 秒")


asyncio.run(main())

# ===== 练习题 =====
# 1. 把消费者加到 3 个，观察总耗时变化。
# 2. 统计每个消费者各处理了几条（Counter 收集）。
# 3. 思考：哨兵个数为什么等于消费者个数？少发一个会发生什么？
