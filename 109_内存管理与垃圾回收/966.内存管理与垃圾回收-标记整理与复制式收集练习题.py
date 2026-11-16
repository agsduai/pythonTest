# ===== 第966课：内存管理与垃圾回收-标记整理与复制式收集 =====
# 知识点：
#   - 标记-清扫的遗留问题：碎片化 —— 空闲空间散落，大对象分不到
#   - 标记-整理（compact）：标记后把活对象滑动到一端 —— 碎片归零
#   - 复制式收集（Cheney）：半空间互换，活对象搬过去 —— 分配变 O(1) bump
#   - 整理/复制的代价：移动对象需要更新所有引用 —— 需要知道指针位置
#   - 代价模型：复制式 = 只付活对象的成本（死对象零开销）
# 依赖：无（标准库）


class FragmentedHeap:
    """演示碎片的标记-清扫堆。"""

    def __init__(self, slots=12):
        self.slots = slots                   # 内存槽（每槽 1 单位）
        self.slots_used = [None] * slots     # 槽位 -> 对象 id
        self.objects = {}                    # id -> {"refs", "size", "slots"}

    def alloc(self, label, refs, size):
        size = max(1, size)
        free_runs = self._free_runs()
        for start, length in free_runs:
            if length >= size:
                oid = f"{label}"
                slot_list = list(range(start, start + size))
                for s in slot_list:
                    self.slots_used[s] = oid
                self.objects[oid] = {"refs": refs, "size": size,
                                     "slots": slot_list}
                return oid
        raise MemoryError(f"最大连续空闲 {max(l[1] for l in free_runs)} < 需要 {size}")

    def _free_runs(self):
        runs = []
        start = None
        for i, used in enumerate(self.slots_used + [1]):   # 哨兵
            if used is None:
                if start is None:
                    start = i
            else:
                if start is not None:
                    runs.append((start, i - start))
                    start = None
        return runs

    def sweep(self, reachable):
        """清扫：释放不可达对象的槽位。"""
        freed = []
        for oid in list(self.objects):
            if oid not in reachable:
                for s in self.objects[oid]["slots"]:
                    self.slots_used[s] = None
                freed.append(oid)
                del self.objects[oid]
        return freed

    def fragmentation(self):
        runs = self._free_runs()
        total_free = sum(l for _, l in runs)
        largest = max((l for _, l in runs), default=0)
        return {"空闲总槽": total_free, "空闲段数": len(runs),
                "最大连续段": largest}


print("== 碎片的产生 ==")
heap = FragmentedHeap(slots=12)
a = heap.alloc("A", [], 3)                  # 槽 0-2
b = heap.alloc("B", [], 2)                  # 槽 3-4
c = heap.alloc("C", [], 3)                  # 槽 5-7
d = heap.alloc("D", [], 2)                  # 槽 8-9
print(f"  分配 A(3) B(2) C(3) D(2)：{heap.slots_used}")
# B 死亡 → 槽 3-4 空出
for s in heap.objects["B"]["slots"]:
    heap.slots_used[s] = None
del heap.objects["B"]
print(f"  B 死亡后：{heap.slots_used}")
print(f"  碎片状态: {heap.fragmentation()}")

print("\n== 碎片的危害：总和够但连续不够 ==")
try:
    heap.alloc("E", [], 4)
except MemoryError as exc:
    print(f"  分配 4 连续槽失败: {exc}")
print("  空闲总槽 = 5 ≥ 4，但最大连续段只有 2 —— 碎片化是散落的空房")

print("\n== 标记-整理（compact）：滑动到一端 ==")
reachable = {"A", "C", "D"}                 # 标记结果
compact_slots = [None] * heap.slots
write = 0
moved = []
for i in range(heap.slots):
    oid = heap.slots_used[i]
    if oid in reachable:
        if i != write:
            moved.append((oid, i, write))
        compact_slots[write] = oid
        write += 1
