# ===== 第970课：内存管理与垃圾回收-综合案例-迷你分代GC引擎 =====
# 知识点：
#   - 综合：对象图(963) + 引用计数(964) + 标记清扫(965) + 复制式(966) +
#     分代(967) + 增量屏障(968) + 调优(969)
#   - 迷你引擎：引用计数即时回收 + 周期性标记清理循环引用
#   - 负载模拟：常规分配 / 循环引用 / 长寿对象三种模式
#   - 输出运行报告：回收统计、循环检测、内存曲线
#   - CPython 同款架构：引用计数为主、循环收集器为辅
# 依赖：无（标准库）
import random


class GCObject:
    __slots__ = ("oid", "label", "size", "refcount", "refs",
                 "generation", "gc_flag")

    def __init__(self, oid, label, size):
        self.oid = oid
        self.label = label
        self.size = size
        self.refcount = 0
        self.refs = {}                        # 字段名 -> oid
        self.generation = 0                   # 0=年轻代 1=老年代
        self.gc_flag = False                  # 标记阶段的标志位


class MiniGCEngine:
    """引用计数 + 周期性循环收集（CPython 同款架构）。"""

    def __init__(self, cycle_threshold=10):
        self.objects = {}
        self.next_oid = 0
        self.roots = set()                    # 根集（变量持有）
        self.cycle_threshold = cycle_threshold
        self.allocations_since_cycle = 0
        self.stats = {"alloc": 0, "freed_refcount": 0,
                      "cycles": 0, "freed_cycle": 0}

    # ---- 分配与引用管理 ----
    def alloc(self, label, size=64):
        self.next_oid += 1
        oid = self.next_oid
        self.objects[oid] = GCObject(oid, label, size)
        self.roots.add(oid)                  # 变量持有引用：根集 + 计数
        self.objects[oid].refcount += 1
        self.stats["alloc"] += 1
        self.allocations_since_cycle += 1
        return oid

    def incref(self, oid):
        self.objects[oid].refcount += 1

    def decref(self, oid):
        obj = self.objects.get(oid)
        if obj is None:
            return
        obj.refcount -= 1
        if obj.refcount <= 0:
            self._destroy(oid)

    def _destroy(self, oid):
        obj = self.objects.pop(oid)
        self.stats["freed_refcount"] += 1
        for ref_oid in obj.refs.values():     # 级联 decref
            self.decref(ref_oid)

    def set_ref(self, holder_oid, field, target_oid):
        """赋值：旧目标 decref，新目标 incref。"""
        holder = self.objects[holder_oid]
        old = holder.refs.get(field)
        if old is not None:
            self.decref(old)
        if target_oid is not None:
            self.objects[target_oid].refcount += 1
        holder.refs[field] = target_oid

    def drop_root(self, oid):
        """根引用消失：decref。"""
        self.roots.discard(oid)
        self.decref(oid)

    # ---- 循环收集器（标记-清扫式）----
    def collect_cycles(self):
        """两阶段：1) 候选（rc>0 但可能成环）减计数试探；2) 标记可达回收。"""
        self.stats["cycles"] += 1
        # 阶段 1：对候选对象执行『试探性 decref』（CPython 的 gc_refs 技法）
        trial = {}
        for oid, obj in self.objects.items():
            trial[oid] = obj.refcount
        for oid, obj in self.objects.items():
            if obj.refcount > 0:
                for ref_oid in obj.refs.values():
                    if ref_oid in trial:
                        trial[ref_oid] -= 1
        # trial > 0 的对象：有外部引用，确定存活；trial == 0 的可能是环
        candidates = {oid: cnt for oid, cnt in trial.items() if cnt == 0}
        # 阶段 2：从 trial>0 的对象出发标记可达
        definitely_alive = {oid for oid, cnt in trial.items() if cnt > 0}
        live = set()
        queue = deque(definitely_alive)
        while queue:
            oid = queue.popleft()
            if oid in live:
                continue
            live.add(oid)
            for ref_oid in self.objects[oid].refs.values():
                if ref_oid in self.objects and ref_oid not in live:
                    queue.append(ref_oid)
        # 阶段 3：不在 live 中的候选 → 环垃圾，回收
        freed = [oid for oid in candidates if oid not in live]
        for oid in freed:
            obj = self.objects.pop(oid)
            self.stats["freed_cycle"] += 1
        return freed

    def maybe_collect(self):
        if self.allocations_since_cycle >= self.cycle_threshold:
            freed = self.collect_cycles()
            self.allocations_since_cycle = 0
            return freed
        return []

    def heap_report(self):
        alive = [o for o in self.objects.values() if o.refcount > 0]
        total_size = sum(o.size for o in self.objects.values())
        return {"对象数": len(self.objects), "活跃": len(alive),
                "内存": total_size}


