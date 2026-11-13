# ===== 第251课：算法入门-队列与双端队列 =====
# 知识点：
#   - 队列：先进先出 FIFO，排队、任务调度、广度优先搜索的基础
#   - deque 双端队列：两端增删 O(1)，可当栈也可当队列（复习第229课）
#   - deque(maxlen=n)：固定容量滑动窗口
#   - 经典小游戏：热土豆（约瑟夫问题简化版）

from collections import deque


class Queue:
    """用 deque 封装的先进先出队列。"""

    def __init__(self):
        self._items = deque()

    def enqueue(self, item):
        self._items.append(item)        # 队尾进

    def dequeue(self):
        if not self._items:
            raise IndexError("队列为空")
        return self._items.popleft()    # 队头出

    def __len__(self):
        return len(self._items)


q = Queue()
for name in ("任务A", "任务B", "任务C"):
    q.enqueue(name)
while len(q):
    print("处理：", q.dequeue())

# 打印队列模拟（先提交的先打印）
print_queue = deque()
for job in ("文档1", "图片2", "合同3"):
    print_queue.append(job)
print(print_queue.popleft(), "打印中...")

# 双端队列：两端都能进出
d = deque([1, 2, 3])
d.append(4)
d.appendleft(0)
print(d)
print(d.pop(), d.popleft(), d)

# 滑动窗口：传感器只保留最近 3 条
window = deque(maxlen=3)
for sensor in (23.1, 23.4, 23.8, 24.2, 25.0):
    window.append(sensor)
    print("最近3条：", list(window))

# 热土豆游戏：传一圈，拿到土豆的人出列
players = deque(["小明", "小红", "小刚", "小丽"])
while len(players) > 1:
    players.append(players.popleft())   # 传一圈
    out = players.popleft()             # 出列
    print(f"{out} 出列，剩余：{list(players)}")
print("最后留下：", players[0])

# ===== 练习题 =====
# 1. 用 Queue 实现“客服排队”：3 个来电、2 个客服依次接听。
# 2. 用 deque(maxlen=2) 模拟浏览器“后退按钮”可回退的最近 2 个页面。
# 3. 修改热土豆规则：传 2 圈再出列，结果有什么变化？
# 4. 思考：队列和栈分别对应生活中的什么场景？
