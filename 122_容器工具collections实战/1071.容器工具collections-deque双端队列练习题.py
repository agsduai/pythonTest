# ===== 第1071课：容器工具collections-deque双端队列 =====
# 知识点：
#   - deque：两端都能进出队的列表，appendleft / popleft 操作左端
#   - 头部插入删除 O(1)，列表的 insert(0) / pop(0) 是 O(n)，量大时 deque 快得多
#   - maxlen=上限：满了自动挤掉旧数据，天然适合"最近 N 条"记录
#   - 实际场景：浏览历史、消息队列、滑动窗口、排队叫号

# 案例一：排队叫号
from collections import deque

queue = deque(["1号", "2号", "3号"])
queue.append("4号")          # 新客人排到队尾
print(f"当前队列：{list(queue)}")
served = queue.popleft()     # 队首叫号
print(f"叫号：{served}，剩余：{list(queue)}")

# 案例二：浏览器历史 —— 最近访问记录
history = deque(maxlen=5)  # 只保留最近 5 条
for page in ["首页", "商品页", "详情页", "购物车", "支付页", "完成页"]:
    history.append(page)
print(f"历史记录（最多 5 条）：{list(history)}")  # 最早的"首页"被挤掉了

# 案例三：左端操作 —— 撤销功能
# 场景：编辑器撤销，最后做的最先撤销
actions = deque()
actions.append("输入A")
actions.append("输入B")
actions.append("删除C")
print(f"撤销：{actions.pop()}")   # 从右端取最近动作
print(f"撤销：{actions.pop()}")
print(f"剩余操作：{list(actions)}")

# 案例四：性能对比 —— 头部插入
# 小量数据看不出差别，10 万次就很明显
import time

N = 50_000
start = time.time()
d = deque()
for i in range(N):
    d.appendleft(i)  # 左端插入，O(1)
print(f"deque 头插 {N} 次：{time.time() - start:.3f} 秒")

start = time.time()
lst = []
for i in range(N):
    lst.insert(0, i)  # 头插，O(n) 每次都要挪动全部元素
print(f"list 头插 {N} 次：{time.time() - start:.3f} 秒（慢很多）")

# 案例五：rotate 轮转
# 场景：值日表轮换
duty = deque(["周一组", "周二组", "周三组"])
duty.rotate(1)  # 整体右移一位
print(f"轮换后：{list(duty)}")

# ===== 练习题 =====
# 1. 用 deque 模拟打印队列：3 个任务进队，依次 popleft 处理并打印"处理任务x"。
# 2. 用 deque(maxlen=3) 记录最近 3 次搜索词（依次输入 5 个），打印最终保留的 3 个。
# 3. 用 rotate 写"击鼓传花"：8 个人围成一圈，轮转 3 次后打印"花落在谁手里"（取队首）。
