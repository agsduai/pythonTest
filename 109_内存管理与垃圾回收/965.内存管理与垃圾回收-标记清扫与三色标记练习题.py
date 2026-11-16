# ===== 第965课：内存管理与垃圾回收-标记清扫与三色标记 =====
# 知识点：
#   - 标记-清扫（Mark-Sweep）两阶段：标记可达对象 → 清扫不可达对象
#   - 三色抽象：白（未访）→ 灰（已访未扫子节点）→ 黑（完整处理）
#   - 标记阶段 = 从根集开始的 BFS/DFS 着色；清扫 = 遍历堆回收白色
#   - 暂停时间与堆大小成正比：标记必须扫全部活对象
#   - 三色不变式是增量式 GC（968 课）的理论基础
# 依赖：无（标准库）
from collections import deque


class GCObject:
    __slots__ = ("oid", "size", "refs", "color", "label")

    _next = [0]

    def __init__(self, refs=(), label=""):
        GCObject._next[0] += 1
        self.oid = GCObject._next[0]
        self.size = 50 + self.oid * 7
        self.refs = [r.oid for r in refs]
        self.color = "white"
        self.label = label


class MarkSweepGC:
    def __init__(self, heap_size=10000):
        self.heap_size = heap_size
        self.used = 0
        self.objects = {}                    # oid -> GCObject
        self.sweep_count = 0

    def alloc(self, label, refs=()):
        obj = GCObject(refs, label)
        if self.used + obj.size > self.heap_size:
            self.collect(roots=self.live_roots())
            if self.used + obj.size > self.heap_size:
                raise MemoryError("GC 后仍不足")
        self.objects[obj.oid] = obj
        self.used += obj.size
        return obj

    def live_roots(self):
        """简化：登记在 roots 集合的对象为根。"""
        return [oid for oid, obj in self.objects.items()
                if obj.label.startswith("root")]

    def mark(self, roots):
        """标记阶段：三色 BFS。"""
        for obj in self.objects.values():
            obj.color = "white"
        gray = deque()
        for r in roots:
            if r in self.objects and self.objects[r].color == "white":
                self.objects[r].color = "gray"
                gray.append(r)
        mark_order = []
        while gray:
            oid = gray.popleft()
            obj = self.objects[oid]
            obj.color = "black"
            mark_order.append(oid)
            for ref in obj.refs:
                child = self.objects.get(ref)
                if child and child.color == "white":
                    child.color = "gray"
                    gray.append(ref)
        return mark_order

    def sweep(self):
        """清扫阶段：回收所有白色对象。"""
        freed = []
        for oid in list(self.objects):
            obj = self.objects[oid]
            if obj.color == "white":
                freed.append(obj)
                self.used -= obj.size
                del self.objects[oid]
        self.sweep_count += 1
        return freed

    def collect(self, roots):
        order = self.mark(roots)
        freed = self.sweep()
        return order, freed

    def live_roots(self):
        return []


print("== 构造对象图 ==")
gc = MarkSweepGC(heap_size=10000)
root1 = GCObject(label="root:全局缓存")
gc.objects[root1.oid] = root1
gc.used += root1.size
child1 = GCObject(label="子对象1")
child2 = GCObject(label="子对象2")
orphan = GCObject(label="孤儿")
gc.objects[child1.oid] = child1; gc.used += child1.size
gc.objects[child2.oid] = child2; gc.used += child2.size
gc.objects[orphan.oid] = orphan; gc.used += orphan.size
root1.refs = [child1.oid, child2.oid]
child1.refs = [child2.oid]
print(f"  root1 → {child1.oid}, {child2.oid}；child1 → child2；orphan 不可达")

print("\n== 标记阶段：三色演化 ==")
roots = [root1.oid]
for obj in gc.objects.values():
    obj.color = "white"
