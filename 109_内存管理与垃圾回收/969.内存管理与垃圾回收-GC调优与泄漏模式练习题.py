# ===== 第969课：内存管理与垃圾回收-GC调优与泄漏模式 =====
# 知识点：
#   - GC 调优三目标：吞吐（应用时间占比）、延迟（暂停上界）、内存占用
#   - 泄漏模式：无界缓存、监听器未注销、ThreadLocal 未清理、静态集合累积
#   - 堆增长曲线是泄漏检测的『心电图』：锯齿基线持续抬升 = 泄漏
#   - 参数联动：年轻代大小 ↔ Minor 频率 ↔ 晋升速率 ↔ Full GC 触发
#   - 工具链：GC 日志、堆快照、分配剖析（allocation profiling）
# 依赖：无（标准库）
import math
import random


class GCSimulator:
    """带可调参数的应用+GC 联合模拟器。"""

    def __init__(self, young_size=50, promote_age=2, full_threshold=200,
                 leak_rate=0.0, seed=169):
        self.rng = random.Random(seed)
        self.young_size = young_size
        self.promote_age = promote_age
        self.full_threshold = full_threshold
        self.leak_rate = leak_rate
        self.young = {}
        self.old = {}
        self.age = {}
        self.total_alloc = 0
        self.leaked = 0
        self.gc_events = []
        self.heap_curve = []

    def allocate_round(self, round_id):
        """一轮应用负载：分配若干对象 + 泄漏少量（模拟 bug）。"""
        allocations = []
        n = self.rng.randint(8, 15)
        for i in range(n):
            oid = f"r{round_id}o{i}"
            is_long_lived = self.rng.random() < 0.1
            refs = ["root"] if is_long_lived else []
            self.young[oid] = {"refs": refs}
            self.age[oid] = 0
            allocations.append(oid)
        # 泄漏：每轮把 leak_rate 比例的『临时对象』偷偷挂到全局（模拟 bug）
        leaked_n = int(n * self.leak_rate)
        for i in range(leaked_n):
            oid = allocations[i]
            if oid in self.young:
                self.young[oid]["leaked"] = True
                self.leaked += 1
        self.total_alloc += n

    def minor_gc(self):
        live = {"root"}
        # 泄漏对象也是『可达』的（挂在全局上）—— 这正是泄漏的定义
        for oid, meta in self.young.items():
            if meta.get("leaked"):
                live.add(oid)
        queue = list(live)
        all_objs = {**self.young, **self.old}
        while queue:
            oid = queue.pop()
            for ref in all_objs.get(oid, {}).get("refs", []):
                if ref not in live and ref in all_objs:
                    live.add(ref)
                    queue.append(ref)
        promoted, died = [], 0
        for oid in list(self.young):
            if oid in live:
                self.age[oid] += 1
                if self.age[oid] >= self.promote_age:
                    self.old[oid] = self.young.pop(oid)
                    promoted.append(oid)
            else:
                del self.young[oid]
                died += 1
        self.gc_events.append(("minor", died, len(promoted)))
        return promoted

    def heap_usage(self):
        return len(self.young) + len(self.old)

    def run(self, rounds=60):
        for r in range(rounds):
            self.allocate_round(r)
            if len(self.young) >= self.young_size:
                self.minor_gc()
            # Full GC：老年代超过阈值
            if len(self.old) > self.full_threshold:
                before = len(self.old)
                # 全量回收：无泄漏引用的老对象被清（简化模型）
                self.old = {oid: meta for oid, meta in self.old.items()
                            if meta.get("leaked") or oid == "root"}
                self.gc_events.append(("major", before - len(self.old),
                                       len(self.old)))
            self.heap_curve.append(self.heap_usage())
            if self.leaked > self.full_threshold * 2:
                self.gc_events.append(("OOM", self.leaked, self.leaked))
                break
        return self.heap_curve


print("== 场景 1：健康应用（无泄漏）==")
sim_healthy = GCSimulator(leak_rate=0.0)
curve_ok = sim_healthy.run(rounds=60)
print(f"  {'轮':>4}{'堆占用':>8}  曲线")
for r in range(0, 60, 5):
    print(f"  {r:>4}{curve_ok[r]:>8}  {'#' * int(curve_ok[r] / max(curve_ok) * 36)}")
