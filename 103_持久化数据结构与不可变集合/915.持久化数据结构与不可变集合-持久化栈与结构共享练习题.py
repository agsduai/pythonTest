# ===== 第915课：持久化数据结构与不可变集合-持久化栈与结构共享 =====
# 知识点：
#   - 持久化数据结构：更新返回「新版本」，旧版本依然完整可用
#   - 核心机制 = 结构共享：新旧版本共享未变化部分，只复制被改的路径
#   - 持久化栈（不可变链表）：push/pop 全是 O(1)，天然支持时间旅行
#   - 与可变结构对比：list.copy() 每次 O(n)；持久化版本任何快照 O(1)
#   - 应用：撤销/重做、多版本共存、函数式编程、无锁并发
# 依赖：无（标准库）
import time


class PStack:
    """持久化栈（不可变链表）。节点 = 值 + 指向前一版本的引用。"""

    def __init__(self, head=None, rest=None):
        self._head = head
        self._rest = rest

    def push(self, value):
        return PStack(value, self)             # O(1)：只造一个新节点

    def pop(self):
        """返回 (栈顶值, 弹出后的栈)。旧栈不受影响。"""
        if self.is_empty():
            raise IndexError("pop from empty persistent stack")
        return self._head, self._rest

    def peek(self):
        if self.is_empty():
            raise IndexError("peek from empty persistent stack")
        return self._head

    def is_empty(self):
        return self._head is None

    def size(self):
        n = 0
        cur = self
        while not cur.is_empty():
            n += 1
            cur = cur._rest
        return n

    def to_list(self):
        out = []
        cur = self
        while not cur.is_empty():
            out.append(cur._head)
            cur = cur._rest
        return list(reversed(out))


def collect_nodes(*stacks):
    """统计一组栈实际占用的节点总数（按 id 去重）。"""
    ids = set()
    for st in stacks:
        cur = st
        while not cur.is_empty():
            ids.add(id(cur))
            cur = cur._rest
    return len(ids)


print("== 基本操作 ==")
s0 = PStack()                                  # 空栈
s1 = s0.push(1)
s2 = s1.push(2)
s3 = s2.push(3)
print(f"  s3 内容 = {s3.to_list()}  (大小 {s3.size()})")
top, s2_again = s3.pop()
print(f"  pop(s3) -> 值 {top}, 余栈 {s2_again.to_list()}")
print(f"  s2 仍是原版本: {s2.to_list()}  （旧版本完整保留 —— 时间旅行）")
print(f"  s2_again 与最初 s2 是同一个对象: {s2_again is s2}（结构共享）")

print("\n== 分叉：两个未来共享同一个过去 ==")
sA = s3.push("A")
sB = s3.push("B")
print(f"  从 s3 分叉: sA = {sA.to_list()}")
print(f"             sB = {sB.to_list()}")
total = collect_nodes(sA, sB)
naive = sA.size() + sB.size()
print(f"  两栈节点总长 {naive}，实际占用 {total} 个节点"
      f"（共享率 {(naive - total) / naive:.0%}）")
print("  朴素复制要 2×6 个节点；结构共享只要 8 个（6 个公共 + 2 个分叉）")

print("\n== 快照成本：O(1) vs O(n) ==")
N = 2000
lst = list(range(N))
t0 = time.perf_counter()
snapshots = []
for _ in range(300):
    snapshots.append(lst.copy())               # 可变结构：每次快照 O(n)
t_copy = time.perf_counter() - t0

st = PStack()
for v in range(N):
    st = st.push(v)
t0 = time.perf_counter()
pers_snapshots = []
cur = st
for _ in range(300):
    pers_snapshots.append(cur)                 # 持久化：快照 = 存个引用
    cur = cur.pop()[1]
t_pers = time.perf_counter() - t0
print(f"  可变列表 300 次快照（每次 copy）: {t_copy * 1000:.2f} ms")
print(f"  持久化栈 300 次快照（引用即可）: {t_pers * 1000:.2f} ms")
print(f"  两种方式都保存了 {len(snapshots)} 个完整快照 —— 成本差一个数量级")

print("\n== 撤销/重做雏形 ==")
undo_stack = PStack()
current = ""
for ch in "你好":
    undo_stack = undo_stack.push(current)      # 每次修改前存快照
    current += ch
print(f"  输入 '你好' 后文本 = {current!r}")
prev, undo_stack = undo_stack.pop()            # 撤销：弹出的正是上一版快照
current = prev
print(f"  撤销一步: 文本 = {current!r}")
redo_stack = PStack()
redo_stack = redo_stack.push("你好")
current = redo_stack.peek()
print(f"  重做: 文本 = {current!r}（撤销栈/重做栈都是持久化栈）")

print("\n== 不可变带来的并发安全 ==")
for line in (
    "  可变结构 + 多线程 = 加锁或者复制（成本高）",
    "  不可变结构 = 任何线程拿到快照后永远不会『被人改掉』",
    "  读读/读写之间天然无竞争 —— 这就是函数式语言的核心数据结构",
    "  Python 的 tuple/frozenset 也是持久化思想的最小应用",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  持久化 = 更新造新版本 + 旧版本活着 + 未变部分共享",
    "  持久化栈是最低门槛的入门：一个节点类就够",
    "  快照 O(1) 让撤销/时间旅行从『昂贵的功能』变成『免费的副产品』",
    "  916 课：栈太简单，接下来是真正的主力 —— 持久化映射（HAMT）",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 用两个持久化栈实现持久化队列（入队 push 一栈、出队弹另一栈并倒腾）。
# 2. 测量 100 条分叉时间线的结构共享率，画出「分支数-共享率」曲线。
# 3. 给 PStack 加 __iter__ 与 __repr__，验证 to_list 与迭代顺序一致。
# 4. 思考：为什么不可变结构在函数式语言里是默认选择？命令式代码里哪些
#    场景会因「旧值被悄悄改掉」而出 bug？
