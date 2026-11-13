# ===== 第356课：异步进阶-超时与取消 =====
# 知识点：
#   - asyncio.wait_for(协程, timeout)：超时自动取消任务并抛 TimeoutError
#   - asyncio.timeout(3.11+)：async with 版本，作用域更清晰
#   - task.cancel()：主动取消；协程内捕获 CancelledError 做清理
#   - 惯例：清理完要把 CancelledError 继续抛出去，别吞
import asyncio


async def slow_job(seconds):
    try:
        await asyncio.sleep(seconds)
        return "完成"
    except asyncio.CancelledError:
        print("  [清理] 收到取消信号，回滚现场……")
        raise                                  # 清理后继续抛，让上层知道被取消


async def main():
    # ---- wait_for：超时拦截 ----
    try:
        await asyncio.wait_for(slow_job(2), timeout=0.3)
    except TimeoutError:
        print("wait_for：0.3 秒未完成，已拦截")

    # ---- asyncio.timeout：3.11+ 的推荐写法 ----
    try:
        async with asyncio.timeout(0.3):
            await slow_job(2)
    except TimeoutError:
        print("asyncio.timeout：同样拦截，作用域写法更直观")

    # ---- 主动取消 ----
    task = asyncio.create_task(slow_job(2))
    await asyncio.sleep(0.2)
    task.cancel()                              # 发出取消信号
    try:
        await task                             # 等协程处理完取消
    except asyncio.CancelledError:
        print("任务确认已被取消")

    # ---- 超时但任务其实能完成 ----
    result = await asyncio.wait_for(slow_job(0.1), timeout=1)
    print("正常完成：", result)


asyncio.run(main())

# ===== 练习题 =====
# 1. 用 wait_for 给“三个不同耗时任务”分别设超时，统计成功/超时数。
# 2. 思考：CancelledError 为什么不该被静默吞掉？
# 3. 进阶：asyncio.shield 保护“关键写入”不被取消（查文档试用一次）。
