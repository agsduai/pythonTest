# ===== 第824课：并发模式与并发容器-并行流水线与并行映射 =====
# 知识点：
#   - 并行映射 parallel map：用线程池把函数并行应用到列表每个元素
#   - concurrent.futures：ThreadPoolExecutor / ProcessExecutor 统一接口
#   - map vs submit：map 返回有序结果；submit 返回 Future 可单独管理
#   - 并行流水线：多阶段处理，每阶段一个线程池，用队列连接
#   - GIL 影响：CPU 密集用 ProcessPoolExecutor；IO 密集用 ThreadPoolExecutor
#   - 异常传播：Future.result() 会重新抛出子任务中的异常
# 依赖：无（标准库）
from concurrent.futures import (
    ThreadPoolExecutor, ProcessPoolExecutor,
    as_completed, wait, ALL_COMPLETED, FIRST_COMPLETED,
)
import time
import math
import random


def cpu_heavy(n):
    """CPU 密集任务：计算素数个数。"""
    if n < 2: return 0
    count = 1
    for i in range(3, n+1, 2):
        is_prime = True
        for j in range(3, int(math.sqrt(i))+1, 2):
            if i % j == 0:
                is_prime = False; break
        if is_prime: count += 1
    return count


def io_heavy(n):
    """IO 密集任务模拟：sleep（不真实 sleep，用循环消耗 CPU）。"""
    result = 0
    for i in range(n * 1000):
        result += i % 7
    return result


print("== ThreadPoolExecutor.map ==")
with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(math.sqrt, [1, 4, 9, 16, 25]))
print(f"  map(sqrt, [1,4,9,16,25]) = {results}")

print("\n== submit + as_completed ==")
inputs = [1000, 5000, 10000, 15000]
with ThreadPoolExecutor(max_workers=4) as pool:
    futures = {pool.submit(cpu_heavy, n): n for n in inputs}
    for future in as_completed(futures):
        n = futures[future]
        result = future.result()
        print(f"  素数个数(1..{n}) = {result}")

print("\n== CPU 密集：Thread vs Process ==")
nums = [20000, 20000, 20000, 20000]

t0 = time.perf_counter()
with ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(cpu_heavy, nums))
t_thread = time.perf_counter() - t0

t0 = time.perf_counter()
seq_result = [cpu_heavy(n) for n in nums]
t_seq = time.perf_counter() - t0

print(f"  顺序执行: {t_seq:.3f}s")
print(f"  ThreadPool: {t_thread:.3f}s（GIL 使 CPU 密集任务无法真正并行）")
print("  GIL 只允许一个线程执行 Python 字节码 → CPU 密集需用进程")
print("  ProcessPoolExecutor 在 Windows 上需要 if __name__ == '__main__' 保护")

print("\n== IO 密集：ThreadPool 效果好 ==")
def io_task(n):
    """模拟 IO：用 time.sleep 替代真实 IO（sleep 释放 GIL）。"""
    import time
    time.sleep(0.05)
    return n

inputs = list(range(20))
t0 = time.perf_counter()
with ThreadPoolExecutor(max_workers=5) as pool:
    io_results = list(pool.map(io_task, inputs))
t_io = time.perf_counter() - t0
print(f"  20 个 IO 任务 (每个 50ms): 总耗时={t_io:.2f}s（顺序≈{20*0.05:.2f}s）")
print(f"  加速≈{20*0.05/t_io:.1f}×（IO 密集用线程池效果好）")

print("\n== Future 的高级用法 ==")
with ThreadPoolExecutor(max_workers=3) as pool:
    f1 = pool.submit(io_task, 10)
    f2 = pool.submit(io_task, 20)
    f3 = pool.submit(io_task, 30)

    # wait: 等待全部或第一个完成
    done, not_done = wait([f1, f2, f3], return_when=FIRST_COMPLETED)
    print(f"  FIRST_COMPLETED: 第一个完成的是 f{[id(f) for f in done].index(id(f1))+1 if f1 in done else '?'}")

    # result(timeout): 带超时获取
    print(f"  f1.result() = {f1.result(timeout=5)}")

    # 异常传播
    def failing_task():
        raise RuntimeError("任务失败")

    f_fail = pool.submit(failing_task)
    try:
        f_fail.result()
    except RuntimeError as e:
        print(f"  异常传播: {e}")

print("\n== 并行流水线（两阶段） ==")
def pipeline_two_stage(items):
    """阶段1: CPU 密集转换 → 阶段2: IO 密集写入。"""
    stage1_out = queue.Queue()
    final = []

    def stage1_worker(pool):
        futures = [pool.submit(lambda x: x * 2, item) for item in items]
        for f in futures:
            stage1_out.put(f.result())
        stage1_out.put(None)              # 结束标记

    def stage2_worker():
        while True:
            v = stage1_out.get()
            if v is None: break
            final.append(f"processed:{v}")

    import queue as q
    stage1_out = q.Queue()
    with ThreadPoolExecutor(max_workers=3) as pool:
        t1 = threading.Thread(target=stage1_worker, args=(pool,))
        t2 = threading.Thread(target=stage2_worker)
        t1.start(); t2.start()
        t1.join(); t2.join()
    return final

import queue
import threading
r = pipeline_two_stage(list(range(10)))
print(f"  流水线结果: {r}")

print("\n== 选择指南 ==")
for line in [
    "  CPU 密集 → ProcessPoolExecutor（绕过 GIL）",
    "  IO 密集 → ThreadPoolExecutor 或 asyncio",
    "  混合 → 先 ThreadPool 做 IO，结果给 Process 做计算",
    "  map 适合「统一转换」；submit 适合「不同函数/不同参数」",
    "  as_completed 适合「先完成先处理」；map 保持顺序",
]:
    print("  -", line)

print("\n== 工程要点 ==")
for line in [
    "  max_workers 默认 = CPU 核数×5（IO）或 CPU 核数（CPU）",
    "  ProcessPool 的参数/返回值必须可 pickle（lambda 不行）",
    "  线程池要 with 语句管理，确保 shutdown 后不留僵尸线程",
    "  超时保护：future.result(timeout=n) 防止永远等待",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 用 ProcessPoolExecutor 并行计算 4 个大数的素数个数，对比与 ThreadPool 的耗时。
# 2. 实现「带进度的并行映射」：每完成一个任务就打印进度。
# 3. 实现「可取消的并行任务」：用 Future.cancel() 取消未开始的任务。
# 4. 思考：为什么 `map` 保持输入顺序但 `as_completed` 不保持？各有什么用途？
