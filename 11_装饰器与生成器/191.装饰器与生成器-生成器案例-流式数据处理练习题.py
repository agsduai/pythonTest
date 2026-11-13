# ===== 第191课：装饰器与生成器-生成器案例-流式数据处理 =====
# 知识点：
#   - 生成器管道：读取 → 过滤 → 解析，多个生成器串联成流水线
#   - 流式处理：任何时刻内存中只有一条数据，适合处理超大文件
#   - sum() 等聚合函数可以直接接在生成器管道末尾
#   - 管道思路与 SQL 的 SELECT...WHERE 一致

import os

DATA_FILE = "sales_demo_191.txt"

# 准备演示数据：一万条销售记录（真实场景可能是一个几 GB 的日志）
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for i in range(1, 10_001):
            f.write(f"订单{i},商品{i % 5},金额{10 + i % 90}\n")


def read_lines(path):
    """管道第一环：逐行读取文件（for line in f 本身就是流式的）。"""
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield line.strip()


def filter_lines(lines, keyword):
    """管道中间环节：只放行包含关键词的行。"""
    for line in lines:
        if keyword in line:
            yield line


def parse_amount(lines):
    """管道末段：把 '订单1,商品2,金额35' 解析成金额。"""
    for line in lines:
        yield float(line.rsplit("金额", 1)[1])


# 三个生成器串成管道：没有任何一步把全部数据装进内存
pipeline = parse_amount(filter_lines(read_lines(DATA_FILE), "商品3"))
print(f"商品3 销售总额：{sum(pipeline):.2f}")

# 管道可以复用：换个关键词就是一条新流水线
hot = parse_amount(filter_lines(read_lines(DATA_FILE), "商品1"))
print(f"商品1 销售总额：{sum(hot):.2f}")

# 对照组：一次性读入内存的写法（数据量大时会占满内存）
with open(DATA_FILE, encoding="utf-8") as f:
    total = sum(
        float(line.rsplit("金额", 1)[1])
        for line in f
        if "商品2" in line
    )
print(f"商品2 销售总额（一次性写法）：{total:.2f}")

# 清理演示文件
os.remove(DATA_FILE)

# ===== 练习题 =====
# 1. 在管道中加一环 filter_by_amount(lines, min_value)，只保留金额
#    不小于 min_value 的记录，统计商品4 的“大额订单”数量。
# 2. 编写生成器函数统计文件总行数，与 sum(1 for _ in open(...)) 对比。
# 3. 打印 pipeline 的 type()，验证它是生成器对象。
# 4. 思考：为什么 for line in f 读大文件不会把内存撑爆？
