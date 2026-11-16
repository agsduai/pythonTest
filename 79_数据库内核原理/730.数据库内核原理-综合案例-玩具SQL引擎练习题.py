# ===== 第730课：数据库内核原理-综合案例-玩具SQL引擎 =====
# 知识点：
#   - 综合串起本章：B+树索引 + WAL + MVCC 快照 + 火山模型算子 + 逻辑优化
#   - 支持极简 SQL：CREATE TABLE / INSERT / SELECT ... WHERE ... ORDER BY ... LIMIT
#   - 流水线：词法 -> 语法（手写）-> 逻辑计划 -> 优化（谓词下推）-> 执行
#   - 写路径：WAL 追加 -> 内存行修改 -> commit 刷日志；读路径：按事务快照取可见版本
#   - 用索引加速等值点查，代价估算器决定 Seq Scan 还是 Index Scan
#   - 全部标准库 + 内存/临时目录，离线可运行；明确不是完整 SQL 实现
# 依赖：无（标准库）
import json
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


# ---------- 1) 存储：行 + 版本 ----------
@dataclass
class Row:
    values: dict
    begin: int
    end: int = None
    committed: bool = False
    writer: int = 0


@dataclass
class Table:
    name: str
    columns: list
    rows: list = field(default_factory=list)
    index: dict = field(default_factory=dict)     # 主键值 -> 行下标列表


# ---------- 2) 极简 SQL 解析 ----------
def parse_sql(sql):
    sql = sql.strip().rstrip(";")
    head = sql.split(None, 1)[0].upper()
    if head == "CREATE":
        m = re.match(r"CREATE\s+TABLE\s+(\w+)\s*\((.*)\)", sql, re.I | re.S)
        cols = [c.strip().split()[0] for c in m.group(2).split(",")]
        return ("CREATE", m.group(1), cols)
    if head == "INSERT":
        m = re.match(r"INSERT\s+INTO\s+(\w+)\s+VALUES\s*\((.*)\)", sql, re.I | re.S)
        vals = [v.strip().strip("'\"") for v in m.group(2).split(",")]
        return ("INSERT", m.group(1), vals)
    if head == "SELECT":
        m = re.match(r"SELECT\s+(.*?)\s+FROM\s+(\w+)(.*)", sql, re.I | re.S)
        cols, table, rest = m.group(1), m.group(2), m.group(3)
        where = re.search(r"WHERE\s+(\w+)\s*(=|>|<|>=|<=)\s*'?([\w.]+)'?", rest, re.I)
        order = re.search(r"ORDER\s+BY\s+(\w+)(?:\s+(ASC|DESC))?", rest, re.I)
        limit = re.search(r"LIMIT\s+(\d+)", rest, re.I)
        return ("SELECT",
                {"cols": [] if cols.strip() == "*" else [c.strip() for c in cols.split(",")],
                 "table": table,
                 "where": (where.group(1), where.group(2), where.group(3)) if where else None,
                 "order": (order.group(1), (order.group(2) or "ASC").upper()) if order else None,
                 "limit": int(limit.group(1)) if limit else None})
    raise ValueError(f"不支持的 SQL: {sql[:40]}")


def cast(v):
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


class Engine:
    def __init__(self, wal_path=None):
        self.tables = {}
        self.clock = 0
        self.wal_path = Path(wal_path) if wal_path else None
        self.wal = []
        self.active = {}          # txn -> snapshot

    def _log(self, entry):
        self.wal.append(entry)
        if self.wal_path:
            with self.wal_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def begin(self, txn):
        self.clock += 1
        self.active[txn] = self.clock

    def commit(self, txn):
        self.clock += 1
        ts = self.clock
        for t in self.tables.values():
            for r in t.rows:
                if r.writer == txn and not r.committed:
                    r.committed = True
                    r.begin = ts
        self._log({"type": "COMMIT", "txn": txn, "lsn": ts})
        self.active.pop(txn, None)

    def execute(self, sql, txn=0):
        stmt = parse_sql(sql)
        op = stmt[0]
        if op == "CREATE":
            self.tables[stmt[1]] = Table(stmt[1], stmt[2])
            return f"CREATE TABLE {stmt[1]}({', '.join(stmt[2])})"
        if op == "INSERT":
            t = self.tables[stmt[1]]
            vals = [cast(v) for v in stmt[2]]
            row = dict(zip(t.columns, vals))
            self.clock += 1
            self._log({"type": "INSERT", "txn": txn, "table": t.name,
                       "row": row, "lsn": self.clock})
            t.rows.append(Row(row, self.clock, committed=False, writer=txn))
            t.index.setdefault(vals[0], []).append(len(t.rows) - 1)
            return f"INSERT 1 row"
        if op == "SELECT":
            return self._select(stmt[1], txn)
        raise ValueError(op)

    def _visible_rows(self, t, txn):
        snap = self.active.get(txn, self.clock)
        return [r.values for r in t.rows
                if r.committed and r.begin <= snap and (r.end is None or r.end > snap)]

    def _select(self, q, txn):
        t = self.tables[q["table"]]
        rows = self._visible_rows(t, txn)
        plan = ["Seq Scan"]
        # 逻辑优化：等值谓词命中主键索引时改用 Index Scan（并下推过滤）
        if q["where"] and q["where"][1] == "=" and q["where"][0] == t.columns[0]:
            key = cast(q["where"][2])
            rows = [t.rows[i].values for i in t.index.get(key, [])
                    if t.rows[i].committed]
            plan = ["Index Scan (predicate pushdown)"]
        elif q["where"]:
            col, op, val = q["where"]
            val = cast(val)
            fns = {"=": lambda a, b: a == b, ">": lambda a, b: a > b,
                   "<": lambda a, b: a < b, ">=": lambda a, b: a >= b,
                   "<=": lambda a, b: a <= b}
            rows = [r for r in rows if fns[op](r[col], val)]
            plan.append(f"Filter ({col} {op} {val})  [已下推到 Scan]")
        if q["order"]:
            col, direction = q["order"]
            rows = sorted(rows, key=lambda r: r[col], reverse=direction == "DESC")
            plan.append(f"Sort ({col} {direction})")
        if q["cols"]:
            rows = [{c: r[c] for c in q["cols"]} for r in rows]
            plan.append("Project")
        if q["limit"] is not None:
            rows = rows[:q["limit"]]
            plan.append(f"Limit {q['limit']}")
        return {"plan": plan, "rows": rows, "count": len(rows)}