heap.slots_used = compact_slots
print(f"  整理后：{heap.slots_used}")
for oid, old, new in moved:
    print(f"  {oid}: 槽 {old} → 槽 {new}（引用表同步更新）")
print(f"  整理后空闲 = {heap.slots - write} 连续槽 —— 分配 E 不再有问题")
e = heap.alloc("E", [], 4)
print(f"  重新分配 E(4)：{heap.slots_used}")

print("\n== 复制式收集（Cheney 算法）==")


class CopyingGC:
    """半空间复制：from-space 活对象搬到 to-space，然后交换。"""

    def __init__(self, half=8):
        self.half = half
        self.from_space = {}
        self.to_space = {}
        self.scan_pointer = 0                # Cheney 的_free 指针
        self.roots = []

    def alloc(self, label, refs=()):
        oid = label
        if len(self.from_space) + len(self.to_space) >= self.half:
            self.collect()
            if len(self.from_space) + len(self.to_space) >= self.half:
                raise MemoryError("复制 GC 后仍不足")
        self.from_space[oid] = {"refs": refs, "forward": None}
        return oid

    def collect(self):
        self.to_space = {}
        queue = deque(self.roots)
        moved = []
        # 先搬根集
        for r in self.roots:
            if r in self.from_space:
                self.to_space[r] = dict(self.from_space[r])
                moved.append(r)
        # Cheney 扫描：逐个处理 to-space 中已搬的对象
        scan = list(self.roots)
        i = 0
        while i < len(scan):
            oid = scan[i]
            i += 1
            for ref in self.to_space[oid]["refs"]:
                if ref in self.from_space and ref not in self.to_space:
                    self.to_space[ref] = dict(self.from_space[ref])
                    scan.append(ref)
        self.from_space = {}
        self.scan_pointer = 0
        return moved


from collections import deque
cg = CopyingGC(half=8)
cg.roots = ["root"]
cg.alloc("root", ["child1", "child2"])
cg.alloc("child1", ["grandchild"])
cg.alloc("child2", [])
cg.alloc("garbage", [])                      # 不可达
cg.alloc("grandchild", [])
print(f"  收集前 from-space: {sorted(cg.from_space)}")
moved = cg.collect()
print(f"  复制后 to-space: {sorted(cg.to_space)}")
print(f"  搬运顺序（Cheney 扫描）: {moved}")
print("  垃圾（garbage）根本没被复制 —— 死对象的回收是零成本的！")
print("  分配指针 bump：新分配 = to-space 末尾 +1 —— O(1) 极速分配")

print("\n== 三种算法的成本对比 ==")
print(f"  {'算法':<14}{'分配':<12}{'回收成本':<22}{'适用'}")
for row in (("标记-清扫", "空闲链表查找", "整个堆遍历", "通用"),
            ("标记-整理", "空闲链表/整理后顺序", "堆遍历 ×2 + 引用更新", "防碎片"),
            ("复制式", "bump 指针 O(1)", "只付活对象成本", "年轻代（死亡多）")):
    print(f"  {row[0]:<14}{row[1]:<12}{row[2]:<22}{row[3]}")

print("\n== 小结 ==")
for line in (
    "  碎片是标记-清扫的结构性缺陷；整理与复制是两种解法",
    "  复制式收集的核心洞察：回收成本只与活对象成正比",
    "  代价：空间减半 + 对象需要移动（引用更新）",
    "  967 课：分代收集 —— 把复制式用在『死亡最多』的年轻代",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现整理时的「引用更新」：对象移动后所有指向它的引用同步改写。
# 2. 实现「滑动整理的两次遍历」：先计算新地址，再搬移（Lisp2 算法）。
# 3. 对比复制式在『存活率 90%』与『存活率 10%』下的成本差异。
# 4. 思考：为什么 JVM 年轻代用复制式而老年代用标记-整理？
