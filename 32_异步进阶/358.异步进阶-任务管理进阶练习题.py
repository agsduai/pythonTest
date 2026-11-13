# ===== 第358课：异步进阶-任务管理进阶 =====
# 知识点：
#   - TaskGroup（3.11+）：结构化并发 —— 组内一个失败，全组取消，异常打包抛出
#   - except*：接住 ExceptionGroup 的专用语法
#   - as_completed：谁先完成先处理（复习第201课）
#   - 选型：任务“同生共死”用 TaskGroup；各自独立用 gather(return_exceptions=True)
import asyncio
import time


async def job(name, delay, fail=False):
    await asyncio.sleep(delay)
    if fail:
        raise ValueError(f"{name} 出错")
    return f"{name} 完成"


async def main():
    # ---- TaskGroup：结构化并发 ----
    t3 = None
    try:
        async with asyncio.TaskGroup() as tg:
            t1 = tg.create_task(job("任务A", 0.3))
            t2 = tg.create_task(job("任务B", 0.2, fail=True))
            t3 = tg.create_task(job("任务C", 0.5))
    except* ValueError as eg:                       # 3.11+ 异常组语法
        print("TaskGroup 捕获：", [str(e) for e in eg.exceptions])
    # 结构化并发的核心语义：组内一个失败，其余任务被“连带取消”
    print("  A 是否被连带取消：", t1.cancelled(), "| C 是否被连带取消：", t3.cancelled())

    # ---- gather(return_exceptions=True)：各自独立、互不牵连 ----
    results = await asyncio.gather(
        job("任务D", 0.1),
        job("任务E", 0.1, fail=True),
        job("任务F", 0.1),
        return_exceptions=True,
    )
    print("gather 结果：", results)

    # ---- as_completed：先完成先处理 ----
    tasks = [asyncio.create_task(job(f"J{i}", d)) for i, d in enumerate([0.3, 0.1, 0.2])]
    for fut in asyncio.as_completed(tasks):
        print("先到先得：", await fut)


asyncio.run(main())

# ===== 练习题 =====
# 1. 把 TaskGroup 里的 B 改成成功，验证三人全部有结果。
# 2. 用 as_completed 统计“先完成的前 2 个任务名”。
# 3. 思考：支付回调（一个失败不该牵连其他）适合 TaskGroup 还是 gather？
