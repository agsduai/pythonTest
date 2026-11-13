# ===== 第357课：异步进阶-同步原语 =====
# 知识点：
#   - asyncio.Lock / Semaphore / Event：线程版（第196课）的协程版
#   - 异步锁：await 等锁期间事件循环去跑别的协程，不阻塞线程
#   - Semaphore：并发限流（第201课已预览，本课放进完整场景）
#   - Event：一等多广播信号
import asyncio


async def worker(name, lock, counter_box):
    async with lock:                       # 拿到锁才进临界区
        current = counter_box[0]
        await asyncio.sleep(0.05)          # 模拟“读-改-写”之间的等待
        counter_box[0] = current + 1


async def main():
    # ---- Lock：保护共享计数 ----
    lock = asyncio.Lock()
    counter_box = [0]
    await asyncio.gather(*(worker(f"协程{i}", lock, counter_box) for i in range(5)))
    print("加锁计数结果：", counter_box[0], "（无锁会是 <5 的随机值）")

    # ---- Semaphore：最多 2 个协程同时进入 ----
    sem = asyncio.Semaphore(2)

    async def limited(i):
        async with sem:
            print(f"  任务{i} 进入（同时最多 2 个）")
            await asyncio.sleep(0.2)

    await asyncio.gather(*(limited(i) for i in range(4)))

    # ---- Event：发令枪 ----
    event = asyncio.Event()

    async def runner(name):
        print(f"  {name} 就位，等待发令……")
        await event.wait()
        print(f"  {name} 冲出起跑线！")

    runners = [asyncio.create_task(runner(n)) for n in ("甲", "乙", "丙")]
    await asyncio.sleep(0.1)
    print("发令！")
    event.set()                            # 一次唤醒所有等待者
    await asyncio.gather(*runners)


asyncio.run(main())

# ===== 练习题 =====
# 1. 把 Lock 注释掉重跑，观察计数是否偶尔 <5（协程切换点在 await 处）。
# 2. 用 Semaphore + 第359课预演：限制并发“下载”为 3。
# 3. 思考：单线程的协程为什么还需要锁？（提示：await 处就是切换点）
