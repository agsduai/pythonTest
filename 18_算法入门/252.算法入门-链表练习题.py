# ===== 第252课：算法入门-链表 =====
# 知识点：
#   - 链表：节点(Node) + next 指针串联；头指针是唯一入口
#   - 优势：头插/删除 O(1)；劣势：随机访问 O(n)，只能顺着爬
#   - 对比 list：随机访问 O(1)，但头插要整体搬移 O(n)
#   - 遍历套路：cur = head; while cur: ...; cur = cur.next


class Node:
    def __init__(self, value, next=None):
        self.value = value
        self.next = next


class LinkedList:
    def __init__(self):
        self.head = None

    def append(self, value):
        """尾插：爬到末尾再接上，O(n)。"""
        node = Node(value)
        if self.head is None:
            self.head = node
            return
        cur = self.head
        while cur.next:
            cur = cur.next
        cur.next = node

    def find(self, value):
        cur, idx = self.head, 0
        while cur:
            if cur.value == value:
                return idx
            cur, idx = cur.next, idx + 1
        return -1

    def remove(self, value):
        if self.head is None:
            return False
        if self.head.value == value:        # 特殊情况：删头节点
            self.head = self.head.next
            return True
        prev, cur = self.head, self.head.next
        while cur:
            if cur.value == value:
                prev.next = cur.next        # 前一个直接跳过当前
                return True
            prev, cur = cur, cur.next
        return False

    def __iter__(self):
        cur = self.head
        while cur:
            yield cur.value
            cur = cur.next

    def __len__(self):
        return sum(1 for _ in self)


linked = LinkedList()
for x in (10, 20, 30, 40):
    linked.append(x)
print(list(linked), "长度", len(linked))
print("查找 30 的下标：", linked.find(30))
linked.remove(20)
print("删除 20 后：", list(linked))
print("删除不存在的 99：", linked.remove(99))

# 性能对比：头插 2 万个元素
import time

N = 20_000

start = time.perf_counter()
head = None
for i in range(N):
    head = Node(i, head)          # 链表头插 O(1)
print(f"链表头插 {N} 个：{time.perf_counter() - start:.3f} 秒")

start = time.perf_counter()
lst = []
for i in range(N):
    lst.insert(0, i)              # list 头插 O(n)，整体搬移
print(f"list 头插 {N} 个：{time.perf_counter() - start:.3f} 秒")

# ===== 练习题 =====
# 1. 给 LinkedList 增加 insert_head(value)：头插 O(1)。
# 2. 实现 reverse()：原地反转链表（提示：三指针 prev/cur/next）。
# 3. 用 100000 个元素对比头插性能，体会差距如何被拉大。
# 4. 思考：为什么 Python 没有内置链表，实际项目里 deque 够用吗？
