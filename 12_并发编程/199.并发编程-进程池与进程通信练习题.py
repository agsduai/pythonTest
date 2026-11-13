# ===== 第199课：并发编程-进程池与进程通信 =====
# 知识点：
#   - multiprocessing.Pool：进程池，复用进程，支持 map / apply_async
#   - 多进程不能直接共享变量，进程间通信用 Queue
#   - Queue.put / get：生产者-消费者模式
#   - with Pool() 结束时自动等待并回收进程

import multiprocessing
import os


def square(x):
    """每个进程处理一个数字。"""
    return x * x


def producer(q):
    for i in range(3):
        q.put(f"进程{os.getpid()} 生产的 数据{i}")
    q.put(None)          # 放入结束标记


def consumer(q):
    while True:
        item = q.get()
        if item is None:     # 收到结束标记，退出
            break
        print(f"消费：{item}")


if __name__ == "__main__":
    # 进程池：map 把任务自动分给池里的进程
    with multiprocessing.Pool(processes=4) as pool:
        results = pool.map(square, range(8))
        print("map 结果：", results)

        # apply_async：异步提交单个任务
        future = pool.apply_async(square, (10,))
        print("异步结果：", future.get())

    # 进程间通信：Queue + 生产者消费者
    queue = multiprocessing.Queue()
    p1 = multiprocessing.Process(target=producer, args=(queue,))
    p2 = multiprocessing.Process(target=consumer, args=(queue,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    print("进程通信结束")

# ===== 练习题 =====
# 1. 用 pool.map 对 1~100 万的每个数求立方，与单进程版本对比耗时。
# 2. 给 consumer 增加计数，最后打印共消费了多少条数据。
# 3. 尝试在 producer 里修改全局变量并在父进程读取，验证“行不通”，
#    从而理解为什么需要 Queue。
# 4. 思考：线程池与进程池分别适合什么任务？
