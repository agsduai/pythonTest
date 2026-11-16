# ===== 第492课：动态规划专题-最长递增子序列LIS =====
# 知识点：
#   - LIS：最长严格递增子序列（不要求连续）
#   - O(n²) DP：dp[i] = 以 i 结尾的 LIS 长度；dp[i] = 1 + max(dp[j])，j<i 且 a[j]<a[i]
#   - O(n log n)：维护 tails 数组 + 二分查找（耐心排序）
#   - 重建方案：记录前驱下标
#   - 变体：最长非递减、最长递减、二维信封问题
#   - 与第247课二分查找、第336课双指针的联系
import bisect


def lis_n2(nums: list[int]):
    """O(n²)，返回 (长度, 一个具体序列)。"""
    n = len(nums)
    if n == 0:
        return 0, []
    dp = [1] * n
    prev = [-1] * n
    for i in range(n):
        for j in range(i):
            if nums[j] < nums[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                prev[i] = j

    best_end = max(range(n), key=lambda i: dp[i])
    length = dp[best_end]
    seq = []
    cur = best_end
    while cur != -1:
        seq.append(nums[cur])
        cur = prev[cur]
    return length, list(reversed(seq))


def lis_nlogn(nums: list[int]):
    """O(n log n)，只返回长度。tails[k] = 长度为 k+1 的递增子序列的最小结尾。"""
    tails = []
    for x in nums:
        pos = bisect.bisect_left(tails, x)     # 严格递增用 left
        if pos == len(tails):
            tails.append(x)
        else:
            tails[pos] = x
    return len(tails), tails


NUMS = [10, 9, 2, 5, 3, 7, 101, 18]
print("== 序列 ==", NUMS)
length, seq = lis_n2(NUMS)
print(f"\n== O(n²) DP ==")
print(f"  长度：{length}")
print("  一个 LIS：", seq)
print("  说明：序列不要求连续，2→3→7→101 或 2→5→7→101 都可以")

print("\n== O(n log n) 耐心排序 ==")
length2, tails = lis_nlogn(NUMS)
print(f"  长度：{length2}（与 DP 一致：{length2 == length}）")
print(f"  tails 数组：{tails}")
print("  tails 不是 LIS 本身，只是各长度的最小结尾；求具体序列要用 DP 前驱")

# ---- 逐步观察 tails 变化 ----
print("\n== tails 演变过程 ==")
tails = []
for i, x in enumerate(NUMS):
    pos = bisect.bisect_left(tails, x)
    if pos == len(tails):
        tails.append(x)
        action = "追加"
    else:
        tails[pos] = x
        action = f"替换位置 {pos}"
    print(f"  处理 {x:3d}：{action:10s} → {tails}")

# ---- 变体：最长非递减 ----
print("\n== 最长非递减（允许相等）==")
def lis_non_decreasing(nums):
    tails = []
    for x in nums:
        pos = bisect.bisect_right(tails, x)    # 用 right 允许相等
        if pos == len(tails):
            tails.append(x)
        else:
            tails[pos] = x
    return len(tails)


dup = [1, 2, 2, 2, 3]
print("  序列：", dup, "| 严格递增：", lis_nlogn(dup)[0],
      "| 非递减：", lis_non_decreasing(dup))

# ---- 变体：最长递减 ----
print("\n== 最长递减 ==")
length_dec, seq_dec = lis_n2([-x for x in NUMS])
print(f"  长度：{length_dec}，序列：{seq_dec}（取负后求 LIS）")

# ---- 二维信封问题（LIS 的应用）----
print("\n== 应用：俄罗斯套娃信封 ==")
envelopes = [(5, 4), (6, 4), (6, 7), (2, 3)]
# 宽升序、同宽时高降序 → 对高求 LIS
envelopes.sort(key=lambda e: (e[0], -e[1]))
heights = [h for _, h in envelopes]
print("  排序后：", envelopes)
print("  最多嵌套层数：", lis_nlogn(heights)[0])

# ---- 复杂度对比 ----
print("\n== 复杂度 ==")
print("  O(n²)：n=1 万 → 1 亿次操作，偏慢")
print("  O(n log n)：n=100 万也可接受")
print("  需要具体序列 → O(n²) 记录前驱最简单")
print("  只要长度 → 优先 O(n log n)")

# ===== 练习题 =====
# 1. 实现 O(n log n) 版本的“具体序列”重建（提示：记录每个位置的 pos）。
# 2. 求“最长摆动子序列”长度（上升下降交替）。
# 3. 把 LIS 用于“股票最多两次交易”？不，先做“最长递增子数组”（连续版）。
# 4. 思考：tails 数组为什么能代表“各长度的最小结尾”？
