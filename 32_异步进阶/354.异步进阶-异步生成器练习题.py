# ===== 第354课：异步进阶-异步生成器 =====
# 知识点：
#   - async def + yield = 异步生成器：写异步序列的最简形式
#   - 与 async for 配对使用；生成器推导式也支持 async
#   - 与第190课对照：yield 让出的是“值”，异步版还能顺带 await
import asyncio


async def tick(n, delay=0.05):
    """每 delay 秒吐出 1~n（模拟实时数据源）。"""
    for i in range(1, n + 1):
        await asyncio.sleep(delay)
        yield i


async def main():
    # 基本消费
    total = 0
    async for t in tick(5):
        total += t
    print("累加：", total)

    # 异步推导式（对照列表推导式，第190课）
    squares = [x * x async for x in tick(3)]
    print("异步推导式：", squares)

    # 过滤组合
    evens = [x async for x in tick(6) if x % 2 == 0]
    print("只留偶数：", evens)

    # 异步生成器 + await 混合：管道
    async def double(source):
        async for x in source:
            await asyncio.sleep(0.01)
            yield x * 2

    print("管道输出：", [x async for x in double(tick(3))])


asyncio.run(main())

# ===== 练习题 =====
# 1. 写异步生成器 read_lines(text)：按行吐出字符串，模拟逐行读取。
# 2. 用异步管道实现“读行 → 过滤空行 → 转大写”三段流水线。
# 3. 思考：异步生成器与第353课的类写法，哪个更适合快速开发？
