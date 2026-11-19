# ===== 第1100课：itertools迭代工具-chain与count =====
# 知识点：
#   - import itertools：itertools.chain(*多个可迭代)：把多个列表"串起来"遍历
#   - chain.from_iterable(嵌套列表)：串起"列表的列表"
#   - count(start, step)：无限计数器，必须配 islice/break 限量，否则死循环
#   - 实际场景：合并多个班名单、流水号生成、限量取数

# 案例一：chain 串联多个列表
import itertools

class_a = ["小张", "小李"]
class_b = ["小王", "小赵"]
class_c = ["小周"]
all_students = list(itertools.chain(class_a, class_b, class_c))
print(f"合并名单：{all_students}")

# 案例二：from_iterable 处理嵌套结构
# 场景：每个订单的商品列表拍平
orders = [["苹果", "牛奶"], ["面包"], ["鸡蛋", "酸奶", "可乐"]]
items = list(itertools.chain.from_iterable(orders))
print(f"全部商品：{items}")

# 案例三：count 无限计数器
# 场景：生成订单号，取前 5 个就停
counter = itertools.count(start=1001, step=1)
order_ids = []
for _ in range(5):
    order_ids.append(f"ORD-{next(counter)}")
print(f"订单号：{order_ids}")

# 案例四：islice 给无限序列"限量"
# islice(可迭代, n) 只取前 n 个，count 就安全了
ids = list(itertools.islice(itertools.count(1, 10), 5))  # 1, 11, 21, 31, 41
print(f"步长 10 的 5 个号：{ids}")

# 案例五：count 的小数步长
temps = list(itertools.islice(itertools.count(36.0, 0.5), 6))
print(f"模拟体温计刻度：{temps}")

# ===== 练习题 =====
# 1. 用 chain 把 ["a","b"]、[1,2,3]、"xy" 串起来打印（注意：字符串会拆成单字符）。
# 2. 用 chain.from_iterable 把 [[1,2],[3],[4,5,6]] 拍平，并与 116 章的嵌套推导式写法对比，两者结果应一致。
# 3. 写函数 take(n, start, step)：用 islice + count 返回前 n 个数，测试 take(4, 0, 2.5)。
