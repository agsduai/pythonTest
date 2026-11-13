# ===== 第229课：常用标准库-collections-deque与namedtuple =====
# 知识点：
#   - deque 双端队列：两端增删都是 O(1)（list 头部插入是 O(n)）
#   - deque(maxlen=n)：固定容量，自动淘汰旧数据，滑动窗口神器
#   - namedtuple：给元组字段命名，比下标访问可读性强得多

from collections import deque, namedtuple

# deque 基本操作
q = deque([1, 2, 3], maxlen=5)
q.append(4)            # 右端入队
q.appendleft(0)        # 左端入队
print(q)               # deque([0, 1, 2, 3, 4])
q.pop()                # 右端出队
q.popleft()            # 左端出队
print(q)

# 用 deque(maxlen) 实现滑动窗口：只保留最近 3 条
window = deque(maxlen=3)
for x in (10, 20, 30, 40, 50):
    window.append(x)
    print("窗口：", list(window))

# namedtuple：给元组的每个位置起名字
Point = namedtuple("Point", ["x", "y"])
p = Point(3, 4)
print(p.x, p.y)
print(p._asdict())
print(p == Point(3, 4))

User = namedtuple("User", "name age city")     # 空格分隔字符串也可以
u = User("小明", 15, "北京")
print(u.name, u.city)

# namedtuple 仍然是元组：可以下标、解包
name, age, city = u
print(name, age, city)

# ===== 练习题 =====
# 1. 用 deque 实现“最近 5 个操作的历史记录”，超出自动淘汰最旧的。
# 2. 用 deque 写一个简易任务队列：交替执行“入队、出队”直到空。
# 3. 定义 namedtuple Order（商品、数量、单价），写函数计算订单总价。
# 4. 思考：什么时候用 namedtuple，什么时候直接定义 class？
