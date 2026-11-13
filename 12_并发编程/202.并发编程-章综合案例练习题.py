# ===== 第202课：并发编程-章综合案例 =====
# 知识点：
#   - 综合运用：线程池处理 IO 任务 + 统一收集结果 + 汇总统计
#   - 场景：模拟批量下载 10 个文件，有的成功有的失败
#   - 要点：任务隔离（单个失败不影响其他）、结果统一收集、耗时统计

import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def download(url):
    """模拟下载：随机耗时，20% 概率失败。"""
    time.sleep(random.uniform(0.1, 0.5))
    if random.random() < 0.2:
        raise ConnectionError(f"{url} 连接超时")
    return f"{url} 的内容（{random.randint(100, 999)}KB）"


def batch_download(urls, max_workers=4):
    """批量下载并收集成功/失败结果。"""
    success, failed = [], []
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(download, url): url for url in urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                success.append(future.result())
                print(f"[成功] {url}")
            except Exception as exc:
                failed.append((url, str(exc)))
                print(f"[失败] {url}：{exc}")
    cost = time.perf_counter() - start
    return success, failed, cost


urls = [f"https://cdn.example.com/file{i}.zip" for i in range(1, 11)]
success, failed, cost = batch_download(urls)

print("\n========== 汇总 ==========")
print(f"成功 {len(success)} 个，失败 {len(failed)} 个，总耗时 {cost:.2f} 秒")
for url, err in failed:
    print(f"  失败：{url}（{err}）")

# ===== 练习题 =====
# 1. 把 max_workers 改成 1 和 10，对比总耗时，体会并发度的作用。
# 2. 增加重试逻辑：失败的 url 用线程池再试一次（复用 batch_download 思路）。
# 3. 把 download 换成 async 版本，用 asyncio.gather 实现同样的批量下载。
# 4. 思考：success/failed 只在主线程（as_completed 循环里）修改，为什么线程安全？
