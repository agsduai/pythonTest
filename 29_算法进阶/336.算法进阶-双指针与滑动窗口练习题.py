# ===== 第336课：算法进阶-双指针与滑动窗口 =====
# 知识点：
#   - 对撞指针：头尾向中间收 —— 有序数组两数之和 O(n)
#   - 快慢指针：同向前进，原地去重/移除
#   - 滑动窗口：右扩左收，把“子串/子数组”问题降到 O(n)
#   - 与第274课呼应：嵌套循环 → 双指针，也是“换算法”级别的优化
# 依赖：无

# ---- 对撞指针：有序数组两数之和 ----
def two_sum_sorted(nums, target):
    left, right = 0, len(nums) - 1
    while left < right:
        s = nums[left] + nums[right]
        if s == target:
            return left, right
        if s < target:
            left += 1               # 和太小 → 左指针右移
        else:
            right -= 1              # 和太大 → 右指针左移
    return None


print("两数之和：", two_sum_sorted([2, 7, 11, 15], 9))

# ---- 快慢指针：原地移除重复（数组已排序）----
def remove_duplicates(nums):
    if not nums:
        return 0
    slow = 0
    for fast in range(1, len(nums)):
        if nums[fast] != nums[slow]:
            slow += 1
            nums[slow] = nums[fast]
    return slow + 1


arr = [1, 1, 2, 3, 3, 3, 4]
k = remove_duplicates(arr)
print("去重后长度：", k, "前 k 位：", arr[:k])

# ---- 滑动窗口：最长无重复字符子串 ----
def max_unique_length(s):
    window, left, best = set(), 0, 0
    for right, ch in enumerate(s):
        while ch in window:          # 有重复 → 左边收缩
            window.remove(s[left])
            left += 1
        window.add(ch)
        best = max(best, right - left + 1)
    return best


print("abcabcbb 最长无重复：", max_unique_length("abcabcbb"))     # 3
print("pwwkew  最长无重复：", max_unique_length("pwwkew"))        # 3

# ---- 滑动窗口：和 >= target 的最短子数组（正数版）----
def min_subarray_len(nums, target):
    left, total, best = 0, 0, float("inf")
    for right, x in enumerate(nums):
        total += x                            # 右扩
        while total >= target:
            best = min(best, right - left + 1)
            total -= nums[left]               # 左收
            left += 1
    return best if best != float("inf") else 0


print("最短子数组长度：", min_subarray_len([2, 3, 1, 2, 4, 3], 7))   # 2 → [4,3]

# ===== 练习题 =====
# 1. 对撞指针判断回文串（忽略大小写与非字母，对照第212课）。
# 2. 滑动窗口求“长度为 k 的子数组最大和”（固定窗口）。
# 3. 思考：双指针能成立的前提通常是“有序”或“单调”，为什么？
