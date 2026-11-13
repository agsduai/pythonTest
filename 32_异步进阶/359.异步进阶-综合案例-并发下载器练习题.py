# ===== 第359课：异步进阶-综合案例-并发下载器 =====
# 知识点：
#   - 综合运用：Queue 任务分发（355）+ Semaphore 限流（357）
#     + 超时与重试（356）+ 结果统计
#   - 不发真实网络请求：用 asyncio.sleep 模拟，专注结构
#   - 这套骨架把 requests 换成 aiohttp 就是真实爬虫（第08章进阶）
import asyncio
import random
import time


async def simulate_http(url):
    """模拟一次 HTTP 请求：随机耗时，20% 概率足够慢而触发超时。"""
    await asyncio.sleep(random.uniform(0.05, 0.65))
    return f"{url} 的内容（{random.randint(1, 999)}KB）"


async def worker(name, queue, sem, stats):
    while True:
        url = await queue.get()
        if url is None:                    # 哨兵：下班
            break
        async with sem:                    # 全局并发限流
            ok = False
            for attempt in range(1, 4):    # 最多重试 3 次
                try:
                    body = await asyncio.wait_for(simulate_http(url), timeout=0.4)
                    stats["成功"] += 1
                    print(f"[{name}] ✓ {url}（第 {attempt} 次）")
                    ok = True
                    break
                except TimeoutError:
                    print(f"[{name}] … {url} 第 {attempt} 次超时")
            if not ok:
                stats["失败"] += 1
        queue.task_done()
    print(f"[{name}] 收工")


async def main():
    urls = [f"https://cdn.example.com/file{i}.zip" for i in range(12)]
    queue = asyncio.Queue()
    sem = asyncio.Semaphore(3)             # 全局最多 3 个在途请求
    stats = {"成功": 0, "失败": 0}

    n_workers = 3
    workers = [asyncio.create_task(worker(f"工人{i}", queue, sem, stats))
               for i in range(n_workers)]
    for url in urls:
        await queue.put(url)
    for _ in range(n_workers):
        await queue.put(None)              # 每人一个哨兵

    start = time.perf_counter()
    await asyncio.gather(*workers)
    print(f"统计：{stats}，总耗时 {time.perf_counter() - start:.2f} 秒")


asyncio.run(main())

# ===== 练习题 =====
# 1. 把 Semaphore 改成 1 和 6，观察总耗时变化。
# 2. 统计每个工人的工作量（dict 收集）。
# 3. 进阶：给失败任务记录到 JSON（第232课），支持“失败重跑”。
# 4. 思考：限流保护的到底是本机还是目标服务器？（对照第201课）
