# ===== 第272课：性能优化-选对数据结构 =====
# 知识点：
#   - 成员判断：set/dict O(1) vs list O(n) —— 大数据量差距是数量级的
#   - 头部插删：deque O(1) vs list O(n)
#   - 选型口诀：查得多用 set/dict，头尾操作多用 deque，随机访问用 list
#   - 这是“换数据结构”级别的优化：通常比抠代码细节收益大得多

import time
from collections import deque

# ---- 成员判断：list vs set ----
data = list(range(100_000))
data_set = set(data)
target = 99_999

start = time.perf_counter()
for _ in range(1000):
    target in data
t_list = time.perf_counter() - start

start = time.perf_counter()
for _ in range(1000):
    target in data_set
t_set = time.perf_counter() - start

print(f"list 判存 1000 次：{t_list:.4f} 秒")
print(f"set  判存 1000 次：{t_set:.6f} 秒")
print(f"差距约 {t_list / max(t_set, 1e-9):.0f} 倍")

# ---- 头部插入：list vs deque ----
N = 20_000

start = time.perf_counter()
lst = []
for i in range(N):
    lst.insert(0, i)
t_list_ins = time.perf_counter() - start

start = time.perf_counter()
dq = deque()
for i in range(N):
    dq.appendleft(i)
t_deque = time.perf_counter() - start

print(f"list 头插 {N} 次：{t_list_ins:.3f} 秒")
print(f"deque 头插 {N} 次：{t_deque:.6f} 秒")

# ---- 常见选型对照 ----
# dict/set   ：去重、判存、映射查找
# deque      ：队列、滑动窗口、两端进出
# list       ：按下标访问、尾部追加
# heap       （heapq）：只要“当前最大/最小”
import heapq

nums = [5, 1, 8, 3, 9, 2]
print("最大3个：", heapq.nlargest(3, nums), "最小2个：", heapq.nsmallest(2, nums))

# ===== 练习题 =====
# 1. 把第253课的 has_duplicate 改用 set 实现，再用第271课剖析对比。
# 2. 构造“频繁在头部取出任务”的场景，对比 list.pop(0) 与 deque.popleft。
# 3. 思考：什么情况下 list 反而比 set 快？（提示：数据量小、或按下标访问）
