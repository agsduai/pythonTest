# ===== 第967课：内存管理与垃圾回收-分代收集与晋升 =====
# 知识点：
#   - 弱分代假设：大多数对象朝生夕死 —— 这是分代收集的统计基础
#   - 年轻代：新对象在此分配，用复制式收集（死亡多 → 活对象少 → 便宜）
#   - 老年代：熬过若干次 GC 的对象晋升进来，用标记-整理（活得久 → 全量扫）
#   - Minor GC 只扫年轻代 → 快；Major/Full GC 扫全堆 → 慢但少
#   - 写屏障：老年代引用年轻代对象时必须登记 —— 否则年轻代漏标
# 依赖：无（标准库）
import random


class GenerationalGC:
    def __init__(self, young_size=8, promote_after=2):
        self.young = {}                      # 年轻代对象
        self.old = {}                        # 老年代对象
        self.age = {}                        # oid -> 经历过的 minor GC 次数
        self.young_size = young_size
        self.promote_after = promote_after
        self.remembered = set()              # 记忆集：老→新引用的来源（写屏障）
        self.gc_log = []
        self.minor_count = 0
        self.major_count = 0

    def alloc(self, label, refs=()):
        if len(self.young) >= self.young_size:
            self.minor_gc()
            if len(self.young) >= self.young_size:
                self.minor_gc()              # 晋升后仍满 → 强制再来一次
        oid = label
        self.young[oid] = {"refs": list(refs), "label": label}
        self.age[oid] = 0
        return oid

    def write_barrier(self, old_oid, new_ref_oid):
        """写屏障：老年代对象引用年轻代对象 → 登记进记忆集。"""
        if old_oid in self.old and new_ref_oid in self.young:
            self.remembered.add(old_oid)
            self.gc_log.append(f"[写屏障] {old_oid} 引用新对象 {new_ref_oid}，登记")

    def minor_gc(self):
        """Minor GC：复制式收集年轻代。"""
        self.minor_count += 1
        roots = ["root"]                     # 简化：root 是全局根
        live = set()
        queue = deque()
        for r in roots:
            if r in self.young:
                live.add(r)
                queue.append(r)
            elif r in self.old:
                live.add(r)
                queue.append(r)
        # 从根遍历（跨代引用从记忆集补根）
        queue.extend(self.remembered)
        all_objects = {**self.old, **self.young}
        while queue:
            oid = queue.popleft()
            for ref in all_objects.get(oid, {}).get("refs", []):
                if ref not in live and ref in all_objects:
                    live.add(ref)
                    queue.append(ref)
        # 年轻代：活对象晋升或留存，死对象消失
        promoted, survived = [], []
        for oid in list(self.young):
            if oid in live:
                self.age[oid] += 1
                if self.age[oid] >= self.promote_after:
                    self.old[oid] = self.young.pop(oid)
                    promoted.append(oid)
                else:
                    survived.append(oid)
            else:
                del self.young[oid]          # 年轻代死亡：零成本消失
        self.remembered = {r for r in self.remembered if r in self.old}
        self.gc_log.append(f"Minor GC#{self.minor_count}: "
                           f"存活 {len(survived)}, 晋升 {len(promoted)}, "
                           f"死亡 {self.young_size - len(survived) - len(promoted)}")
        return promoted

    def major_gc(self):
        """Major GC：全堆标记-清扫。"""
        self.major_count += 1
        all_objects = {**self.old, **self.young}
        live = set()
        queue = deque(["root"])
        while queue:
            oid = queue.popleft()
            if oid in live:
                continue
            live.add(oid)
            for ref in all_objects.get(oid, {}).get("refs", []):
                if ref not in live and ref in all_objects:
                    queue.append(ref)
        freed_old = [o for o in list(self.old) if o not in live]
        freed_young = [o for o in list(self.young) if o not in live]
        for o in freed_old:
            del self.old[o]
        for o in freed_young:
            del self.young[o]
        self.gc_log.append(f"Major GC#{self.major_count}: 回收老年代 "
                           f"{len(freed_old)}, 年轻代 {len(freed_young)}")


