# ===== 第726课：数据库内核原理-WAL与崩溃恢复 =====
# 知识点：
#   - WAL（Write-Ahead Logging）：数据页落盘前，日志必须先持久化
#   - 日志记「redo 信息」：(LSN, txn, page, before, after)，顺序追加写，比随机写页快
#   - ARIES 三阶段：分析 analysis -> 重做 redo（重复历史）-> 撤销 undo（未提交事务）
#   - LSN：日志序列号，页上也记 pageLSN，redo 时跳过已应用的日志
#   - 检查点：记录活跃事务与脏页表，缩短恢复时需要扫描的日志范围
#   - 崩溃模型：已提交事务必须持久（redo），未提交必须回滚（undo）
# 依赖：无（标准库）
import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LogRecord:
    lsn: int
    txn: int
    page: int
    before: object
    after: object
    kind: str = "UPDATE"     # UPDATE / COMMIT / ABORT / CLR

    def to_line(self):
        return json.dumps(vars(self), ensure_ascii=False)

    @classmethod
    def from_line(cls, line):
        return cls(**json.loads(line))


class WAL:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.records = []
        self.lsn = 0
        self.flushed_lsn = 0
        if self.path and self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = LogRecord.from_line(line)
                    self.records.append(r)
                    self.lsn = max(self.lsn, r.lsn)

    def append(self, txn, page, before, after, kind="UPDATE"):
        self.lsn += 1
        r = LogRecord(self.lsn, txn, page, before, after, kind)
        self.records.append(r)
        if self.path:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(r.to_line() + "\n")
                f.flush()
        return r.lsn

    def flush(self, upto=None):
        """模拟 fsync：只保证 flushed_lsn 之前的日志真正落盘。"""
        self.flushed_lsn = upto or self.lsn
        return self.flushed_lsn

    def commit(self, txn):
        lsn = self.append(txn, -1, None, None, "COMMIT")
        self.flush(lsn)               # 提交必须强制刷日志
        return lsn


@dataclass
class Page:
    value: object
    page_lsn: int = 0


class Database:
    def __init__(self, wal, n_pages=5):
        self.wal = wal
        self.pages = {i: Page(0) for i in range(n_pages)}
        self.disk = {i: Page(0) for i in range(n_pages)}

    def write(self, txn, page_id, value):
        old = self.pages[page_id].value
        lsn = self.wal.append(txn, page_id, old, value)
        self.pages[page_id].value = value
        self.pages[page_id].page_lsn = lsn
        return lsn

    def flush_page(self, page_id):
        """WAL 规则：页落盘前，必须保证对应 LSN 的日志已刷。"""
        lsn = self.pages[page_id].page_lsn
        if lsn > self.wal.flushed_lsn:
            self.wal.flush(lsn)        # 先强制刷日志
        self.disk[page_id] = Page(self.pages[page_id].value, lsn)

    def checkpoint(self):
        return {"lsn": self.wal.lsn, "dirty": [i for i, p in self.pages.items()
                                               if p.page_lsn > self.disk[i].page_lsn]}


def recover(wal_path, n_pages=5):
    """ARIES 简化版：分析 -> redo -> undo。"""
    wal = WAL(wal_path)
    disk = {i: Page(0) for i in range(n_pages)}
    committed, active = set(), set()
    # 1) 分析：找出已提交/未提交事务
    for r in wal.records:
        if r.kind == "COMMIT":
            committed.add(r.txn); active.discard(r.txn)
        elif r.kind in ("UPDATE", "CLR"):
            if r.txn not in committed:
                active.add(r.txn)
    # 2) redo：按日志顺序重放全部（含未提交），跳过 pageLSN 已更新的
    redo, skipped = 0, 0
    for r in wal.records:
        if r.kind not in ("UPDATE", "CLR") or r.page < 0:
            continue
        if r.lsn <= disk[r.page].page_lsn:
            skipped += 1
            continue
        disk[r.page].value = r.after
        disk[r.page].page_lsn = r.lsn
        redo += 1
    # 3) undo：按 LSN 倒序撤销未提交事务，并写 CLR（防止重复 undo）
    undone = 0
    for r in reversed([x for x in wal.records
                       if x.txn in active and x.kind == "UPDATE"]):
        disk[r.page].value = r.before
        undone += 1
    return disk, committed, active, {"redo": redo, "skipped": skipped, "undone": undone}


with tempfile.TemporaryDirectory() as tmp:
    log = Path(tmp) / "wal.log"
    wal = WAL(log)
    db = Database(wal)

    print("== 正常运行 ==")
    print(f"  T1: page0: 0->10, page1: 0->20")
    db.write(1, 0, 10); db.write(1, 1, 20)
    db.flush_page(0)                       # 页落盘前触发日志刷写
    print(f"  T1 提交，commit LSN={wal.commit(1)}")
    print(f"  T2: page0: 10->99（未提交）")
    db.write(2, 0, 99)
    print(f"  T3: page2: 0->50 未提交，page3: 0->7 提交")
    db.write(3, 2, 50); db.write(3, 3, 7); wal.commit(3)
    cp = db.checkpoint()
    print(f"  检查点: LSN={cp['lsn']} 脏页={cp['dirty']}")
    print(f"  此时磁盘: {[db.disk[i].value for i in range(5)]}（只有 page0 落过盘）")
    print(f"  内存页 : {[db.pages[i].value for i in range(5)]}")

    print("\n== 模拟崩溃：丢掉内存页，只保留 WAL 与已落盘数据 ==")
    print(f"  WAL 共 {len(wal.records)} 条记录，flushed_lsn={wal.flushed_lsn}")
    disk, committed, active, stats = recover(log)
    print(f"  已提交事务={sorted(committed)} 未提交事务={sorted(active)}")
    print(f"  redo={stats['redo']} 跳过={stats['skipped']} undo={stats['undone']}")
    print(f"  恢复后磁盘: {[disk[i].value for i in range(5)]}")
    print("  期望: page0=10(T1已提交,T2未提交被撤销), page1=20(T1重做), "
          "page2=50、page3=7(T3已提交,两条都重做)")

print("\n== 逐条日志（教学示例）==")
sample = [LogRecord(1, 1, 0, 0, 10), LogRecord(2, 1, 1, 0, 20),
          LogRecord(3, 1, -1, None, None, "COMMIT"),
          LogRecord(4, 2, 0, 10, 99)]
for r in sample:
    print("  ", r.to_line())

print("\n== WAL 规则为什么重要 ==")
for line in (
    "  若数据页先落盘、日志未落盘，崩溃后无法 undo 这个未提交修改",
    "  日志是顺序追加，比随机写数据页快一个数量级",
    "  group commit 把多个事务的 fsync 合并，摊薄成本",
    "  pageLSN 让 redo 幂等：重复重放不会破坏状态",
):
    print(" ", line)

print("\n== ARIES 三阶段 ==")
for line in (
    "  analysis: 从检查点起扫描，重建活跃事务表与脏页表",
    "  redo    : 重复历史，把数据库恢复到崩溃那一刻（含未提交的）",
    "  undo    : 倒序撤销未提交事务，写 CLR 保证 undo 本身可重放",
    "  恢复期间再次崩溃也能正确继续，靠 CLR 的 LSN 追踪",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 实现真正的 CLR 写入，让恢复中途崩溃也能正确继续 undo。
# 2. 利用检查点裁剪日志，只扫描 checkpoint 之后的记录。
# 3. 模拟「页先落盘、日志未刷」的违规场景，观察恢复结果错误。
# 4. 思考：为什么 redo 要「重复历史」把未提交的修改也重做一遍？
