# ===== 毕业实操题 · 项目05：异步并发采集器 =====
# 难度：★★★★☆    建议用时：8~10 小时
# 覆盖章节：11 生成器 / 12 并发 / 32 异步进阶 / 34 测试进阶
# 详细任务书：见同目录 README.md「项目 05」
#
# 需求速览：
#   python collector.py run --total 50 --workers 6 --limit 5
#     - fetch(url)：asyncio.sleep 模拟网络（0.05~0.8s），20% 概率失败
#     - N 个 worker 从 asyncio.Queue 取任务；全局并发上限 Semaphore(limit)
#     - 单 URL 最多重试 3 次，退避 0.2/0.4/0.8 秒
#     - 成功写 done.json；再次运行自动跳过（断点续跑）
#     - 结果写 results.json（url/大小/耗时/尝试次数）；失败写 failed.json
#     - Ctrl+C 优雅退出，保存已完成部分
#
# 实现要求：
#   1. 必须使用 asyncio.Queue + Semaphore + wait_for + gather
#   2. worker 数量与并发上限分离（worker 多不代表并发高）
#   3. 落盘统一在主协程完成（不要并发写同一个文件）
#   4. 测试用 unittest.IsolatedAsyncioTestCase + AsyncMock
#
# 当前文件为「任务书骨架」：直接运行会打印任务卡。

import argparse
import asyncio
import json
import random
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

RESULTS = Path("results.json")
FAILED = Path("failed.json")
DONE = Path("done.json")


async def simulate_fetch(url: str) -> dict:
    """模拟一次网络请求：随机耗时，20% 抛 ConnectionError。"""
    raise NotImplementedError("TODO: await asyncio.sleep(random.uniform(...))")


async def fetch_with_retry(url: str, retries: int = 3) -> dict:
    """带重试与超时：返回 {url, size, cost, attempts, ok}；用 wait_for 设超时。"""
    raise NotImplementedError("TODO: 实现退避重试（0.2/0.4/0.8）")


def load_done() -> set[str]:
    """读 done.json，不存在返回空集合。"""
    raise NotImplementedError("TODO: 实现 load_done")


def save_state(results: list[dict], failed: list[str]) -> None:
    """主协程调用：写 results.json / failed.json / done.json。"""
    raise NotImplementedError("TODO: 实现 save_state（原子写入）")


async def worker(name: str, queue: asyncio.Queue, sem: asyncio.Semaphore,
                 results: list[dict], failed: list[str], progress: dict) -> None:
    """从队列取 URL → 限流执行 → 收集结果 → task_done()；收到 None 退出。"""
    raise NotImplementedError("TODO: 实现 worker")


async def run_collector(total: int, workers: int, limit: int) -> int:
    """组装队列/信号量/worker，等待完成并落盘。返回失败数。"""
    raise NotImplementedError("TODO: 实现 run_collector")


def make_urls(total: int) -> list[str]:
    return [f"https://example.com/item/{i}" for i in range(total)]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="collector.py", description="异步并发采集器")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("run")
    p.add_argument("--total", type=int, default=50)
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--reset", action="store_true", help="清空断点记录")
    args = parser.parse_args(argv)
    if args.command == "run":
        raise NotImplementedError("TODO: 调用 asyncio.run(run_collector(...))")
    return 0


# ---------- 自测（实现后删除 @unittest.skip） ----------
class TestCollector(unittest.IsolatedAsyncioTestCase):

    @unittest.skip("实现后删除本行")
    async def test_fetch_retry_then_success(self):
        # 用 AsyncMock(side_effect=[ConnectionError, ConnectionError, 成功dict])
        # 断言 attempts == 3 且 ok 为 True
        pass

    @unittest.skip("实现后删除本行")
    async def test_timeout(self):
        # 用 wait_for 包一个 sleep(1) 的假 fetch，timeout=0.01
        pass

    @unittest.skip("实现后删除本行")
    async def test_queue_workers_process_all(self):
        # 10 个 URL、3 个 worker、limit=2：断言结果 10 条且无重复
        pass

    @unittest.skip("实现后删除本行")
    async def test_resume_skips_done(self):
        # done.json 里预置 5 个 URL，断言本轮只处理剩余
        pass

    @unittest.skip("实现后删除本行")
    def test_save_state_files(self):
        pass


def print_task_card():
    print("=" * 64)
    print("毕业实操题 · 项目05  异步并发采集器")
    print("=" * 64)
    print("目标：队列分发 + 信号量限流 + 重试退避 + 断点续跑 + 优雅退出")
    print("\n验收清单：")
    for item in [
        "50 个 URL 全部有终态（成功或失败），无遗漏",
        "并发上限生效（同时运行数 <= limit）",
        "第二次运行自动跳过已成功 URL",
        "失败 URL 有 3 次尝试记录（failed.json）",
        "Ctrl+C 能保存已完成部分",
        "4 个异步测试全部通过（删除 @unittest.skip 后）",
    ]:
        print(f"  [ ] {item}")
    print("\n下一步：")
    print("  1. 先写 simulate_fetch + fetch_with_retry，单 URL 调试")
    print("  2. 再写 worker：queue.get → sem → 重试 → 收集 → task_done")
    print("  3. run_collector 负责发 URL + 哨兵 + gather(workers)")
    print("  4. 最后加断点续跑与 Ctrl+C 处理")
    print("  5. 测试：AsyncMock 模拟成功/失败，IsolatedAsyncioTestCase 隔离事件循环")


if __name__ == "__main__":
    print_task_card()
    sys.exit(0)
