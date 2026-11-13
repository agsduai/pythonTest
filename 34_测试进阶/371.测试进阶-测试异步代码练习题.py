# ===== 第371课：测试进阶-测试异步代码 =====
# 知识点：
#   - IsolatedAsyncioTestCase：每个测试自动跑在独立事件循环里
#   - 测试方法直接写成 async def，内部正常 await
#   - 超时/取消也能测（对接第356课）
#   - 运行方式与普通 unittest 完全一致
import asyncio
import unittest


async def fetch_data(delay, value):
    await asyncio.sleep(delay)
    return value


async def fetch_all():
    """并发取两个数据源（第200课 gather）。"""
    return await asyncio.gather(fetch_data(0.01, "A"), fetch_data(0.02, "B"))


class TestAsyncFetch(unittest.IsolatedAsyncioTestCase):

    async def test_single(self):
        self.assertEqual(await fetch_data(0.001, "X"), "X")

    async def test_order_preserved(self):
        self.assertEqual(await fetch_all(), ["A", "B"])   # gather 按提交顺序

    async def test_timeout(self):
        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(fetch_data(1, "Y"), timeout=0.01)

    async def test_concurrent_is_faster(self):
        import time
        start = time.perf_counter()
        await fetch_data(0.01, "A")
        await fetch_data(0.02, "B")
        serial = time.perf_counter() - start
        start = time.perf_counter()
        await fetch_all()
        concurrent = time.perf_counter() - start
        self.assertLess(concurrent, serial, "并发应快于串行累加")


if __name__ == "__main__":
    unittest.main(verbosity=2)

# ===== 练习题 =====
# 1. 给第355课的生产者消费者写测试：断言 6 条数据都被处理。
# 2. 用 Mock(side_effect=AsyncMock?) 思考：异步函数的替身该是什么？
#    （答案：unittest.mock.AsyncMock —— 查文档用一次）
# 3. 思考：为什么每个测试要“独立事件循环”？（隔离状态，互不污染）
