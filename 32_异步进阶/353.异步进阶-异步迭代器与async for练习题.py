# ===== 第353课：异步进阶-异步迭代器与async for =====
# 知识点：
#   - __aiter__ / __anext__ + StopAsyncIteration：异步版迭代器协议
#   - async for：消费“取每条数据本身要等待”的序列
#   - 与第189课对照：普通迭代器是同步取值，异步迭代器每步都可 await
#   - 典型场景：分页 API、消息队列、实时数据流
import asyncio


class AsyncCounter:
    """每 0.1 秒吐出一个数字的异步序列。"""

    def __init__(self, n):
        self.n = n
        self.i = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.i >= self.n:
            raise StopAsyncIteration           # 异步版“迭代结束”
        await asyncio.sleep(0.1)               # 取数据需要等待 ← 为什么必须异步
        self.i += 1
        return self.i


async def main():
    async for num in AsyncCounter(3):
        print("收到：", num)

    # 与 list 不同：异步序列往往“无限/未知长”，靠 async for 边取边处理
    total = 0
    async for num in AsyncCounter(5):
        total += num
    print("累计：", total)


asyncio.run(main())

# ===== 练习题 =====
# 1. 写一个 AsyncFibonacci：异步吐出斐波那契数列前 n 项。
# 2. 给 AsyncCounter 加“跳过偶数”参数，用 async for 验证。
# 3. 思考：什么信号说明该用异步迭代器而不是普通迭代器？
#    （提示：取数据的动作本身要 await）
