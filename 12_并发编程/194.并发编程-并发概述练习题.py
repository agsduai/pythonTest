# ===== 第194课：并发编程-并发概述 =====
# 知识点：
#   - 串行/并发/并行：排队做、交替做、同时做
#   - 进程：独立内存，稳定、开销大；线程：共享内存，轻量、需注意安全
#   - 协程：单线程内主动让出执行权的并发，最适合 IO 等待
#   - GIL：CPython 中同一进程内同一时刻只有一个线程执行字节码
#   - 选型：IO 密集（网络/磁盘）→ 线程或协程；CPU 密集 → 多进程

import threading
import time


def download(name):
    """模拟一次下载：耗时 1 秒（sleep 属于 IO 等待，不占 CPU）。"""
    print(f"开始下载 {name}")
    time.sleep(1)
    print(f"完成下载 {name}")


# 串行：三个任务排队，总耗时约 3 秒
start = time.perf_counter()
for name in ("文件A", "文件B", "文件C"):
    download(name)
print(f"串行总耗时：{time.perf_counter() - start:.2f} 秒\n")


# 并发：任务同时在“等 IO”，等待时间重叠，总耗时约 1 秒
start = time.perf_counter()
threads = []
for name in ("文件A", "文件B", "文件C"):
    t = threading.Thread(target=download, args=(name,))
    threads.append(t)
    t.start()
for t in threads:
    t.join()          # 等待所有线程结束再计时
print(f"并发总耗时：{time.perf_counter() - start:.2f} 秒")

# 说明：CPU 密集任务用多线程几乎不会更快（GIL 限制），需要用多进程（第198课）。

# ===== 练习题 =====
# 1. 把下载时间改成 2 秒，观察串行与并发的总耗时各是多少。
# 2. 把任务数量加到 5 个，验证并发耗时依然接近单个任务的时间。
# 3. 写一个 CPU 密集函数（如 sum(range(10_000_000))），分别串行执行 2 次
#    和用 2 个线程执行，对比总耗时，验证 GIL 的说法。
# 4. 思考：你手头的项目里哪些活是 IO 密集，哪些是 CPU 密集？
