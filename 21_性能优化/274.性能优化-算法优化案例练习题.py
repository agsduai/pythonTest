# ===== 第274课：性能优化-算法优化案例 =====
# 知识点：
#   - 优化优先级：换算法 > 换数据结构 > 微优化
#   - 案例一：两数之和 O(n²) 双循环 → O(n) 哈希表
#   - 案例二：判重 O(n²) → set O(n)
#   - 核心思想：用空间换时间，把“重复比较”变成“一次查询”

import random
import time


def two_sum_slow(nums, target):
    """双循环：把所有配对试一遍。"""
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return i, j
    return None


def two_sum_fast(nums, target):
    """哈希表：记住“需要什么”，一查便知。"""
    seen = {}                      # 值 -> 下标
    for i, x in enumerate(nums):
        need = target - x
        if need in seen:
            return seen[need], i
        seen[x] = i
    return None


nums = list(range(2000))
random.shuffle(nums)
target = 3997

start = time.perf_counter()
r1 = two_sum_slow(nums, target)
t1 = time.perf_counter() - start

start = time.perf_counter()
r2 = two_sum_fast(nums, target)
t2 = time.perf_counter() - start

print(f"两数之和：慢版 {t1:.4f}s → 快版 {t2:.6f}s（答案 {r1} / {r2}）")


# ---- 案例二：判重 ----
def has_dup_slow(items):
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                return True
    return False


def has_dup_fast(items):
    return len(set(items)) != len(items)


items = list(range(10_000))

start = time.perf_counter()
print("判重(慢)：", has_dup_slow(items), f"{time.perf_counter() - start:.4f}s")
start = time.perf_counter()
print("判重(快)：", has_dup_fast(items), f"{time.perf_counter() - start:.6f}s")

# 优化套路总结：
#   ① 找到热点（cProfile） ② 看它的复杂度 ③ 问“能不能用哈希/排序/分治换掉”

# ===== 练习题 =====
# 1. 把两数之和的 nums 规模翻倍，验证慢版耗时约 4 倍、快版约 2 倍。
# 2. 实现“三数之和”的暴力版与优化版（提示：固定一个数 + 两数之和）。
# 3. 把第253课 SimpleHashMap 的思想复述成一句话：为什么查询能 O(1)？
# 4. 思考：空间换时间的极限在哪里？什么时候反过来“用时间省空间”？
