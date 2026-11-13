# ===== 第235课：常用标准库-itertools =====
# 知识点：
#   - itertools：迭代器工具箱 —— 惰性求值、处理大数据不占内存
#   - count/cycle/repeat：无限迭代器（记得用 islice 或 break 截断）
#   - accumulate：滚动累计；groupby：相邻分组
#   - product/permutations/combinations：排列组合
#   - chain：把多个可迭代对象串成一条流

import itertools

# 无限迭代器
counter = itertools.count(start=10, step=5)
print([next(counter) for _ in range(3)])       # [10, 15, 20]

c = itertools.cycle(["A", "B"])
print([next(c) for _ in range(5)])             # A B A B A

# 滚动累计：前缀和 / 滚动最大值
print(list(itertools.accumulate([1, 2, 3, 4])))
print(list(itertools.accumulate([3, 1, 4, 1, 5], max)))

# groupby：相邻同键元素分一组（必须先按同一键排序！）
data = sorted([("a", 1), ("b", 2), ("a", 3)], key=lambda kv: kv[0])
for key, group in itertools.groupby(data, key=lambda kv: kv[0]):
    print(key, [kv for kv in group])

# 笛卡尔积 / 排列 / 组合
print(list(itertools.product("AB", "12")))
print(list(itertools.permutations("ABC", 2)))
print(list(itertools.combinations("ABC", 2)))

# chain：串接多个可迭代对象
print(list(itertools.chain([1, 2], "ab", (3,))))

# islice：给无限迭代器“装刹车”
print(list(itertools.islice(itertools.count(1), 5)))

# 实用组合：批处理（每 3 个一组）
def batch(iterable, size):
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, size))
        if not chunk:
            return
        yield chunk


print(list(batch(range(1, 11), 3)))

# ===== 练习题 =====
# 1. 用 itertools.product 打印所有两位密码组合（00~99）。
# 2. 用 accumulate 计算每日余额滚动最大值。
# 3. 用 cycle 模拟“轮流值班表”：4个人排 7 天。
# 4. 思考：groupby 为什么要求先排序？不排序会发生什么？
