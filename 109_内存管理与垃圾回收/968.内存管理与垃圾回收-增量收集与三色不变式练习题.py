# ===== 第968课：内存管理与垃圾回收-增量收集与三色不变式 =====
# 知识点：
#   - 全量 GC 的 STW 与堆成正比 → 大堆无法接受 → 切成小步
#   - 三色不变式：强不变式 = 不存在黑→白引用；破坏即误回收活对象
#   - 写屏障：赋值时拦截，把被引用的白对象重新着灰 —— 维护不变式
#   - 删除屏障：黑对象删除灰引用时也要处理（两屏障取其一或都用）
#   - 增量标记的进度保证：灰色节点 = 待办事项，写屏障防『清零待办』
# 依赖：无（标准库）
from collections import deque


class IncrementalGC:
    """增量标记-清扫：mutator（应用）与 GC 交替运行。"""

    def __init__(self, step_budget=2):
        self.objects = {}                    # oid -> {"refs": set, "color": str}
        self.roots = set()
        self.gray = deque()
        self.state = "idle"                  # idle / marking / sweeping
        self.step_budget = step_budget
        self.write_barrier_log = []
        self.barrier_mode = "incremental_update"
        self.sweep_cursor = 0

    def alloc(self, label, refs=(), color="white"):
        oid = label
        self.objects[oid] = {"refs": set(refs), "color": color, "label": label}
        return oid

    def mutate(self, oid, field, new_target):
        """mutator 操作：对象引用变更 —— 触发写屏障。"""
        old = self.objects[oid]["refs"]
        old.add(new_target)
        self.write_barrier(oid, new_target)

    def write_barrier(self, oid, new_target):
        """增量更新屏障：黑对象引用白对象 → 白变灰（或黑降灰）。"""
        obj = self.objects[oid]
        if obj["color"] == "black":
            target = self.objects.get(new_target)
            if target and target["color"] == "white":
                target["color"] = "gray"
                self.gray.append(new_target)
                self.write_barrier_log.append(
                    f"屏障: 黑{oid} 新引用 白{new_target} → 灰化 {new_target}")

    def mark_start(self):
        """标记开始：根集灰化。"""
        for r in self.roots:
            obj = self.objects[r]
            if obj["color"] == "white":
                obj["color"] = "gray"
                self.gray.append(r)
        self.state = "marking"

    def mark_step(self):
        """一步标记：处理 step_budget 个灰色节点。"""
        done = 0
        while self.gray and done < self.step_budget:
            oid = self.gray.popleft()
            obj = self.objects[oid]
            if obj["color"] != "gray":
                continue
            for ref in obj["refs"]:
                target = self.objects.get(ref)
                if target and target["color"] == "white":
                    target["color"] = "gray"
                    self.gray.append(ref)
            obj["color"] = "black"
            done += 1
        if not self.gray:
            self.state = "sweeping"
            self.sweep_cursor = 0
        return done

    def sweep_step(self):
        """一步清扫：扫一段堆。"""
        oids = list(self.objects)
        freed = []
        end = min(self.sweep_cursor + self.step_budget, len(oids))
        for i in range(self.sweep_cursor, end):
            oid = oids[i]
            if self.objects[oid]["color"] == "white":
                freed.append(oid)
        self.sweep_cursor = end
        if self.sweep_cursor >= len(oids):
            for oid in freed:
                del self.objects[oid]
            self.state = "idle"
        return freed

    def step(self):
        """GC 的一步：按状态分派。"""
        if self.state == "marking":
            return self.mark_step()
        if self.state == "sweeping":
            return self.sweep_step()
        self.mark_start()
        return 0


print("== 场景搭建 ==")
gc = IncrementalGC(step_budget=2)
gc.roots = {"rootA"}
gc.alloc("rootA", ["obj1"], color="black")
gc.alloc("obj1", ["obj2"], color="black")       # 已标记为黑（模拟上轮已扫）
gc.alloc("obj2", [], color="white")             # 白色待标记
gc.alloc("obj3", [], color="white")
print("  初始: rootA(黑) → obj1(黑) → obj2(白) → obj3(白)")

print("\n== 危险时刻：黑对象新增白引用 ==")
gc.mark_start()
gc.mark_step()                                  # 处理 rootA → obj1 灰
gc.mutate("obj1", "extra", "obj3")              # 黑对象 obj1 引用白 obj3！
print("  mutator: obj1(黑) 新增引用 obj3(白) —— 不变式被破坏!")
print(f"  写屏障日志: {gc.write_barrier_log}")
print("  屏障把 obj3 灰化 → obj3 会被扫到 → 不会被误回收")

print("\n== 不写屏障的后果演示 ==")
gc2 = IncrementalGC()
gc2.roots = {"r"}
gc2.alloc("r", ["a"], color="black")
gc2.alloc("a", ["b"], color="black")            # a 已黑，b 尚白
gc2.alloc("b", [], color="white")
gc2.mark_start()
gc2.mark_step()                                 # 处理 r；a 已黑被跳过？b 仍白
# mutator 破坏不变式：黑 a 引用白 b（无屏障）
gc2.objects["a"]["refs"].add("b")
while gc2.state == "marking":
    gc2.mark_step()
gc2.state = "sweeping"
freed = []
gc2.state = "sweeping"
gc2.sweep_cursor = 0
oids = list(gc2.objects)
freed = [o for o in oids if gc2.objects[o]["color"] == "white"]
print(f"  无屏障时被误回收的对象: {freed}")
print("  b 是活对象却被当垃圾回收 → 悬垂指针 → 崩溃 —— 这就是必须写屏障的理由")

print("\n== 增量步进：mutator 与 GC 交替 ==")
gc3 = IncrementalGC(step_budget=1)
gc3.roots = {"r"}
gc3.alloc("r", ["a", "b", "c"], color="white")
gc3.alloc("a", [], color="white")
gc3.alloc("b", [], color="white")
gc3.alloc("c", [], color="white")
gc3.mark_start()
print("  交替执行：mutator 一步 / GC 一步")
for i in range(6):
    done = gc3.mark_step()
    print(f"  GC步{i + 1}: 处理 {done} 个灰色节点, "
          f"灰队列 = {len(gc3.gray)}, 状态 = {gc3.state}")
colors = {k: v["color"] for k, v in gc3.objects.items()}
print(f"  全部着色: {colors}")
print("  每步最多处理 budget 个节点 → 暂停时间有上界")

print("\n== 暂停时间对比 ==")
print(f"  {'方案':<16}{'单次暂停':<20}{'总开销'}")
for row in (("全量 STW", "与堆成正比（大）", "最低"),
            ("增量式", "有上界（小）", "屏障开销 + 总量略增"),
            ("并发式", "接近零", "CPU 竞争 + 两套屏障")):
    print(f"  {row[0]:<16}{row[1]:<20}{row[2]}")

print("\n== 小结 ==")
for line in (
    "  三色不变式是并发/增量 GC 的正确性基石",
    "  写屏障 = 赋值操作上的一道检查 —— 微小开销换暂停上界",
    "  增量更新 vs 快照（SATB）是两大屏障流派",
    "  969 课：GC 的调优 —— 让参数服务业务负载",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「删除屏障（SATB 风格）」：删除灰引用前快照被删对象，对比两种屏障。
# 2. 实现「清扫增量」的过渡：标记完成后清扫也按 budget 分步（本课已含框架）。
# 3. 构造「屏障遗漏」场景：只保护新增引用、不管删除引用，找到误回收路径。
# 4. 思考：为什么 Go 选择并发标记+清除，而 JVM 主流是并发标记+整理？
