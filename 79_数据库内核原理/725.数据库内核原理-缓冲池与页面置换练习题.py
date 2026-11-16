# ===== 第725课：数据库内核原理-缓冲池与页面置换 =====
# 知识点：
#   - 缓冲池 buffer pool：把磁盘页缓存在内存，避免每次访问都做 IO
#   - 页表 page table：page_id -> frame，配合 pin count 防止换出「正在用」的页
#   - 脏页 dirty：被修改过的页，换出/检查点时必须先写回磁盘
#   - 置换策略：FIFO / LRU / Clock / LRU-K；数据库常用 Clock 或 LRU-K 抗扫描污染
#   - 命中率与「局部性」：顺序扫描会把 LRU 冲干净，故需要抗污染策略
#   - 本课用「磁盘=dict，内存=OrderedDict」模拟，统计命中率与写回次数
# 依赖：无（标准库）
from collections import OrderedDict
from dataclasses import dataclass, field


@dataclass
class Frame:
    page_id: int
    data: str
    dirty: bool = False
    pin: int = 0
    ref: int = 0            # Clock 用引用位


class Disk:
    def __init__(self, n_pages=50):
        self.pages = {i: f"page-{i:03d}" for i in range(n_pages)}
        self.reads = self.writes = 0

    def read(self, pid):
        self.reads += 1
        return self.pages[pid]

    def write(self, pid, data):
        self.writes += 1
        self.pages[pid] = data


class BufferPool:
    def __init__(self, capacity, disk, policy="LRU"):
        self.cap, self.disk, self.policy = capacity, disk, policy
        self.frames = OrderedDict()     # pid -> Frame（LRU 顺序）
        self.clock_hand = 0
        self.hits = self.misses = 0

    def _evict(self):
        if self.policy == "FIFO":
            pid = next(iter(self.frames))
        elif self.policy == "LRU":
            pid = next(iter(self.frames))
        else:                            # Clock：找 ref==0 的页换出
            keys = list(self.frames)
            while True:
                pid = keys[self.clock_hand % len(keys)]
                f = self.frames[pid]
                if f.pin > 0:
                    self.clock_hand += 1
                    continue
                if f.ref == 0:
                    break
                f.ref = 0
                self.clock_hand += 1
        f = self.frames.pop(pid)
        if f.dirty:
            self.disk.write(pid, f.data)
        return pid

    def get(self, pid):
        if pid in self.frames:
            self.hits += 1
            f = self.frames[pid]
            if self.policy == "LRU":
                self.frames.move_to_end(pid)
            f.ref = 1
            f.pin += 1
            return f
        self.misses += 1
        if len(self.frames) >= self.cap:
            self._evict()
        f = Frame(pid, self.disk.read(pid), pin=1, ref=1)
        self.frames[pid] = f
        return f

    def put(self, pid, data):
        f = self.get(pid)
        f.data = data
        f.dirty = True
        f.pin = max(0, f.pin - 1)
        return f

    def unpin(self, pid):
        if pid in self.frames:
            self.frames[pid].pin = max(0, self.frames[pid].pin - 1)

    def flush_all(self):
        for pid, f in self.frames.items():
            if f.dirty:
                self.disk.write(pid, f.data)
                f.dirty = False

    def stats(self):
        total = self.hits + self.misses
        return {"hits": self.hits, "misses": self.misses,
                "hit_rate": self.hits / total if total else 0,
                "disk_reads": self.disk.reads, "disk_writes": self.disk.writes}


def workload(pool, accesses):
    for i, pid in enumerate(accesses):
        f = pool.get(pid)
        if i % 3 == 0:                # 1/3 的访问是写
            pool.put(pid, f"modified-{pid}-{i}")
        pool.unpin(pid)


print("== 三种策略的命中率（容量=4）==")
# 局部性访问 + 一次全表扫描污染
accesses = [1,2,3,1,2,1,3] + list(range(10, 20)) + [1,2,3,1,2]
for policy in ("FIFO", "LRU", "Clock"):
    d = Disk(50)
    p = BufferPool(4, d, policy)
    workload(p, accesses)
    s = p.stats()
    print(f"  {policy:<6}: 命中率={s['hit_rate']:.1%} "
          f"读IO={s['disk_reads']} 写回={s['disk_writes']}")
print("  中段顺序扫描会把热页挤出缓存，这就是「缓冲池污染」")

print("\n== 容量对命中率的影响（LRU，纯局部性）==")
hot = [1,2,3,4,1,2,3,4,1,2,3,4,5,1,2,3,4,1,2] * 3
for cap in (2, 3, 4, 5, 8):
    d = Disk(20); p = BufferPool(cap, d, "LRU")
    workload(p, hot)
    print(f"  capacity={cap}: 命中率={p.stats()['hit_rate']:.1%}")
print("  容量达到工作集大小后，命中率跃升并趋于平稳")

print("\n== 脏页与写回 ==")
d = Disk(10); p = BufferPool(3, d, "LRU")
for pid in (1, 2, 3):
    p.put(pid, f"new-{pid}"); p.unpin(pid)
print(f"  写 3 页后: 磁盘写入={d.writes}（未换出，尚未落盘）")
p.get(4); p.unpin(4)                 # 触发换出
print(f"  换出 1 个脏页后: 磁盘写入={d.writes}（先写回再读入）")
p.flush_all()
print(f"  flush_all 后: 磁盘写入={d.writes}，剩余脏页="
      f"{sum(f.dirty for f in p.frames.values())}")

print("\n== pin 保护 ==")
d = Disk(10); p = BufferPool(2, d, "LRU")
f = p.get(1)                         # pin=1
p.get(2)
print(f"  page1 pin={p.frames[1].pin}（仍在使用中，Clock 不会换出它）")
p.unpin(1)
print(f"  unpin 后 pin={p.frames[1].pin}")

print("\n== 检查点 checkpoint ==")
for line in (
    "  定期把脏页刷盘并记录 LSN，崩溃恢复只需重放之后的 WAL（第726课）",
    "  刷太平: IO 抖动大；刷太疏: 恢复时间长",
    "  PostgreSQL 用 bgwriter + checkpoint_timeout + max_wal_size 平衡",
):
    print(" ", line)

print("\n== 策略对比 ==")
print(f"  {'策略':<10}{'实现':<16}{'抗扫描污染':<14}{'典型'}")
for row in (("FIFO", "队列", "差", "教学基线"),
            ("LRU", "链表/哈希", "差", "通用缓存"),
            ("Clock", "环+引用位", "中", "MySQL InnoDB"),
            ("LRU-K", "历史访问次数", "好", "PostgreSQL")):
    print(f"  {row[0]:<10}{row[1]:<16}{row[2]:<14}{row[3]}")

print("\n== 工程要点 ==")
for line in [
    "  页在使用中必须 pin，否则被换出会读到别人的数据",
    "  预读 prefetch 利用顺序访问局部性，把后续页提前载入",
    "  多实例缓冲池 + 共享内存要考虑并发 latch，而非普通 dict",
    "  命中率不是唯一指标，还要看脏页比例与检查点抖动",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 LRU-K（记录最近第 K 次访问时间），验证抗扫描污染效果。
# 2. 增加预取：检测到连续 3 次顺序访问后提前载入后续页。
# 3. 给 Clock 增加「脏页优先/延后」的细化策略，观察写回次数变化。
# 4. 思考：为什么一次大表全扫描会毁掉 LRU 缓存，而 Clock 相对好一些？
