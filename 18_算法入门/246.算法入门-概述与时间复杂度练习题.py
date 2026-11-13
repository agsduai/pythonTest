# ===== 第246课：算法入门-概述与时间复杂度 =====
# 知识点：
#   - 算法：解决问题的步骤；评价看时间与空间两个维度
#   - 大O表示法：描述“数据量增大时，耗时的增长趋势”
#   - 常见等级：O(1) < O(log n) < O(n) < O(n log n) < O(n²)
#   - 关键思维：不看绝对秒数，看“n 翻倍后耗时怎么变”

import time


def get_first(data):          # O(1)：与数据量无关
    return data[0]


def linear_sum(data):         # O(n)：数据翻倍，耗时约翻倍
    total = 0
    for x in data:
        total += x
    return total


def has_duplicate(data):      # O(n²)：双层循环
    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            if data[i] == data[j]:
                return True
    return False


def halving_steps(n):         # O(log n)：每次砍一半
    count = 0
    while n > 1:
        n //= 2
        count += 1
    return count


print(get_first([1, 2, 3]), halving_steps(1_000_000))   # O(1) 与 O(log n)
print(linear_sum(range(10)), has_duplicate([1, 2, 3, 1]))


# 实测增长趋势：n 翻倍，O(n) 耗时约翻倍，O(n²) 耗时约 4 倍
def measure(func, n):
    data = list(range(n))
    start = time.perf_counter()
    func(data)
    return time.perf_counter() - start


for n in (1_000, 2_000, 4_000):
    t_n = measure(linear_sum, n)
    t_n2 = measure(has_duplicate, n)
    print(f"n={n}: O(n) 耗时 {t_n:.4f}s | O(n²) 耗时 {t_n2:.4f}s")

# ===== 练习题 =====
# 1. 判断下列操作的大O：list[0]、list.append、list.insert(0, x)、dict[key]。
# 2. 把 halving_steps(1_000_000) 和 math.log2(1_000_000) 对比。
# 3. 观察上表：n 每翻倍，两种算法的耗时分别大约乘几？
# 4. 思考：为什么大O只讲“趋势”，不讲“具体多少秒”？
