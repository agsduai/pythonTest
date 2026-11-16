# ===== 第497课：动态规划专题-DP优化三板斧 =====
# 知识点：
#   - 滚动数组：只保留上一层状态，空间从 O(n×C) 降到 O(C)
#   - 前缀和 + 哈希：把“子数组和”问题从 O(n²) 降到 O(n)
#   - 单调队列：维护窗口内最小值/最大值，把 O(nk) 降到 O(n)
#   - 优化前提：先写出朴素 DP，再观察“依赖哪些旧状态”
#   - 与第423课单调队列、第424课树状数组的呼应
# 依赖：无
from collections import deque


# ---------------- 1. 滚动数组：0/1 背包 ----------------
def knapsack_2d(weights, values, capacity):
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for c in range(capacity + 1):
            dp[i][c] = dp[i - 1][c]
            if weights[i - 1] <= c:
                dp[i][c] = max(dp[i][c], dp[i - 1][c - weights[i - 1]] + values[i - 1])
    return dp[n][capacity]


def knapsack_1d(weights, values, capacity):
    dp = [0] * (capacity + 1)
    for w, v in zip(weights, values):
        for c in range(capacity, w - 1, -1):
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[capacity]


W = [3, 2, 2, 4, 1]
V = [8, 5, 4, 9, 2]
print("== 滚动数组 ==")
print(f"  二维结果：{knapsack_2d(W, V, 8)} | 一维结果：{knapsack_1d(W, V, 8)}")
print("  空间：O(n×C) → O(C)，时间不变")

# 另一个例子：不同路径（只能向右/向下）
def unique_paths_2d(m, n):
    dp = [[1] * n for _ in range(m)]
    for i in range(1, m):
        for j in range(1, n):
            dp[i][j] = dp[i - 1][j] + dp[i][j - 1]
    return dp[m - 1][n - 1]


def unique_paths_1d(m, n):
    dp = [1] * n
    for _ in range(1, m):
        for j in range(1, n):
            dp[j] += dp[j - 1]
    return dp[-1]


print("\n  不同路径 3×4：二维", unique_paths_2d(3, 4), "| 一维", unique_paths_1d(3, 4))

# ---------------- 2. 前缀和 + 哈希：和为 K 的子数组个数 ----------------
def subarray_sum_naive(nums, k):
    count = 0
    for i in range(len(nums)):
        total = 0
        for j in range(i, len(nums)):
            total += nums[j]
            if total == k:
                count += 1
    return count


def subarray_sum_prefix(nums, k):
    """prefix[j] - prefix[i] == k → 查 prefix[i] == prefix[j] - k 出现几次。"""
    seen = {0: 1}
    prefix = count = 0
    for x in nums:
        prefix += x
        count += seen.get(prefix - k, 0)
        seen[prefix] = seen.get(prefix, 0) + 1
    return count


nums = [1, 2, 3, -2, 2, 1, 1]
print("\n== 前缀和 + 哈希 ==")
print("  数组：", nums)
print(f"  和为 3 的子数组：朴素 {subarray_sum_naive(nums, 3)} 个，"
      f"前缀和 {subarray_sum_prefix(nums, 3)} 个")
print("  复杂度：O(n²) → O(n)")

# ---------------- 3. 单调队列：长度不超过 k 的最大子数组和 ----------------
def max_sum_at_most_k_naive(nums, k):
    best = float("-inf")
    for i in range(len(nums)):
        total = 0
        for j in range(i, min(len(nums), i + k)):
            total += nums[j]
            best = max(best, total)
    return best


def max_sum_at_most_k(nums, k):
    """prefix[j] - min(prefix[i])，i 在窗口 [j-k, j-1] 内。"""
    prefix = [0]
    for x in nums:
        prefix.append(prefix[-1] + x)

    dq = deque()                      # 存下标，prefix 值递增
    best = float("-inf")
    for j in range(len(prefix)):
        while dq and dq[0] < j - k:   # 窗口左边界滑出
            dq.popleft()
        if dq:
            best = max(best, prefix[j] - prefix[dq[0]])
        while dq and prefix[dq[-1]] >= prefix[j]:
            dq.pop()
        dq.append(j)
    return best


arr = [4, -1, 2, 1, -5, 4]
print("\n== 单调队列优化 ==")
print("  数组：", arr, "| 最长长度 k=3")
print(f"  朴素：{max_sum_at_most_k_naive(arr, 3)} | 单调队列：{max_sum_at_most_k(arr, 3)}")
print("  复杂度：O(nk) → O(n)")

# ---------------- 4. 优化决策树 ----------------
print("\n== 先朴素，再优化 ==")
for item in [
    "写出 dp 表，标出 dp[i][j] 依赖哪些格子",
    "只依赖上一行 → 滚动数组",
    "需要“区间和” → 前缀和",
    "需要“窗口内最值” → 单调队列 / 堆 / 树状数组",
    "需要“以前所有状态的最值” → 维护全局 best，避免重复扫描",
]:
    print("  -", item)

# ---------------- 5. 不要过早优化 ----------------
print("\n== 提醒 ==")
print("  n <= 1000 时 O(n²) 往往够用；先保证正确性")
print("  优化会牺牲可读性，务必保留朴素版本做对拍测试")
print("  对拍：随机生成小数据，比较两版结果（第211课断言）")

# ===== 练习题 =====
# 1. 用滚动数组优化 LCS 的空间（第493课）。
# 2. 用前缀和求“和恰好为 K 的最长子数组长度”。
# 3. 用单调队列优化“跳跃游戏”的最少步数（进阶）。
# 4. 思考：滚动数组倒序/正序分别对应什么背包？