gray = deque([root1.oid])
root1.color = "gray"
step = 0
while gray:
    step += 1
    oid = gray.popleft()
    obj = gc.objects[oid]
    obj.color = "black"
    for ref in obj.refs:
        child = gc.objects.get(ref)
        if child and child.color == "white":
            child.color = "gray"
            gray.append(ref)
    print(f"  步{step}: {obj.label} 白→黑, 灰色队列 = {list(gray)}")
colors = {o.label: o.color for o in gc.objects.values()}
print(f"  最终着色: {colors}")
print("  黑色 = 确认存活；白色 = 候选垃圾；灰色 = 待处理边界")

print("\n== 清扫阶段 ==")
freed = [obj for obj in gc.objects.values() if obj.color == "white"]
for obj in freed:
    print(f"  回收 {obj.label}（{obj.size}B）")
    del gc.objects[obj.oid]
    gc.used -= obj.size
print(f"  回收 {len(freed)} 个对象 / {sum(o.size for o in freed)}B，"
      f"剩余使用 {gc.used}B")

print("\n== 完整 GC 周期（分配压力触发）==")
gc2 = MarkSweepGC(heap_size=3000)
gc2.roots_ref = []
root_obj = GCObject(label="root:main")
gc2.objects[root_obj.oid] = root_obj
gc2.used += root_obj.size
gc2.live_roots = lambda: [root_obj.oid] + gc2.roots_ref
alloc_log = []
for i in range(60):
    label = "root" if i % 10 == 0 else f"临时{i}"
    refs = [root_obj] if i % 10 == 0 else []
    try:
        obj = gc2.alloc(label, refs)
        if label.startswith("root"):
            gc2.roots_ref.append(obj.oid)
        alloc_log.append(f"分配 {label}")
    except MemoryError:
        freed_n = len(gc2.collect(gc2.live_roots())[1])
        alloc_log.append(f"GC 触发: 回收 {freed_n} 个")
        obj = gc2.alloc(label, refs)
        if label.startswith("root"):
            gc2.roots_ref.append(obj.oid)
print(f"  60 次分配中的 GC 触发: {sum(1 for a in alloc_log if 'GC' in a)} 次")
print(f"  最终堆使用 = {gc2.used}B / {gc2.heap_size}B")

print("\n== 三色不变式（968 课的基础）==")
for line in (
    "  强不变式：不存在黑→白 的引用边",
    "  若破坏（黑对象新增白引用且灰色未扫到）→ 活对象被误回收!",
    "  解决：写屏障（赋值时把新引用的目标重新着灰）",
    "  增量 GC 就是在『维持不变式』的前提下分步标记",
):
    print("  -", line)

print("\n== 标记-清扫的暂停分析 ==")
print(f"  {'阶段':<10}{'耗时来源':<26}{'与什么成正比'}")
for row in (("标记", "遍历全部活对象", "活对象数量 × 指针数"),
            ("清扫", "遍历整个堆", "堆总大小"),
            ("合计", "一次 STW 暂停", "堆越大暂停越长")):
    print(f"  {row[0]:<10}{row[1]:<26}{row[2]}")
print("  Go 的解决方案：并发标记 + 增量清扫（968 课）")

print("\n== 小结 ==")
for line in (
    "  标记-清扫 = 可达性判定（标记）+ 空间回收（清扫）的解耦",
    "  三色抽象把遍历过程形式化 —— 每个对象恰好经历白→灰→黑",
    "  清扫的白色集合 = 标记阶段触达不了的垃圾",
    "  966 课：清扫留碎片 → 标记-整理与复制式收集",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「标记缓冲」：分多轮标记（每轮处理 N 个灰色节点），记录暂停切片。
# 2. 实现「位图标记」：用整数位向量代替颜色字典，对比内存与速度。
# 3. 构造深链结构（1→2→3→...→100），验证标记的递归深度与迭代实现差异。
# 4. 思考：为什么清扫可以增量进行，而标记阶段传统上需要一次完成？