print(f"  60 轮后堆占用 = {curve_ok[-1]}（锯齿稳定 = 无泄漏）")
print(f"  Minor GC {sum(1 for e in sim_healthy.gc_events if e[0] == 'minor')} 次, "
      f"Full GC {sum(1 for e in sim_healthy.gc_events if e[0] == 'major')} 次")

print("\n== 场景 2：泄漏应用（每轮泄漏 10%）==")
sim_leak = GCSimulator(leak_rate=0.15)
curve_leak = sim_leak.run(rounds=60)
for r in range(0, 60, 10):
    print(f"  轮 {r:>3}: 堆占用 {curve_leak[r]:>4}  "
          f"{'#' * int(curve_leak[r] / max(curve_leak) * 36)}")
print(f"  60 轮后堆占用 = {curve_leak[-1]} vs 健康应用 {curve_ok[-1]}")
print(f"  泄漏对象总数 = {sim_leak.leaked}")
if any(e[0] == "OOM" for e in sim_leak.gc_events):
    print("  ⚠ 触发 OOM 模拟 —— 泄漏撑爆了堆")

print("\n== 堆增长曲线的形态判读 ==")
print(f"  {'形态':<22}{'诊断'}")
for row in (("锯齿稳定（基线平）", "健康：GC 周期性回收"),
            ("锯齿基线持续抬升", "泄漏：每轮都有对象逃逸回收"),
            ("锯齿幅度变大", "存活对象变多（缓存膨胀/晋升加速）"),
            ("频繁 Full GC", "老年代被长寿命对象占满")):
    print(f"  {row[0]:<22}{row[1]}")

print("\n== 调优参数的敏感性实验 ==")
print(f"  {'年轻代':>8}{'Minor次数':>10}{'Full次数':>10}{'堆占用':>10}")
for young in (20, 50, 100):
    sim = GCSimulator(young_size=young, leak_rate=0.0)
    curve = sim.run(rounds=60)
    minor_n = sum(1 for e in sim.gc_events if e[0] == "minor")
    full_n = sum(1 for e in sim.gc_events if e[0] == "major")
    print(f"  {young:>8}{minor_n:>10}{full_n:>10}{curve[-1]:>10}")
print("  年轻代大 → Minor 少、对象晋升慢 → 老年代压力小；但内存占用高")

print("\n== 四大泄漏模式 ==")
for line in (
    "  1. 无界缓存：Map 只进不出 → 加 TTL/LRU 上限",
    "  2. 监听器：注册后忘记注销 → 用弱引用或生命周期钩子",
    "  3. ThreadLocal：线程池复用线程 → 用完必须 remove()",
    "  4. 闭包捕获：回调持有大对象引用 → 缩小捕获范围",
):
    print("  -", line)

print("\n== GC 日志的读法 ==")
print(f"  {'日志字段':<22}{'解读'}")
for row in (("minor: died=45", "45 个年轻代对象被回收（正常）"),
            ("minor: promoted=12", "12 个晋升 —— 关注晋升速率"),
            ("major: freed_old=3", "Full GC 只回收 3 个 —— 老年代被占住"),
            ("OOM", "泄漏或堆参数不足")):
    print(f"  {row[0]:<22}{row[1]}")

print("\n== 小结 ==")
for line in (
    "  GC 调优 = 在吞吐、延迟、内存三角形里找业务的平衡点",
    "  泄漏的早期信号是『基线抬升』—— 看曲线胜过看单次快照",
    "  每个泄漏模式都有对应的工程习惯防线 —— 习惯比工具便宜",
    "  970 课：综合案例 —— 把 963~969 的全部机制装进迷你 GC 引擎",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「分配站点统计」：记录每个分配点的存活对象数，定位泄漏源。
# 2. 实现「GC 负载模拟」：比较吞吐随年轻代大小的 U 形曲线，找出最优值。
# 3. 实现「堆快照 diff」：两次快照对比，列出增长最快的对象类别。
# 4. 思考：为什么『并发 GC』不能完全消除对调优的需求？（吞吐与延迟的
#    此消彼长是物理约束）
