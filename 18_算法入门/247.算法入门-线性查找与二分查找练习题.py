# ===== 第247课：算法入门-线性查找与二分查找 =====
# 知识点：
#   - 线性查找 O(n)：逐个比对，无需有序
#   - 二分查找 O(log n)：每次砍掉一半，前提是“已排序”
#   - 100 万条数据：线性最坏 100 万次，二分最多 20 次
#   - 二分的核心：low/high/mid 三个指针的维护

import math


def linear_search(data, target):
    for i, x in enumerate(data):
        if x == target:
            return i
    return -1


def binary_search(data, target):
    """data 必须是升序排列。"""
    low, high = 0, len(data) - 1
    while low <= high:
        mid = (low + high) // 2
        if data[mid] == target:
            return mid
        elif data[mid] < target:
            low = mid + 1          # 目标在右半边
        else:
            high = mid - 1         # 目标在左半边
    return -1


nums = list(range(0, 100, 7))
print(nums)
print("线性查找 42：", linear_search(nums, 42))
print("二分查找 42：", binary_search(nums, 42))
print("二分查找 41（不存在）：", binary_search(nums, 41))


# 打印折半过程，直观感受“砍一半”
def binary_trace(data, target):
    low, high = 0, len(data) - 1
    step = 0
    while low <= high:
        mid = (low + high) // 2
        step += 1
        print(f"第{step}步：范围[{data[low]}~{data[high]}]，中点 {data[mid]}")
        if data[mid] == target:
            return step
        elif data[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1


binary_trace(list(range(1, 101)), 77)

print(f"100 万数据：线性最坏 1000000 次，二分最多 {math.ceil(math.log2(1_000_000))} 次")

# ===== 练习题 =====
# 1. 在乱序列表上用二分查找会怎样？动手验证并解释。
# 2. 编写 binary_search_recursive：用递归实现二分（复习第069课）。
# 3. 统计查找 1~128 之间每个数时二分的比较次数，最大值是多少？
# 4. 思考：list.index() 用的是哪种查找？为什么它不要求有序？