from collections import deque

print("== 弱分代假设的实证 ==")
rng = random.Random(167)
lifetimes = [rng.randint(1, 5) if rng.random() < 0.9 else rng.randint(50, 100)
             for _ in range(1000)]
short = sum(1 for l in lifetimes if l <= 5)
print(f"  模拟 1000 个对象的生命周期: {short}% 在 5 个采集周期内死亡")
print("  统计事实：绝大多数对象『朝生夕死』—— 年轻代集中回收它们最划算")

print("\n== 分代 GC 运行 ==")
ggc = GenerationalGC(young_size=6, promote_after=2)
ggc.young["root"] = {"refs": [], "label": "root"}
ggc.age["root"] = 0
alloc_events = [
    ("a", ["root"]), ("b", ["root"]), ("c", ["root"]),
    ("d", ["root"]), ("e", ["root"]), ("f", ["root"]),
    ("g", ["root"]), ("h", ["root"]),
]
for label, refs in alloc_events:
    ggc.alloc(label, refs)

print("\n== GC 日志 ==")
for entry in ggc.gc_log:
    print(f"  {entry}")
print(f"\n  年轻代: {sorted(ggc.young)}")
print(f"  老年代: {sorted(ggc.old)}")
print(f"  年龄表: { {k: ggc.age[k] for k in sorted(ggc.age)} }")

print("\n== 写屏障演示 ==")
ggc.write_barrier("root", "new_child")
# 老年代对象引用年轻代新对象
if ggc.old:
    old_oid = sorted(ggc.old)[0]
    ggc.old[old_oid]["refs"].append("young_new")
    ggc.write_barrier(old_oid, "young_new")
for entry in ggc.gc_log[-3:]:
    print(f"  {entry}")
print("  老年代引用年轻代 → 若 Minor GC 不把该年轻代对象当根 → 误回收！")
print("  记忆集（remembered set）是正确性的保险丝 —— 代价是写路径变慢")

print("\n== Minor vs Major 的成本对比 ==")
minor_cost = len(ggc.young) + len(ggc.remembered)   # 只与年轻代活对象成正比
major_cost = len(ggc.old) + len(ggc.young)          # 全堆
print(f"  Minor GC 成本 ∝ 年轻代活对象 ≈ {minor_cost}")
print(f"  Major GC 成本 ∝ 全堆 ≈ {major_cost}")
print("  比例取决于对象生命周期分布 —— 弱分代假设越强，收益越大")

print("\n== 分代参数的调优空间 ==")
print(f"  {'参数':<20}{'调大':<20}{'调小'}")
for row in (("年轻代大小", "Minor 更少", "晋升更快、老年代压力大"),
            ("晋升阈值", "对象在年轻代更久", "过早晋升占老年代"),
            ("老年代阈值", "Full GC 更少", "占用内存更久")):
    print(f"  {row[0]:<20}{row[1]:<20}{row[2]}")

print("\n== 小结 ==")
for line in (
    "  分代收集 = 弱分代假设 × 复制式（年轻）× 标记整理（年老）",
    "  Minor GC 的便宜来自『只看年轻代』—— 前提是死亡集中发生在那里",
    "  写屏障与记忆集维护跨代引用的正确性",
    "  晋升是年轻代与老年代之间的人口迁移通道",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「晋升阈值自适应」：存活率高的时期推迟晋升，观察老年代增长曲线。
# 2. 实现「Full GC 触发条件」：老年代占用超过 80% 时自动 Major GC。
# 3. 统计「晋升率」：每轮 Minor GC 晋升对象数 / 存活对象数，评估分代假设。
# 4. 思考：什么程序的分配模式会『打败』分代假设？（提示：缓存大量长寿对象）
