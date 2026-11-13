# ===== 第331课：算法进阶-堆与heapq =====
# 知识点：
#   - 堆：能 O(log n) 取“最值”的完全二叉树；heapq 是小顶堆
#   - heappush/heappop/heapify/nlargest/nsmallest
#   - TopK 经典：维护 k 大小的堆，流式找最大的 k 个
#   - 优先级队列：元组 (优先级, 任务)，值小的先出
# 依赖：无（标准库 heapq）

import heapq

# ---- 基本用法 ----
nums = [5, 1, 8, 3, 9, 2]
h = nums[:]
heapq.heapify(h)                     # 原地建堆 O(n)
print("堆顶（最小）：", h[0])
print("连续弹出（自动有序）：", [heapq.heappop(h) for _ in range(3)])

# ---- TopK：流式数据里找最大的 k 个 ----
def top_k(items, k):
    """只维护 k 个元素的小顶堆，内存 O(k)。"""
    heap = []
    for x in items:
        heapq.heappush(heap, x)
        if len(heap) > k:
            heapq.heappop(heap)      # 挤掉最小的
    return sorted(heap, reverse=True)


print("Top3：", top_k([4, 1, 7, 3, 8, 5, 9, 2], 3))
print("内置工具：", heapq.nlargest(3, [4, 1, 7, 3, 8]), heapq.nsmallest(2, [4, 1, 7, 3, 8]))

# ---- 优先级队列：紧急的先处理 ----
tasks = [(2, "写周报"), (1, "处理线上告警"), (3, "看文档"), (1, "回复客户")]
heapq.heapify(tasks)
while tasks:
    priority, name = heapq.heappop(tasks)
    print(f"  执行 P{priority}：{name}")

# ---- 与排序的对比：数据流场景堆完胜 ----
# 数据一次性给全 → sorted 够用；数据一条条到达 → 堆不需要重排全部

# ===== 练习题 =====
# 1. 用堆实现“实时中位数”的简化版：维护两个堆（进阶挑战）。
# 2. 让优先级队列支持“同级任务按提交顺序出队”（提示：加自增序号进元组）。
# 3. 思考：为什么 TopK 用小顶堆而不是大顶堆？