from collections import deque

print("== 启动引擎（循环阈值 10 次分配）==")
engine = MiniGCEngine(cycle_threshold=10)

print("\n== 阶段 1：普通对象（引用计数回收）==")
oid1 = engine.alloc("临时1")
oid2 = engine.alloc("临时2")
engine.drop_root(oid2)                        # 临时2 无引用 → 即时回收
print(f"  alloc 2 个，drop 1 个 -> 即时回收: {engine.stats['freed_refcount']} 个")
print(f"  堆中剩余对象: {len(engine.objects)}")

print("\n== 阶段 2：长寿对象 + 字段引用 ==")
oid_root = engine.alloc("根对象")
engine.set_ref(oid_root, "child", oid1)
engine.incref(oid_root)
print(f"  根对象引用 临时1: 临时1 计数 = "
      f"{engine.objects[oid1].refcount}")

print("\n== 阶段 3：制造循环引用（引用计数无解）==")
c1 = engine.alloc("环A")
c2 = engine.alloc("环B")
engine.set_ref(c1, "peer", c2)
engine.set_ref(c2, "peer", c1)
print(f"  环A ↔ 环B: A 计数 {engine.objects[c1].refcount}, "
      f"B 计数 {engine.objects[c2].refcount}")
engine.drop_root(c1)
engine.drop_root(c2)
print(f"  根引用全部消失: A 计数 {engine.objects[c1].refcount}, "
      f"B 计数 {engine.objects[c2].refcount}")
print("  计数不为零但已不可达 —— 等待循环收集器")

print("\n== 阶段 4：触发循环收集 ==")
for _ in range(8):                            # 制造分配压力
    oid = engine.alloc(f"填充{engine.next_oid}")
    engine.drop_root(oid)                     # 引用计数即时回收（引用计数归零）
freed = engine.maybe_collect()
print(f"  循环收集回收: {freed}")
print(f"  循环对象已从堆中消失: {c1 not in engine.objects and c2 not in engine.objects}")
print(f"  正常对象仍在: {oid_root in engine.objects}")

print("\n== 阶段 5：压力负载与报告 ==")
rng = random.Random(170)
for round_i in range(50):
    oids = [engine.alloc(f"压力{round_i}o{i}") for i in range(3)]
    # 一半对象被引用链保留，一半丢弃
    engine.incref(oids[0])
    for oid in oids[1:]:
        engine.drop_root(oid)
    if round_i % 5 == 4:
        engine.maybe_collect()
report = engine.heap_report()
print(f"  压力测试 50 轮后堆状态: {report}")

print("\n== 引擎运行统计 ==")
print(f"  {'指标':<22}{'数值':>10}")
for label, value in (("总分配", engine.stats["alloc"]),
                     ("引用计数回收", engine.stats["freed_refcount"]),
                     ("循环收集次数", engine.stats["cycles"]),
                     ("循环回收对象", engine.stats["freed_cycle"])):
    print(f"  {label:<22}{value!s:>10}")
refcount_ratio = engine.stats["freed_refcount"] / max(engine.stats["alloc"], 1)
print(f"  引用计数回收占比 = {refcount_ratio:.1%}"
      f"（CPython 的日常：绝大多数对象由计数即时回收）")

print("\n== 与 CPython 的对应 ==")
print(f"  {'本引擎':<26}{'CPython'}")
for row in (("refcount 字段", "ob_refcnt"),
            ("decref 级联", "tp_dealloc"),
            ("collect_cycles 试探减计数", "gc 模块的 PyGC_Head"),
            ("cycle_threshold=10", "gc.set_threshold()"),
            ("roots 集合", "栈帧/全局变量")):
    print(f"  {row[0]:<26}{row[1]}")

print("\n== 小结 ==")
for line in (
    "  迷你引擎 = 引用计数（主力）+ 循环收集（补丁），正是 CPython 架构",
    "  试探性减计数：把『内部引用』排除后看计数是否归零 —— 环检测的精髓",
    "  分配阈值触发收集：小堆少收、大堆多收的自适应节奏",
    "  至此内存管理篇完结：分配(863) + 回收(964~970) 两大子系统",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「分代升级」：存活过 3 次循环收集的对象进老年代集合，降低扫描成本。
# 2. 实现「弱引用」：不影响计数且在对象回收时自动置空。
# 3. 加「GC 压力测试」：随机对象图 + 随机根集变化，验证无泄漏（最终全回收）。
# 4. 思考：为什么 CPython 不改成追踪式 GC？引用计数的即时析构在什么场景
#    是『正确性需求』而非『优化』？
