# ===== 第201课：并发编程-asyncio并发控制 =====
# 知识点：
#   - asyncio.create_task：把协程包装成任务，立即调度执行
#   - asyncio.Semaphore：限制同时运行的协程数量
#   - async with：异步上下文管理器
#   - gather(return_exceptions=True)：收集异常而不是中断全部任务

import asyncio
import time


async def fetch(name, delay):
    print(f"开始 {name}")
    await asyncio.sleep(delay)
    print(f"完成 {name}")
    return f"{name} 完成"


async def main():
    # create_task：任务立即开始调度，不等 await
    task = asyncio.create_task(fetch("后台任务", 0.5))
    print("任务已创建，继续做别的事……")
    result = await task
    print("后台任务结果：", result, "\n")

    # Semaphore：最多 2 个任务同时跑
    semaphore = asyncio.Semaphore(2)

    async def limited_fetch(name):
        async with semaphore:               # 拿到“名额”才能执行
            return await fetch(name, 0.3)

    start = time.perf_counter()
    await asyncio.gather(*(limited_fetch(f"任务{i}") for i in range(5)))
    print(f"限流并发耗时：{time.perf_counter() - start:.2f} 秒（5 个任务、每批 2 个）\n")

    # 收集异常：某个任务失败不影响其他任务
    async def may_fail(name):
        await asyncio.sleep(0.1)
        if name == "坏任务":
            raise ValueError(f"{name} 出错了")
        return f"{name} 正常"

    results = await asyncio.gather(
        may_fail("好任务1"), may_fail("坏任务"), may_fail("好任务2"),
        return_exceptions=True,
    )
    print("gather 结果：", results)     # 异常对象也会出现在结果里


asyncio.run(main())

# ===== 练习题 =====
# 1. 把 Semaphore(2) 改成 (1) 和 (5)，观察耗时变化。
# 2. 用 asyncio.as_completed 按完成顺序处理 3 个 fetch 任务。
# 3. 给 gather 不加 return_exceptions=True 再运行，观察一个异常如何“带崩”全局。
# 4. 思考：爬虫场景下，限流（Semaphore）保护的到底是谁？
