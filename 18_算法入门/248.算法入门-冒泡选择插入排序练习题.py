# ===== 第248课：算法入门-冒泡选择插入排序 =====
# 知识点：
#   - 三种 O(n²) 排序：冒泡（相邻交换）、选择（每轮挑最小）、插入（扑克牌式）
#   - 共同点：维护一个“有序区”，每轮扩大一个位置
#   - 冒泡加 swapped 标记可以在已有序时提前结束
#   - 实际项目直接用内置 sorted（Timsort，O(n log n)）

import random


def bubble_sort(data):
    arr = data[:]                        # 复制，不改原列表
    n = len(arr)
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):       # 尾部已有序，每轮少比一次
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:                  # 一轮没交换 = 已经有序
            break
    return arr


def selection_sort(data):
    arr = data[:]
    for i in range(len(arr) - 1):
        min_idx = i
        for j in range(i + 1, len(arr)):  # 在无序区找最小
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]   # 放到有序区末尾
    return arr


def insertion_sort(data):
    arr = data[:]
    for i in range(1, len(arr)):
        key = arr[i]                     # 摸到的“新牌”
        j = i - 1
        while j >= 0 and arr[j] > key:   # 把比它大的牌依次右移
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key                 # 插入空位
    return arr


nums = [random.randint(1, 50) for _ in range(8)]
print("原数组：", nums)
print("冒泡：", bubble_sort(nums))
print("选择：", selection_sort(nums))
print("插入：", insertion_sort(nums))
print("内置：", sorted(nums))

# 用断言验证三种实现都正确（复习第211课）
assert bubble_sort(nums) == sorted(nums)
assert selection_sort(nums) == sorted(nums)
assert insertion_sort(nums) == sorted(nums)
print("三种实现与内置 sorted 结果一致")

# ===== 练习题 =====
# 1. 给冒泡排序加打印，输出每一轮之后的数组状态。
# 2. 把三种排序改成降序（只改一处比较符号）。
# 3. 用第246课的测量思路对比 n=2000 时插入排序与内置 sorted 的耗时。
# 4. 思考：插入排序在“基本有序”的数据上为什么特别快？
