# ===== 第963课：内存管理与垃圾回收-对象图与根集 =====
# 知识点：
#   - 垃圾回收的第一问：『谁是垃圾？』—— 不可达对象
#   - 对象图：节点 = 对象，边 = 引用；根集 = 全局变量/栈帧/寄存器
#   - 可达性：从根集沿引用遍历，到不了的就是垃圾 —— 与图遍历（459 课）同源
#   - 分配侧：从空闲空间拿内存（863 课伙伴系统）—— 两章在此会合
#   - 保留 vs 回收的判定标准不同：引用计数看『没人用』，追踪 GC 看『不可达』
# 依赖：无（标准库）


class SimObject:
    """模拟堆上的对象：id + 大小 + 引用列表。"""

    _next_id = [0]

    def __init__(self, size, refs=(), label=""):
        SimObject._next_id[0] += 1
        self.oid = SimObject._next_id[0]
        self.size = size
        self.refs = list(refs)              # 引用的对象 id 列表
        self.label = label
        self.reachable = None               # 由 GC 填写

    def __repr__(self):
        return f"obj{self.oid}({self.label},{self.size}B)"


class Heap:
    """模拟堆：分配/释放/对象图。"""

    def __init__(self):
        self.objects = {}                   # oid -> SimObject
        self.free_bytes = 100000            # 剩余堆空间
        self.total_bytes = 100000

    def alloc(self, size, refs=(), label=""):
        if size > self.free_bytes:
            raise MemoryError("堆空间不足（需要 GC）")
        obj = SimObject(size, refs, label)
        self.objects[obj.oid] = obj
        self.free_bytes -= size
        return obj

    def object_graph(self):
        """对象引用图：{oid: [引用的 oid]}。"""
        return {oid: [r for r in obj.refs if r in self.objects]
                for oid, obj in self.objects.items()}

    def reachable_from(self, roots):
        """从根集出发的可达集合（BFS）。"""
        seen = set()
        queue = deque(roots)
        while queue:
            oid = queue.popleft()
            if oid in seen or oid not in self.objects:
                continue
            seen.add(oid)
            queue.extend(self.objects[oid].refs)
        return seen

    def garbage(self, roots):
        reachable = self.reachable_from(roots)
        return {oid for oid in self.objects if oid not in reachable}, reachable


from collections import deque


print("== 构造对象图 ==")
heap = Heap()
a = heap.alloc(100, label="全局配置")
b = heap.alloc(200, refs=[a.oid], label="会话")
c = heap.alloc(300, refs=[b.oid, a.oid], label="请求上下文")
d = heap.alloc(50, refs=[c.oid], label="临时计算")      # 会被 c 引用
e = heap.alloc(400, label="孤儿对象")                    # 没人引用！
f = heap.alloc(60, refs=[e.oid], label="孤儿子对象")     # 只被孤儿引用
print(f"  分配 {len(heap.objects)} 个对象，堆使用 "
      f"{heap.total_bytes - heap.free_bytes}B / {heap.total_bytes}B")

print("\n== 对象图 ==")
for oid, obj in sorted(heap.objects.items()):
    print(f"  obj{oid}({obj.label}) -> {obj.refs or '无'}")

print("\n== 根集判定 ==")
roots = [a.oid, c.oid]                          # 全局变量指向 a 与 c
garbage, reachable = heap.garbage(roots)
print(f"  根集 = {roots}")
print(f"  可达对象 = {sorted(reachable)}")
print(f"  垃圾对象 = {sorted(garbage)}")
for oid in sorted(garbage):
    print(f"    垃圾: {heap.objects[oid]}")
print("  f 被 e 引用，但 e 不可达 → 『传递性不可达』—— 引用链是活的关键")

print("\n== 根集的构成 ==")
for line in (
    "  栈帧：当前函数的局部变量与参数",
    "  全局：模块级变量、静态字段",
    "  寄存器：CPU 寄存器暂存的引用",
    "  特殊：线程栈（每线程一个根集）、外部句柄表",
):
    print("  -", line)

print("\n== 两种判定哲学 ==")
print(f"  {'策略':<12}{'判据':<26}{'优点':<20}{'致命伤'}")
for row in (("引用计数", "引用数归零立即回收", "实时/局部性好", "循环引用泄漏"),
            ("追踪 GC", "从根集不可达即垃圾", "处理循环引用", "全局暂停(STW)")):
    print(f"  {row[0]:<12}{row[1]:<26}{row[2]:<20}{row[3]}")
print("  CPython：引用计数为主 + 分代追踪为辅；JVM/Go：纯追踪")

print("\n== 小结 ==")
for line in (
    "  垃圾 = 从根集不可达的对象 —— 定义对了，算法只是遍历",
    "  传递性：引用垃圾的对象也跟着变垃圾",
    "  863 课的分配器 + 本章的回收器 = 完整的运行时内存子系统",
    "  964 课：引用计数 —— 最简单也最经典的回收算法",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「释放垃圾」：把不可达对象移出堆并归还空间，验证 free_bytes 恢复。
# 2. 构造『引用自环』：a→b→a 且两者都不可达，验证追踪 GC 能回收而引用计数
#    不能（为 964 课埋伏笔）。
# 3. 实现『弱引用』：不参与可达性的引用，观察弱引用对象被回收后的行为。
# 4. 思考：为什么 GC 需要『至少和堆一样大的暂停』？增量式 GC（968 课）如何
#    把大暂停切成小块？
