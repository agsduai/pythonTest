# ===== 第727课：数据库内核原理-事务隔离与MVCC =====
# 知识点：
#   - ACID：原子性、一致性、隔离性、持久性；隔离级别权衡并发与异常
#   - 异常：脏读、不可重复读、幻读、丢失更新、写偏斜
#   - 隔离级别：读未提交 / 读已提交 / 可重复读 / 可串行化
#   - MVCC：每行存多个版本 (begin_ts, end_ts, value)，读按快照取可见版本
#   - 快照读不加锁，写写仍要冲突检测（first committer wins）
#   - 本课用「版本号 + 版本链」模拟 MVCC，复现各隔离级别下的读现象
# 依赖：无（标准库）
from dataclasses import dataclass, field


@dataclass
class Version:
    value: object
    begin: int          # 创建它的事务时间戳
    end: int = None     # 被删除/替换的事务时间戳（None=当前有效）
    writer: int = 0
    committed: bool = False    # 未提交版本对其他事务不可见


class MVCC:
    def __init__(self):
        self.rows = {}       # key -> [Version, ...]（新版本在前）
        self.clock = 0
        self.active = {}     # txn -> snapshot_ts

    def begin(self, txn, isolation="REPEATABLE READ"):
        self.clock += 1
        ts = self.clock
        # 读已提交：每次读取最新快照；可重复读：begin 时定格
        self.active[txn] = {"ts": ts, "iso": isolation, "write_set": set()}
        return ts

    def _snapshot(self, txn):
        info = self.active[txn]
        if info["iso"] == "READ COMMITTED":
            return self.clock
        return info["ts"]           # 可重复读 / 可串行化用 begin 时快照

    def read(self, txn, key):
        snap = self._snapshot(txn)
        for v in self.rows.get(key, []):
            # 可见条件：已提交 + begin <= snap 且 (end is None or end > snap)
            if (v.committed and v.begin <= snap and
                    (v.end is None or v.end > snap)):
                return v.value
        return None

    def write(self, txn, key, value):
        self.active[txn]["write_set"].add(key)
        self.clock += 1
        ts = self.clock
        chain = self.rows.setdefault(key, [])
        # 未提交版本先挂上，旧版本仍对快照可见；commit 时才关闭旧版本
        chain.insert(0, Version(value, ts, None, txn, committed=False))

    def commit(self, txn):
        self.clock += 1
        ts = self.clock
        for chain in self.rows.values():
            for v in chain:
                if v.writer == txn and not v.committed:
                    v.committed = True
                    v.begin = ts            # 可见起点取提交时刻
                    # 关闭同 key 里更早的已提交版本
                    for older in chain:
                        if older is not v and older.end is None and older.committed:
                            older.end = ts
        self.active.pop(txn, None)

    def visible_chain(self, key):
        return [(v.value, v.begin, v.end, v.committed) for v in self.rows.get(key, [])]


def scenario(name, iso):
    db = MVCC()
    db.begin(0, iso); db.write(0, "x", 100); db.commit(0)   # 初始值
    db.begin(1, iso)
    r1 = db.read(1, "x")
    db.begin(2, iso); db.write(2, "x", 200); db.commit(2)
    r2 = db.read(1, "x")                                    # T1 再读
    db.commit(1)
    return r1, r2, r1 == r2

print("== 不可重复读：同一事务两次读同一行 ==")
for iso in ("READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"):
    a, b, same = scenario("demo", iso)
    print(f"  {iso:<18}: 第一次={a} 第二次={b} 可重复={same}")
print("  读已提交允许不可重复读；可重复读/串行化靠快照定格")

print("\n== 脏读（读未提交才会发生）==")
db = MVCC()
db.begin(0); db.write(0, "x", 100); db.commit(0)      # 已提交旧值
db.begin(1, "READ COMMITTED"); db.write(1, "x", 999)  # 未提交
db.begin(2, "READ COMMITTED")
print(f"  T1 未提交写入 999，T2 读到: {db.read(2, 'x')!r}（应为旧值 100，不读脏）")
db.commit(1)
print(f"  T1 提交后，新事务读到: {db.read(2, 'x')!r}")
db.commit(2)

print("\n== 版本链与快照可见性 ==")
db2 = MVCC()
db2.begin(0); db2.write(0, "k", "v1"); db2.commit(0)
db2.begin(1, "REPEATABLE READ")            # 快照 ts 定格
print(f"  T1 快照读: {db2.read(1, 'k')!r}")
db2.begin(2); db2.write(2, "k", "v2"); db2.commit(2)
db2.begin(3); db2.write(3, "k", "v3"); db2.commit(3)
print(f"  之后被改成 v2、v3，T1 再读仍是: {db2.read(1, 'k')!r}")
print("  版本链:", db2.visible_chain("k"))
print("  每个版本带 [begin,end) 区间，快照落在哪个区间就看到哪个值")

print("\n== 丢失更新与写写冲突 ==")
db3 = MVCC()
db3.begin(0); db3.write(0, "bal", 100); db3.commit(0)
db3.begin(1); db3.begin(2)
a, b = db3.read(1, "bal"), db3.read(2, "bal")
print(f"  T1、T2 同时读到余额 = {a}")
# 无冲突检测：两次基于同一旧值的更新，后写直接覆盖前写
db3.write(1, "bal", a + 50); db3.commit(1)
db3.write(2, "bal", b + 30); db3.commit(2)
db3.begin(3)
print(f"  无检测时最终余额 = {db3.read(3, 'bal')}（期望 180，实际丢了 T1 的 +50）")
print("  有 first-committer-wins / 行锁时，T2 会检测到冲突并中止重试")

print("\n== 幻读与可串行化 ==")
for line in (
    "  幻读: 同一事务里按条件范围查询，别的事务插入了符合条件的新行",
    "  可重复读（快照）挡不住幻读：新行的 begin_ts 也在快照之后，本应看不见",
    "  但「谓词锁 / SSI」才能防写偏斜，SQLite 之外的多数引擎需显式 SERIALIZABLE",
    "  PostgreSQL SERIALIZABLE 用 SSI 检测危险结构并中止其中一个事务",
):
    print(" ", line)

print("\n== 隔离级别速查 ==")
print(f"  {'级别':<20}{'脏读':<8}{'不可重复读':<13}{'幻读':<8}{'实现'}")
for row in (("READ UNCOMMITTED", "可能", "可能", "可能", "无快照"),
            ("READ COMMITTED", "不可能", "可能", "可能", "语句级快照"),
            ("REPEATABLE READ", "不可能", "不可能", "可能*", "事务级快照"),
            ("SERIALIZABLE", "不可能", "不可能", "不可能", "锁/SSI")):
    print(f"  {row[0]:<20}{row[1]:<8}{row[2]:<13}{row[3]:<8}{row[4]}")

print("\n== MVCC 工程要点 ==")
for line in [
    "  旧版本不能立刻删：可能还有长事务的快照要读它（VACUUM / purge）",
    "  长事务会拖住版本回收，导致表膨胀，要监控 oldest xmin",
    "  写写冲突仍需锁或乐观检测，MVCC 只解决读写阻塞",
    "  索引也要存版本信息（或回表判断可见性），否则索引读会看到幽灵行",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「读已提交」的语句级快照：同一事务内每条语句刷新一次 ts。
# 2. 加入 first-committer-wins 检测，演示上面丢失更新被阻止。
# 3. 实现 VACUUM：删除所有 end_ts < min(active snapshots) 的旧版本。
# 4. 思考：为什么 MVCC 能让「读不阻塞写、写不阻塞读」？
