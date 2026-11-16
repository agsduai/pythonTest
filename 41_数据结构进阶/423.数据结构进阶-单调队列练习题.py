# ===== 第423课：数据结构进阶-单调队列 =====
# 知识点：
#   - 单调队列：队内保持单调，队首就是当前窗口的最值
#   - 滑动窗口最大值：窗口右扩时入队；左边界越过时从队首淘汰
#   - 每个元素最多进出队一次 → O(n)，比每个窗口重算 O(nk) 快
#   - 与第422课单调栈同源：栈解决“找下一个更大”，队列解决“窗口内最值”
#   - 应用：滑动窗口最大值/最小值、限流统计、股票窗口指标
from collections import deque


def sliding_window_max(nums: list[int], k: int) -> list[int]:
    """返回每个长度为 k 的窗口的最大值。"""
    if k <= 0:
        raise ValueError("k 必须为正")
    dq: deque[int] = deque()        # 存下标，对应值从队首到队尾递减
    result = []
    for i, x in enumerate(nums):
        # 1) 队尾比 x 小的都淘汰：它们不可能再成为最大值
        while dq and nums[dq[-1]] <= x:
            dq.pop()
        dq.append(i)
        # 2) 队首下标滑出窗口则淘汰
        if dq[0] <= i - k:
            dq.popleft()
        # 3) 窗口形成后记录答案
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result


print("== 滑动窗口最大值 ==")
nums = [1, 3, -1, -3, 5, 3, 6, 7]
k = 3
print("  数组：", nums)
print(f"  k={k}：", sliding_window_max(nums, k))   # [3,3,5,5,6,7]

# 逐步打印，观察队列变化
print("\n== 队列变化过程 ==")
dq = deque()
for i, x in enumerate(nums):
    while dq and nums[dq[-1]] <= x:
        dq.pop()
    dq.append(i)
    if dq[0] <= i - k:
        dq.popleft()
    window = nums[max(0, i - k + 1): i + 1]
    print(f"  i={i} 窗口={window} 队列下标={list(dq)} 最大值={nums[dq[0]] if i >= k - 1 else '-'}")

# ---- 对照暴力版，验证一致性 ----
def brute(nums, k):
    return [max(nums[i:i + k]) for i in range(len(nums) - k + 1)]

import random
random.seed(1)
for _ in range(5):
    arr = [random.randint(-9, 9) for _ in range(12)]
    kk = random.randint(1, 5)
    assert sliding_window_max(arr, kk) == brute(arr, kk)
print("\n== 随机对拍 ==")
print("  5 组随机数据，单调队列与暴力结果全部一致")

# ---- 应用：限流器的“最近 1 秒请求数” ----
print("\n== 限流窗口统计 ==")
timestamps = [0.1, 0.3, 0.9, 1.05, 1.2, 1.9, 2.2]      # 秒
window = 1.0
dq = deque()
print("  时间序列：", timestamps)
for t in timestamps:
    dq.append(t)
    while dq and dq[0] < t - window:                   # 淘汰窗口外的旧请求
        dq.popleft()
    print(f"    t={t:.2f} 最近1秒请求数={len(dq)}")

# ===== 练习题 =====
# 1. 求滑动窗口最小值（把“递减队列”改成“递增队列”）。
# 2. 返回最大值对应的下标而不是值。
# 3. 用单调队列实现“窗口大小为 k 的移动平均”的分子部分。
# 4. 思考：为什么队列里存下标而不是值？和 422 课的理由一样吗？
