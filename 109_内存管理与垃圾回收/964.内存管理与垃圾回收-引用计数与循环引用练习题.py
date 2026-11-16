# ===== 第964课：内存管理与垃圾回收-引用计数与循环引用 =====
# 知识点：
#   - 引用计数：每个对象记录『有多少指针指着我』，归零立即回收
#   - incref/decref 的时机：赋值、传参、返回、离开作用域
#   - 优点：回收即时（确定性析构）、暂停短、局部性好
#   - 致命伤：循环引用互相计数永不为零 —— 需要辅助的追踪 GC
#   - CPython 的方案：主引用计数 + gc 模块的分代循环检测器
# 依赖：无（标准库）


class RefCountObject:
    """带引用计数的模拟对象。"""

    def __init__(self, label):
        self.label = label
        self.refcount = 0
        self.refs = {}                       # 字段名 -> 被引用对象
        self.dead = False

    def add_ref(self):
        self.refcount += 1

    def release_ref(self):
        self.refcount -= 1
        if self.refcount == 0:
            self._destroy()

    def set_field(self, name, target):
        """字段赋值：旧目标 decref，新目标 incref。"""
        old = self.refs.get(name)
        if old is not None:
            old.release_ref()
        if target is not None:
            target.add_ref()
        self.refs[name] = target
        if self.refcount == 0 and not self.dead:
            self._destroy()

    def _destroy(self):
        self.dead = True
        # 级联 decref：我引用的对象都少一个引用者
        for target in self.refs.values():
            if target is not None:
                target.release_ref()
        self.refs = {}


class RefCountHeap:
    def __init__(self):
        self.objects = {}

    def alloc(self, label):
        obj = RefCountObject(label)
        self.objects[obj.label] = obj
        obj.add_ref()                        # 变量持有引用
        return obj

    def drop_variable(self, obj):
        """变量离开作用域：释放变量持有的引用。"""
        obj.release_ref()
        self.objects.pop(obj.label, None) if obj.dead else None

    def live_objects(self):
        return [o for o in self.objects.values() if not o.dead]


print("== 基本 incref/decref ==")
heap = RefCountHeap()
a = heap.alloc("对象A")
print(f"  A 引用计数 = {a.refcount}（变量持有）")
b_ref = a                             # 赋值给另一变量：+1
a.add_ref()
print(f"  赋值给第二个变量后 = {a.refcount}")
a.release_ref()
print(f"  第二变量离开作用域 = {a.refcount}")
a.release_ref()
print(f"  最后一个变量离开 -> 计数归零 -> 立即回收: {a.dead}")
print("  确定性析构：归零的瞬间执行清理 —— 资源管理（文件/锁）的便利性")

print("\n== 字段赋值的两向计数 ==")
owner = heap.alloc("容器")
child = heap.alloc("子对象")
owner.set_field("child", child)
print(f"  owner.child = child: child 计数 = {child.refcount}")
owner.set_field("child", None)
print(f"  owner.child = None: child 计数 = {child.refcount} -> 回收 {child.dead}")
print("  每次赋值都是一对 incref/decref —— 这就是引用计数的全部秘密")

print("\n== 循环引用：引用计数的死穴 ==")
node_a = heap.alloc("节点A")
node_b = heap.alloc("节点B")
node_a.set_field("next", node_b)
node_b.set_field("next", node_a)
print(f"  A ↔ B 互相引用: A 计数 {node_a.refcount}（含变量 + B 的字段）, "
      f"B 计数 {node_b.refcount}")
heap.drop_variable(node_a)
heap.drop_variable(node_b)
print(f"  变量全部离开作用域后: A 活着 = {not node_a.dead}, "
      f"B 活着 = {not node_b.refcount == 0 and True}")
print(f"  A 计数 = {node_a.refcount}（只剩 B 的字段引用）")
print(f"  B 计数 = {node_b.refcount}（只剩 A 的字段引用）")
print("  互相扶持 → 计数永不归零 → 永久泄漏 —— 引用计数无法独自解决")

print("\n== 弱引用打破循环 ==")


class WeakRefObject:
    def __init__(self, label):
        self.label = label
        self.refcount = 0
        self.weak_refs = []                  # 弱引用：不增加计数
        self.dead = False

    def add_ref(self):
        self.refcount += 1

    def release_ref(self):
        self.refcount -= 1
        if self.refcount == 0:
            self.dead = True
            for weak in self.weak_refs:
                weak["target"] = None        # 通知弱引用持有者


cache = WeakRefObject("缓存对象")
observer = {"target": cache, "weak": True}   # 观察者持弱引用
cache.weak_refs.append(observer)
print(f"  弱引用不增加计数: {cache.refcount}")
cache.release_ref()                          # 变量释放 -> 归零回收
print(f"  缓存回收: {cache.dead}，弱引用自动变 None: {observer['target'] is None}")
print("  弱引用让『引用但不拥有』成立 —— 缓存/回调/观察者的标准解法")

print("\n== 循环回收：追踪式辅助 GC ==")
def mark_live(obj, seen):
    if obj.dead or id(obj) in seen:
        return seen
    seen.add(id(obj))
    for t in obj.refs.values():
        if t is not None:
            mark_live(t, seen)
    return seen


live = mark_live(node_a if not node_a.dead else node_b, set())
# 真正的循环检测：把变量释放后的 A/B 看作候选，追踪确认无可达根
print(f"  变量全灭后 A/B 互指：从任一节点出发遍历发现闭包 {len(live)} 个对象")
print("  辅助 GC 定期运行：它不关心计数，只关心可达性 —— 循环整体不可达 → 回收")

print("\n== 引用计数的工程权衡 ==")
print(f"  {'维度':<12}{'引用计数':<22}{'追踪 GC'}")
for row in (("回收时机", "归零即时", "批量"),
            ("暂停时间", "分散（decref 级联）", "集中（STW）"),
            ("循环引用", "泄漏", "正确处理"),
            ("写开销", "每次赋值 +1/-1", "写屏障（增量式）")):
    print(f"  {row[0]:<12}{row[1]:<22}{row[2]}")

print("\n== 小结 ==")
for line in (
    "  引用计数把回收切成无数个微小的即时操作 —— 确定性是它的光环",
    "  循环引用是结构性的死穴：计数只统计『谁指着我』不问『我可不可达』",
    "  CPython = 主引用计数 + gc 模块循环检测器，两层配合",
    "  965 课：纯追踪方案 —— 标记-清扫",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「析构回调」：对象回收时触发 __del__ 式钩子，验证级联顺序。
# 2. 实现弱引用表自动清理：对象回收时从弱引用表中移除自身。
# 3. 构造三节点环 A→B→C→A，验证引用计数全部为 2（变量+环）且无法回收。
# 4. 思考：为什么引用计数的 decref 级联也可能造成长暂停？（大树级联释放）
