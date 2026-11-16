# ===== 第422课：数据结构进阶-单调栈 =====
# 知识点：
#   - 单调栈：栈内元素保持单调（递增/递减），用于找“左/右第一个更大/更小”
#   - 每个元素最多入栈出栈一次 → O(n)，比双重循环 O(n²) 快
#   - 经典三题：下一个更大元素、每日温度、柱状图最大矩形
#   - 与第250课栈的关系：普通栈存值，单调栈“带着淘汰规则”存下标
#   - 应用：股票跨度、接雨水、最大矩形、直方图


def next_greater(nums: list[int]) -> list[int]:
    """每个位置右边第一个更大的数，没有则 -1。"""
    result = [-1] * len(nums)
    stack: list[int] = []                 # 存下标，栈内对应值递减
    for i, x in enumerate(nums):
        while stack and nums[stack[-1]] < x:
            j = stack.pop()
            result[j] = x                 # x 就是 j 右边第一个更大值
        stack.append(i)
    return result


print("== 下一个更大元素 ==")
nums = [2, 1, 2, 4, 3]
print("  数组：", nums)
print("  结果：", next_greater(nums))     # [4,2,4,-1,-1]


def daily_temperatures(temps: list[int]) -> list[int]:
    """经典题：还要等几天才升温。"""
    answer = [0] * len(temps)
    stack: list[int] = []
    for i, t in enumerate(temps):
        while stack and temps[stack[-1]] < t:
            j = stack.pop()
            answer[j] = i - j
        stack.append(i)
    return answer


print("\n== 每日温度 ==")
temps = [73, 74, 75, 71, 69, 72, 76, 73]
print("  温度：", temps)
print("  等待：", daily_temperatures(temps))   # [1,1,4,2,1,1,0,0]


def largest_rectangle(heights: list[int]) -> int:
    """柱状图最大矩形：左右各找第一个更矮的柱子。"""
    stack: list[int] = []                 # 递增栈，存下标
    best = 0
    for i, h in enumerate(heights + [0]):  # 末尾补 0，强制清空栈
        while stack and heights[stack[-1]] > h:
            height = heights[stack.pop()]
            left = stack[-1] if stack else -1
            width = i - left - 1
            best = max(best, height * width)
        stack.append(i)
    return best


print("\n== 柱状图最大矩形 ==")
for h in ([2, 1, 5, 6, 2, 3], [2, 4], [1, 1, 1]):
    print(f"  {h} → 最大面积 {largest_rectangle(h)}")

# ---- 对照：双重循环 O(n²) 版，验证结果一致 ----
def largest_rectangle_brute(heights):
    best = 0
    for i in range(len(heights)):
        min_h = heights[i]
        for j in range(i, len(heights)):
            min_h = min(min_h, heights[j])
            best = max(best, min_h * (j - i + 1))
    return best


print("\n== 单调栈 vs 暴力 ==")
data = [2, 1, 5, 6, 2, 3, 4, 7, 1]
print("  单调栈：", largest_rectangle(data), "| 暴力：", largest_rectangle_brute(data))
print("  小数据无感，10 万根柱子时 O(n) 与 O(n²) 差几个数量级")

# ---- 思维模板 ----
#   for i, x in enumerate(nums):
#       while stack and 破坏单调性的条件:
#           j = stack.pop()      # j 的答案就是 i
#       stack.append(i)
# 把“条件”和“出栈时记录什么”换掉，就能套出很多题。

# ===== 练习题 =====
# 1. 求“下一个更小元素”（把比较符号翻转）。
# 2. 用单调栈求“接雨水”的最大储水量。
# 3. 给每日温度加返回“具体升温到多少度”。
# 4. 思考：为什么栈里存下标而不是值？（提示：需要算距离/宽度）