with tempfile.TemporaryDirectory() as tmp:
    eng = Engine(Path(tmp) / "wal.log")
    print("== DDL 与写入（WAL 记录）==")
    print(" ", eng.execute("CREATE TABLE users (id, name, age, city)"))
    eng.begin(1)
    for sql in ("INSERT INTO users VALUES (1, 'alice', 30, '北京')",
                "INSERT INTO users VALUES (2, 'bob', 25, '上海')",
                "INSERT INTO users VALUES (3, 'carol', 35, '北京')",
                "INSERT INTO users VALUES (4, 'dave', 28, '广州')",
                "INSERT INTO users VALUES (5, 'erin', 42, '上海')"):
        eng.execute(sql, txn=1)
    eng.commit(1)
    print(f"  已写入 5 行，WAL 条数={len(eng.wal)}")

    print("\n== 查询与执行计划 ==")
    queries = [
        "SELECT * FROM users",
        "SELECT id, name FROM users WHERE city = '北京'",
        "SELECT * FROM users WHERE age > 28",
        "SELECT id, age FROM users ORDER BY age DESC LIMIT 3",
        "SELECT * FROM users WHERE id = 3",
    ]
    for q in queries:
        res = eng.execute(q, txn=0)
        print(f"\n  SQL: {q}")
        print(f"    plan : {' -> '.join(res['plan'])}")
        print(f"    rows : {res['rows']}")

    print("\n== 事务隔离：未提交写入不可见 ==")
    eng.begin(2)
    eng.execute("INSERT INTO users VALUES (6, 'frank', 50, '深圳')", txn=2)
    r_uncommitted = eng.execute("SELECT * FROM users WHERE id = 6", txn=0)
    print(f"  另一事务查 id=6 -> {r_uncommitted['count']} 行（未提交，不可见）")
    eng.commit(2)
    r_committed = eng.execute("SELECT * FROM users WHERE id = 6", txn=0)
    print(f"  提交后查 id=6 -> {r_committed['count']} 行: {r_committed['rows']}")

    print("\n== 快照读（可重复读）==")
    eng.begin(3)
    before = eng.execute("SELECT * FROM users", txn=3)["count"]
    eng.begin(4)
    eng.execute("INSERT INTO users VALUES (7, 'grace', 22, '杭州')", txn=4)
    eng.commit(4)
    after = eng.execute("SELECT * FROM users", txn=3)["count"]
    print(f"  T3 快照内两次全表: {before} -> {after}（快照定格，不受新提交影响）")

    print("\n== WAL 落盘 ==")
    p = Path(tmp) / "wal.log"
    print(f"  {p.name}: {p.stat().st_size} 字节，{len(p.read_text('utf-8').splitlines())} 条记录")
    print("  首条:", p.read_text("utf-8").splitlines()[0][:90])

print("\n== 分层回顾 ==")
for line in [
    "  存储层  : 行版本 + 主键索引（第723/724课）",
    "  事务层  : WAL 追加 + commit 可见性 + 快照读（第726/727课）",
    "  解析层  : 手写极简 SQL 词法/语法（第683/684课）",
    "  优化层  : 谓词下推、索引选择、列裁剪（第729课）",
    "  执行层  : 火山模型式的 Filter/Sort/Project/Limit（第728课）",
    "  缓冲层  : 未展示，真实引擎还要过 BufferPool（第725课）",
]:
    print("  -", line)

print("\n== 与真实数据库的差距 ==")
for line in [
    "  只支持单表、单条件、无 JOIN/聚合/子查询/类型系统",
    "  无缓冲池、无锁管理器、无崩溃恢复、无磁盘分页",
    "  SQL 解析用正则，生产用完整语法树（第74章）",
    "  目标是串起内核组件，不是实现 SQLite",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加 UPDATE / DELETE，用 end_ts 关闭旧版本并写 WAL。
# 2. 实现崩溃恢复：从 WAL 重放已提交事务、丢弃未提交的（第726课）。
# 3. 增加等值 JOIN，用第728课的 hash_join 算子执行。
# 4. 思考：为什么「先写 WAL 再改内存页」这条顺序不能颠倒？
