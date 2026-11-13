# ===== 第197课：并发编程-线程池 =====
# 知识点：
#   - ThreadPoolExecutor：复用固定数量的线程，避免频繁创建销毁
#   - submit() 提交单个任务返回 Future，result() 拿结果
#   - map() 批量提交，按提交顺序返回结果
#   - as_completed() 谁先完成先处理谁
#   - with 语句保证所有任务结束后才退出

import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def fetch(url, delay=0.5):
    """模拟网络请求。"""
    time.sleep(delay)
    return f"{url} 的响应内容"


# submit：一次提交一个任务
with ThreadPoolExecutor(max_workers=3) as pool:
    future = pool.submit(fetch, "https://a.com")
    print(future.result())        # result() 会阻塞直到任务完成


# map：批量提交，结果顺序与提交顺序一致
with ThreadPoolExecutor(max_workers=3) as pool:
    urls = [f"https://site{i}.com" for i in range(5)]
    for result in pool.map(fetch, urls):
        print(result)

# as_completed：先完成的先处理，不等慢任务
with ThreadPoolExecutor(max_workers=5) as pool:
    futures = {
        pool.submit(fetch, f"https://site-{d}.com", d): f"site-{d}"
        for d in (1.5, 1.0, 0.6, 0.3, 0.9)
    }
    for future in as_completed(futures):
        print(f"先完成先处理 → {future.result()}")


# 异常处理：任务里的异常在 result() 时才抛出
def bad_fetch(url):
    if url.endswith("bad.com"):
        raise ConnectionError("连接失败")
    return "ok"


with ThreadPoolExecutor() as pool:
    f = pool.submit(bad_fetch, "https://bad.com")
    try:
        f.result()
    except ConnectionError as exc:
        print(f"任务出错：{exc}")

# ===== 练习题 =====
# 1. 把 max_workers 改成 1，对比批量任务的执行时间。
# 2. 用线程池并发“下载”10 个任务，统计成功数量和总耗时。
# 3. 对比 pool.map 与 as_completed 的结果顺序，说明各自适合的场景。
# 4. 思考：线程池的大小是不是越大越好？
