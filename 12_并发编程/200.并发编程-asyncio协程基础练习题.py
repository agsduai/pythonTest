# ===== 第200课：并发编程-asyncio协程基础 =====
# 知识点：
#   - async def 定义协程函数，调用它返回协程对象，不会立即执行
#   - await 让出执行权：等待期间事件循环去跑别的协程
#   - asyncio.run(主协程) 启动事件循环
#   - asyncio.gather 并发运行多个协程，全部完成后一起返回
#   - 协程是单线程并发：没有锁的烦恼，但不能使用阻塞调用

import asyncio
import time


async def download(name, delay):
    """async def 定义协程函数；await 处让出执行权。"""
    print(f"开始下载 {name}")
    await asyncio.sleep(delay)      # 模拟 IO 等待（不能写成 time.sleep！）
    print(f"完成下载 {name}")
    return f"{name} 的数据"


async def main():
    # 顺序执行：一个接一个
    start = time.perf_counter()
    await download("文件A", 0.5)
    await download("文件B", 0.5)
    print(f"顺序执行耗时：{time.perf_counter() - start:.2f} 秒\n")

    # 并发执行：gather 同时安排多个协程
    start = time.perf_counter()
    results = await asyncio.gather(
        download("文件C", 0.8),
        download("文件D", 0.5),
        download("文件E", 0.3),
    )
    print(f"并发执行耗时：{time.perf_counter() - start:.2f} 秒")
    print("gather 返回：", results)


asyncio.run(main())     # 事件循环的入口

# 说明：await asyncio.sleep 是异步等待；
# 换成 time.sleep 会阻塞整个事件循环，并发立刻失效。

# ===== 练习题 =====
# 1. 把 asyncio.sleep 换成 time.sleep 再运行，观察并发为什么“失效”。
# 2. 用 gather 并发执行 5 个 download（每个 1 秒），验证总耗时仍约 1 秒。
# 3. print(type(download("x", 0.1))) 查看协程对象类型。
# 4. 思考：协程与线程的本质区别是什么？为什么协程间一般不需要加锁？
