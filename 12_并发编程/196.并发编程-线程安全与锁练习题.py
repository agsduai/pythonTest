# ===== 第196课：并发编程-线程安全与锁 =====
# 知识点：
#   - 竞态条件：多线程同时读写共享数据，结果取决于执行时序
#   - counter += 1 不是原子操作：读 → 加 → 写 三步可能被打断
#   - threading.Lock：with lock 保证同一时刻只有一个线程进入临界区
#   - 锁会降低并发度：尽量缩小锁的保护范围
#   - threading.Semaphore(n)：允许 n 个线程同时进入

import threading
import time

counter = 0


def unsafe_increase(n):
    global counter
    for _ in range(n):
        counter += 1        # 非原子操作，线程切换时会互相覆盖


threads = [threading.Thread(target=unsafe_increase, args=(100_000,)) for _ in range(2)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print(f"无锁结果：{counter}（期望 200000，实际可能更少）")


# 加锁版本：保证“读-加-写”三步一次性完成
counter = 0
lock = threading.Lock()


def safe_increase(n):
    global counter
    for _ in range(n):
        with lock:          # 进入 with 自动 acquire，离开自动 release
            counter += 1


threads = [threading.Thread(target=safe_increase, args=(100_000,)) for _ in range(2)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print(f"加锁结果：{counter}（每次都是 200000）")


# 信号量：限制同时进入的线程数量
sem = threading.Semaphore(2)    # 最多 2 个线程同时打印


def limited_print(task_id):
    with sem:
        print(f"任务 {task_id} 拿到名额，开始处理")
        time.sleep(0.2)


threads = [threading.Thread(target=limited_print, args=(i,)) for i in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()

# 说明：CPython 有 GIL，单条字节码不会被打断，但 += 这类组合操作依然需要锁。

# ===== 练习题 =====
# 1. 把无锁版本改成 4 个线程各加 50000 次，观察结果是否更乱。
# 2. 试试把 with lock 移到整个 for 循环外面，对比两种加锁方式的执行时间。
# 3. 编写两个线程互相抢两把锁的场景，制造“死锁”，再想想怎么避免。
# 4. 思考：锁太多会牺牲性能，锁太少会出竞态，实际项目怎么取舍？
