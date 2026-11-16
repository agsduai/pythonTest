# ===== 第863课：操作系统原理与资源管理-内存分配与伙伴系统 =====
# 知识点：
#   - 动态内存分配的核心矛盾：分配速度 vs 外部碎片
#   - 简单策略：首次适应/最佳适应/最坏适应，都是「洞列表」上的扫描
#   - 伙伴系统：把 2^k 大小的块对半分裂、按位异或找伙伴、释放时成对合并
#   - 优点：O(log n) 分配释放、天然合并、零外部碎片（代价是内部碎片）
#   - Linux 页分配器、内核 slab 底层都源于伙伴思想
# 依赖：无（标准库）


class Buddy:
    """伙伴系统：order k 的块大小 = 2^k。"""

    def __init__(self, order=6):
        self.order = order
        self.free = {order: [0]}          # order -> [地址...]

    def alloc(self, order):
        """分配 2^order 大小的块，返回 (地址, order) 或 None。"""
        for o in range(order, self.order + 1):
            if self.free.get(o):
                addr = self.free[o].pop(0)
                while o > order:          # 自顶向下对半分裂
                    o -= 1
                    buddy = addr + (1 << o)
                    self.free.setdefault(o, []).append(buddy)
                return addr, order
        return None

    def release(self, addr, order):
        """释放块：与伙伴合并，能合几次合几次。"""
        while order < self.order:
            buddy = addr ^ (1 << order)   # 异或低位 = 求伙伴地址
            if buddy in self.free.get(order, []):
                self.free[order].remove(buddy)
                addr = min(addr, buddy)
                order += 1
            else:
                break
        self.free.setdefault(order, []).append(addr)

    def snapshot(self):
        return {o: sorted(addrs) for o, addrs in sorted(self.free.items()) if addrs}


print("== 伙伴系统：64 单位（order 6）的完整生命周期 ==")
b = Buddy(order=6)
print(f"  初始: {b.snapshot()}")

a1, _ = b.alloc(2)
print(f"  alloc(order=2) -> 地址 {a1}，分裂出的半块进入空闲链: {b.snapshot()}")
a2, _ = b.alloc(2)
print(f"  alloc(order=2) -> 地址 {a2}")
a3, _ = b.alloc(3)
print(f"  alloc(order=3) -> 地址 {a3}   当前: {b.snapshot()}")

b.release(a1, 2)
print(f"  release({a1}, 2): 伙伴 {a1 ^ 4} 不在空闲链（已分配）-> 只挂回 order2: {b.snapshot()}")
b.release(a2, 2)
print(f"  release({a2}, 2): 伙伴 {a2 ^ 4} = {a1} 可合并 -> 升到 order3；再遇伙伴 {a3} 占用 -> 停: {b.snapshot()}")
b.release(a3, 3)
print(f"  release({a3}, 3): 连续合并直到 order6: {b.snapshot()}")
print("  全部释放后回到单一整块 —— 伙伴系统自动消除外部碎片")

print("\n== 异或求伙伴的原理 ==")
addr = 8
for o in (2, 3, 4):
    print(f"  地址 {addr:>2} 的 order{o} 伙伴 = {addr} ^ {1 << o} = {addr ^ (1 << o)}")
print("  order k 的伙伴 = 自己的地址翻转第 k 位（成对且不重叠）")

print("\n== 洞列表分配器：first/best/worst 对比 ==")


class Arena:
    def __init__(self, size=100):
        self.holes = [(0, size)]          # (起点, 大小)，按起点有序
        self.blocks = {}
        self.next_id = 1

    def malloc(self, size, mode):
        cands = [i for i, (_, h) in enumerate(self.holes) if h >= size]
        if not cands:
            return None
        if mode == "first":
            i = cands[0]
        elif mode == "best":
            i = min(cands, key=lambda x: self.holes[x][1])
        else:
            i = max(cands, key=lambda x: self.holes[x][1])
        s, h = self.holes[i]
        bid = self.next_id
        self.next_id += 1
        self.blocks[bid] = (s, size)
        self.holes[i] = (s + size, h - size) if h > size else None
        self.holes = [x for x in self.holes if x]
        return bid

    def free_block(self, bid):
        s, size = self.blocks.pop(bid)
        self.holes.append((s, size))
        self.holes.sort()
        merged = []
        for st, sz in self.holes:
            if merged and merged[-1][0] + merged[-1][1] == st:
                merged[-1] = (merged[-1][0], merged[-1][1] + sz)
            else:
                merged.append((st, sz))
        self.holes = merged

    def frag(self):
        return len(self.holes), sum(h for _, h in self.holes)


ops = [("m", 15), ("m", 25), ("m", 15), ("f", 2), ("m", 20), ("f", 1), ("m", 12)]
for mode in ("first", "best", "worst"):
    arena = Arena(100)
    ids = []
    print(f"  [{mode} 适配]")
    for op, arg in ops:
        if op == "m":
            bid = arena.malloc(arg, mode)
            ids.append(bid)
            print(f"    malloc({arg:>2}) -> 块{bid}   洞={arena.holes}")
        else:
            arena.free_block(ids[arg - 1])
            print(f"    free(块{arg})      洞={arena.holes}")
    n_holes, free_sz = arena.frag()
    print(f"    -> 结束时 {n_holes} 个洞 / 空闲 {free_sz}")
print("  best 适应倾向留下很多小碎洞；worst 适应把大洞切碎；buddy 用幂次约束绕开两者")

print("\n== 小结 ==")
for line in (
    "  伙伴系统 = 幂次分块 + 异或找伙伴 + 释放时自底向上合并",
    "  分裂/合并都是 O(log 总量)，空闲链天然按阶组织",
    "  内部碎片最多 1 倍（要 33 单位得给 64）—— 用 slab 缓存在上层弥补",
    "  下一课：把分配好的内存组织成文件系统",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给 Buddy 加 alloc 统计：总申请量、内部碎片总量（2^order - 实际需求）。
# 2. 实现 slab 缓存层：常用大小（16/32/64）预先切好对象池，池空时向 Buddy 要块。
# 3. 实现 bitmap 分配器（1 位=1 页），与 Buddy 对比 1000 次 alloc/free 的速度。
# 4. 思考：为什么伙伴系统只适合「页级」分配？应用层的 malloc 为什么不能
#    直接用它（提示：对象大小分布与内部碎片）？
