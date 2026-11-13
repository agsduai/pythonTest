# ===== 第255课：算法入门-动态规划入门 =====
# 知识点：
#   - 动态规划 DP：大问题拆成小问题，并“记住”小问题的答案
#   - 适用信号：重叠子问题 + 最优子结构
#   - 两条路线：自顶向下（递归+备忘录）、自底向上（迭代填表）
#   - 入门三题：爬楼梯、最大子数组和、零钱兑换

import functools

# 题1：爬楼梯 —— 每次上 1 或 2 阶，n 阶有几种走法（就是斐波那契）


@functools.lru_cache(maxsize=None)
def climb_memo(n):
    """自顶向下：递归 + 备忘录。"""
    if n <= 2:
        return n
    return climb_memo(n - 1) + climb_memo(n - 2)


def climb_table(n):
    """自底向上：迭代填表，O(n) 时间 O(1) 空间。"""
    if n <= 2:
        return n
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b          # 滚动前进，只保留最近两个状态
    return b


print([climb_memo(i) for i in range(1, 8)])
print([climb_table(i) for i in range(1, 8)])
print("climb_table(50) =", climb_table(50))


# 题2：最大子数组和 —— Kadane 算法
def max_subarray(nums):
    best = cur = nums[0]
    for x in nums[1:]:
        cur = max(x, cur + x)    # 要么接上前面的，要么从自己重新开始
        best = max(best, cur)
    return best


print(max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]))   # 6 → [4,-1,2,1]


# 题3：零钱兑换 —— 最少几枚硬币凑出金额
def coin_change(coins, amount):
    INF = float("inf")
    dp = [0] + [INF] * amount       # dp[i] = 凑出 i 元的最少硬币数
    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i and dp[i - coin] + 1 < dp[i]:
                dp[i] = dp[i - coin] + 1
    return dp[amount] if dp[amount] != INF else -1


print(coin_change([1, 5, 11], 15))     # 3 → 5+5+5
print(coin_change([1, 5, 11], 9))      # 5 → 5+1+1+1+1
print(coin_change([2], 3))             # -1 → 凑不出来

# DP 三步曲总结：
#   ①定义状态：dp[i] 表示什么？②转移方程：dp[i] 怎么由更小的 dp 得到？③边界与顺序

# ===== 练习题 =====
# 1. 把 climb_table 改成“每次可上 1/2/3 阶”的版本。
# 2. 修改 max_subarray，让它同时返回最大的那个子数组本身。
# 3. 零钱兑换扩展：增加一个函数返回“具体用了哪些硬币”。
# 4. 思考：斐波那契朴素递归、lru_cache 版、滚动变量版，各是什么思路？
