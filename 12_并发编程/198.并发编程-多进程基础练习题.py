# ===== 第198课：并发编程-多进程基础 =====
# 知识点：
#   - multiprocessing.Process：每个进程有独立内存和独立的 GIL
#   - CPU 密集任务用多进程才能真正并行，充分利用多核
#   - Windows 下必须写 if __name__ == "__main__":（spawn 启动方式）
#   - 进程隔离：子进程修改全局变量不影响父进程
#   - os.getpid() 查看进程号

import multiprocessing
import os
import time


def cpu_task(n):
    """CPU 密集任务：大量求和运算。"""
    print(f"进程 {os.getpid()} 开始计算")
    total = sum(i * i for i in range(n))
    print(f"进程 {os.getpid()} 计算完成")
    return total


def change_global():
    global value
    value = 999
    print(f"子进程里 value = {value}")


value = 100

if __name__ == "__main__":      # Windows 上必须有这段保护
    # 单进程串行执行两次
    start = time.perf_counter()
    cpu_task(5_000_000)
    cpu_task(5_000_000)
    print(f"串行耗时：{time.perf_counter() - start:.2f} 秒\n")

    # 两个进程并行执行
    start = time.perf_counter()
    p1 = multiprocessing.Process(target=cpu_task, args=(5_000_000,))
    p2 = multiprocessing.Process(target=cpu_task, args=(5_000_000,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    print(f"双进程耗时：{time.perf_counter() - start:.2f} 秒\n")

    # 进程隔离演示：子进程改不了父进程的变量
    p3 = multiprocessing.Process(target=change_global)
    p3.start()
    p3.join()
    print(f"父进程里 value = {value}（仍然是 100，进程内存互相独立）")

# ===== 练习题 =====
# 1. 把 if __name__ == "__main__": 注释掉再运行，观察 Windows 上会报什么错。
# 2. 把任务量改成 20_000_000，对比串行与双进程的加速比。
# 3. 用 multiprocessing.cpu_count() 查看本机核心数，开对应数量的进程。
# 4. 思考：多进程的开销在哪里？什么情况下反而更慢？
