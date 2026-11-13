# ===== 第334课：算法进阶-贪心算法 =====
# 知识点：
#   - 贪心：每一步都选“眼前最优”，期望整体最优
#   - 成立前提：问题具有“贪心选择性质”（能证明局部最优连成全局最优）
#   - 经典1：区间调度 —— 按结束时间排序，能选就选
#   - 经典2：标准币制找零；注意任意币制下贪心可能翻车（对照第255课 DP）
# 依赖：无

# ---- 经典1：最多不重叠区间（会议室安排）----
def max_meetings(intervals):
    """按结束时间排序：结束越早，给后面留的空间越大。"""
    intervals = sorted(intervals, key=lambda x: x[1])
    count, last_end = 0, float("-inf")
    for start, end in intervals:
        if start >= last_end:
            count += 1
            last_end = end
    return count


print("最多会议数：", max_meetings([(1, 3), (2, 4), (3, 5), (0, 7), (5, 9), (8, 10)]))

# ---- 经典2：找零（标准币制）----
def make_change(amount, coins=(50, 20, 10, 5, 1)):
    result = {}
    for c in coins:
        if amount >= c:
            result[c], amount = divmod(amount, c)     # 张数与余额一步到位
    return result


print("找零 86 元：", make_change(86))

# ---- 反例：贪心翻车 ----
def greedy_coins(amount, coins):
    count = 0
    for c in sorted(coins, reverse=True):
        count += amount // c
        amount %= c
    return count


print("币制 [1,5,11] 凑 15：贪心 =", greedy_coins(15, [1, 5, 11]), "（5+5+5=3 枚才是最优）")

# ---- 贪心成立的直觉 ----
# 排序依据（结束时间 / 单位价值）就是“贪心策略”；
# 说不清为什么局部最优能推出全局最优时，先怀疑贪心，考虑 DP。

# ===== 练习题 =====
# 1. 区间调度升级：输出“被选中的会议列表”而不只是数量。
# 2. 设计一个贪心会翻车的币制（提示：[1, 3, 4] 凑 6）。
# 3. 用第255课的 coin_change 验证反例，对比两种思路。
