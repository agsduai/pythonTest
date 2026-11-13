# ===== 第249课：算法入门-分治与归并快排 =====
# 知识点：
#   - 分治：拆成小问题 → 分别解决 → 合并结果
#   - 归并排序：稳定 O(n log n)，需要额外空间
#   - 快速排序：平均 O(n log n)，按基准分区，最坏 O(n²)
#   - 递归的三要素：出口、拆分、合并（复习第069课）


def merge(left, right):
    """合并两个有序列表。"""
    result, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])      # 把剩下的直接接上
    result.extend(right[j:])
    return result


def merge_sort(data):
    if len(data) <= 1:           # 递归出口：1 个元素天然有序
        return data[:]
    mid = len(data) // 2
    left = merge_sort(data[:mid])        # 拆
    right = merge_sort(data[mid:])
    return merge(left, right)            # 合


def quick_sort(data):
    if len(data) <= 1:
        return data[:]
    pivot = data[len(data) // 2]         # 选中间元素当基准
    small = [x for x in data if x < pivot]
    equal = [x for x in data if x == pivot]
    large = [x for x in data if x > pivot]
    return quick_sort(small) + equal + quick_sort(large)


import random

nums = [random.randint(1, 99) for _ in range(10)]
print("原数组：", nums)
print("归并：", merge_sort(nums))
print("快排：", quick_sort(nums))
print("内置：", sorted(nums))

assert merge_sort(nums) == sorted(nums)
assert quick_sort(nums) == sorted(nums)
print("两种实现与内置 sorted 结果一致")

# 归并的单步演示：合并 [1,5,9] 和 [2,6]
print("合并演示：", merge([1, 5, 9], [2, 6]))

# ===== 练习题 =====
# 1. 给 merge_sort 加打印，观察递归“拆”与“合”的顺序。
# 2. 把快排基准换成 data[0]，在已排序列表上测试，解释为什么会退化成 O(n²)。
# 3. 归并排序是“稳定”的：构造 [(1,'a'),(1,'b')] 类数据验证稳定性差异。
# 4. 思考：快排的 extra 空间版（本课写法）与真正的原地分区版差在哪？
