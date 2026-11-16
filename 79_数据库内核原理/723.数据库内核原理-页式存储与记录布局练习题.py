# ===== 第723课：数据库内核原理-页式存储与记录布局 =====
# 知识点：
#   - 数据库以「页 page」为 IO 基本单位（常见 4KB/8KB/16KB），不是按行读写
#   - 页内布局：页头（元数据）+ 槽位目录 slot directory + 记录区 + 空闲空间
#   - 变长记录：槽位存 (offset, length)，删除只标槽位为空，避免搬移
#   - 记录序列化：定长字段直接编码，变长字段用长度前缀；NULL 用位图标记
#   - 行溢出 / TOAST：超大字段放溢出页，主记录只留指针
#   - 本课用 bytes/bytearray 在内存模拟页，完整实现插入/读取/删除/紧凑
# 依赖：无（标准库）
import struct
from dataclasses import dataclass

PAGE_SIZE = 256
HEADER_SIZE = 8          # magic(4) + slot_count(2) + free_offset(2)


@dataclass
class Slot:
    offset: int = 0
    length: int = 0
    alive: bool = False


class Page:
    """简化页：头部 + 槽位数组（每条 4B）+ 从尾部往前的记录区。"""

    def __init__(self, size=PAGE_SIZE):
        self.buf = bytearray(size)
        self.buf[0:4] = b"PAGE"
        self.slots = []
        self.free_end = size          # 记录区从页尾往低地址长
        self._write_header()

    def _write_header(self):
        struct.pack_into("<HH", self.buf, 4, len(self.slots), self.free_end)

    def _slot_bytes(self):
        return 4 * len(self.slots)

    def insert(self, record: bytes) -> int:
        need = 4 + len(record)        # 新槽位 + 记录本身
        if HEADER_SIZE + self._slot_bytes() + need > self.free_end:
            raise ValueError("页空间不足，需要分裂或溢出页")
        self.free_end -= len(record)
        self.buf[self.free_end:self.free_end + len(record)] = record
        self.slots.append(Slot(self.free_end, len(record), True))
        self._write_header()
        self._write_slots()
        return len(self.slots) - 1

    def _write_slots(self):
        base = HEADER_SIZE
        for i, s in enumerate(self.slots):
            flag = (1 << 15) if s.alive else 0
            struct.pack_into("<HH", self.buf, base + i * 4,
                             s.offset | (0 if s.alive else 0x8000), s.length)

    def read(self, slot_id: int) -> bytes:
        s = self.slots[slot_id]
        if not s.alive:
            raise KeyError(f"槽位 {slot_id} 已删除")
        return bytes(self.buf[s.offset:s.offset + s.length])

    def delete(self, slot_id: int):
        self.slots[slot_id].alive = False     # 只标墓碑，不搬记录
        self._write_slots()

    def live_count(self):
        return sum(s.alive for s in self.slots)

    def used_bytes(self):
        return PAGE_SIZE - self.free_end + HEADER_SIZE + self._slot_bytes()

    def compact(self):
        """紧凑：丢掉死槽位，把活记录重新连续排布。"""
        live = [(i, self.read(i)) for i, s in enumerate(self.slots) if s.alive]
        self.buf = bytearray(PAGE_SIZE)
        self.buf[0:4] = b"PAGE"
        self.slots, self.free_end = [], PAGE_SIZE
        for _, rec in live:
            self.free_end -= len(rec)
            self.buf[self.free_end:self.free_end + len(rec)] = rec
            self.slots.append(Slot(self.free_end, len(rec), True))
        self._write_header(); self._write_slots()
        return len(live)


def encode_row(values, types):
    """记录编码：NULL 位图 + 定长 int(4B) / 变长 str(2B 长度 + 内容)。"""
    null_bits = 0
    for i, v in enumerate(values):
        if v is None:
            null_bits |= 1 << i
    out = bytearray(struct.pack("<H", null_bits))
    for v, t in zip(values, types):
        if v is None:
            continue
        if t == "int":
            out += struct.pack("<i", v)
        elif t == "str":
            b = v.encode("utf-8")
            out += struct.pack("<H", len(b)) + b
        else:
            raise ValueError(t)
    return bytes(out)


def decode_row(raw, types):
    (bits,) = struct.unpack_from("<H", raw, 0)
    off, vals = 2, []
    for i, t in enumerate(types):
        if bits & (1 << i):
            vals.append(None); continue
        if t == "int":
            (v,) = struct.unpack_from("<i", raw, off); off += 4; vals.append(v)
        else:
            (n,) = struct.unpack_from("<H", raw, off); off += 2
            vals.append(raw[off:off+n].decode("utf-8")); off += n
    return vals


print("== 记录编码（定长 int + 变长 str + NULL）==")
SCHEMA = ("int", "str", "int")
for row in ((1, "alice", 95), (2, "小明", None), (3, "", 0)):
    raw = encode_row(row, SCHEMA)
    print(f"  {row!r:<28} -> {len(raw):>2}B {raw.hex(' ')} -> {decode_row(raw, SCHEMA)!r}")

page = Page()
print("\n== 页内插入 ==")
rows = [(i, f"user{i}", 80 + i) for i in range(1, 6)]
for r in rows:
    sid = page.insert(encode_row(r, SCHEMA))
    print(f"  插入 {r!r:<26} -> slot={sid} free_end={page.free_end} "
          f"已用≈{page.used_bytes()}B")

print("\n== 读取与删除 ==")
print("  slot 2 =", decode_row(page.read(2), SCHEMA))
page.delete(1); page.delete(3)
print(f"  删除 slot 1,3 后: 活记录={page.live_count()} 槽位数={len(page.slots)} "
      f"free_end={page.free_end}（未回收，保持原地）")
try:
    page.read(1)
except KeyError as e:
    print("  读已删槽位:", e)

print("\n== 紧凑回收 ==")
n = page.compact()
print(f"  紧凑后活记录={n} 槽位数={len(page.slots)} free_end={page.free_end} "
      f"（空闲连续区恢复）")
print("  紧凑后数据:", [decode_row(page.read(i), SCHEMA) for i in range(n)])

print("\n== 页大小与放大效应 ==")
for ps in (4096, 8192, 16384):
    print(f"  page={ps:>6}B: 读 1 行也要 IO {ps/1024:.0f}KB；"
          f"16KB 页约放 {ps//40} 条 40B 记录")
print("  页越大顺序扫描越高效，但单行更新/内存占用更贵")

print("\n== 变长记录与溢出 ==")
big = "x" * 600
print(f"  600B 字段 > {PAGE_SIZE}B 页容量 -> 需 TOAST/溢出页，主记录只存 20B 指针")
print("  PostgreSQL 的 TOAST、MySQL 的 off-page column 都是这个思路")

print("\n== 工程要点 ==")
for line in [
    "  槽位目录让页内记录可移动而对外 rid(page,slot) 不变",
    "  删除用墓碑 + 后台 compact/VACUUM，避免每次删除都搬数据",
    "  NULL 位图比「每列一个标记字节」省空间",
    "  页头还应有 LSN、校验和、页类型（本课简化）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给页头增加 CRC32 与 LSN 字段，读取时校验完整性（第601课）。
# 2. 实现溢出页：超长字段拆成链表，主记录存首指针。
# 3. 对比「槽位目录」与「记录内部存长度」两种布局的更新代价。
# 4. 思考：为什么数据库以页而非行为单位做 IO？
