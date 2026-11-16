# ===== 第440课：SQLite高级-事务进阶与并发 =====
# 知识点：
#   - 保存点 SAVEPOINT：事务内部再分小事务，可局部回滚
#   - WAL 模式：读写不互相阻塞，适合“多读一写”场景
#   - busy_timeout：遇到锁时等一会儿再报错，而不是立刻失败
#   - `with conn` 只负责提交/回滚，不会关闭连接（第407课踩过的坑）
#   - 并发写入的真相：SQLite 同一时刻只允许一个写者（写锁）
# 依赖：无（sqlite3 内置）

import sqlite3
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    db_path = Path(tmp) / "tx.db"

    # isolation_level=None：关闭 Python 的隐式事务，改为手动控制 BEGIN/COMMIT
    conn = sqlite3.connect(db_path, isolation_level=None, timeout=5)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 3000")
    conn.execute("CREATE TABLE account (name TEXT PRIMARY KEY, balance REAL)")
    conn.execute("INSERT INTO account VALUES ('小明', 1000), ('小红', 500)")
    print("journal_mode =", conn.execute("PRAGMA journal_mode").fetchone()[0])

    # ---- 1. 保存点：局部回滚 ----
    print("\n== SAVEPOINT 局部回滚 ==")
    conn.execute("BEGIN")
    conn.execute("UPDATE account SET balance = balance - 100 WHERE name = '小明'")
    conn.execute("SAVEPOINT transfer")
    conn.execute("UPDATE account SET balance = balance + 100 WHERE name = '小红'")
    print("  保存点内余额：", [tuple(r) for r in conn.execute("SELECT * FROM account")])

    conn.execute("ROLLBACK TO transfer")        # 只撤销“加钱”这一步
    conn.execute("RELEASE transfer")
    print("  回滚到保存点后：", [tuple(r) for r in conn.execute("SELECT * FROM account")])
    conn.execute("COMMIT")
    print("  提交后：", [tuple(r) for r in conn.execute("SELECT * FROM account")])

    # ---- 2. 写冲突：第二个写者会等待，超时报 locked ----
    print("\n== 并发写：同一时刻只有一个写者 ==")
    conn1 = sqlite3.connect(db_path, isolation_level=None, timeout=0.2)
    conn2 = sqlite3.connect(db_path, isolation_level=None, timeout=0.2)
    conn1.execute("PRAGMA busy_timeout = 200")
    conn2.execute("PRAGMA busy_timeout = 200")

    conn1.execute("BEGIN IMMEDIATE")            # 立刻拿写锁
    conn1.execute("UPDATE account SET balance = balance + 1 WHERE name = '小明'")
    try:
        conn2.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError as exc:
        print("  第二个写者被阻塞：", exc)
    conn1.execute("COMMIT")

    # 释放后重试成功
    conn2.execute("BEGIN IMMEDIATE")
    conn2.execute("UPDATE account SET balance = balance + 2 WHERE name = '小明'")
    conn2.execute("COMMIT")
    print("  锁释放后重试成功")

    # ---- 3. WAL 下读写不互斥 ----
    print("\n== WAL：读不阻塞写 ==")
    reader = sqlite3.connect(db_path)
    writer = sqlite3.connect(db_path, isolation_level=None, timeout=1)
    print("  读连接看到：", reader.execute(
        "SELECT balance FROM account WHERE name='小明'").fetchone()[0])

    writer.execute("BEGIN IMMEDIATE")
    writer.execute("UPDATE account SET balance = balance + 100 WHERE name = '小明'")
    # 写事务未提交时，读连接仍能读旧快照
    print("  写未提交时读：", reader.execute(
        "SELECT balance FROM account WHERE name='小明'").fetchone()[0])
    writer.execute("COMMIT")
    print("  提交后读到：", reader.execute(
        "SELECT balance FROM account WHERE name='小明'").fetchone()[0])

    # ---- 4. 禁用 WAL 对比（可选）----
    print("\n== 事务使用清单 ==")
    for item in [
        "批量导入：BEGIN → 多次 INSERT → 每 N 条 COMMIT（第306课）",
        "转账：BEGIN → 扣款+到账 → 校验 → COMMIT/ROLLBACK（第208课）",
        "分步操作：SAVEPOINT 局部回滚，不影响外层",
        "并发读写：PRAGMA journal_mode=WAL + busy_timeout",
        "长事务：尽量短，避免长时间持锁",
    ]:
        print("  -", item)

    reader.close()
    writer.close()
    conn.close()
    conn1.close()
    conn2.close()

# ===== 练习题 =====
# 1. 模拟“批量插入 1 万条，每 1000 条一个保存点”，中途失败只回滚最后一批。
# 2. 用 PRAGMA journal_mode 在 DELETE/WAL 间切换，观察文件差异。
# 3. 写一个 with_transaction(conn) 上下文管理器，自动 BEGIN/COMMIT/ROLLBACK。
# 4. 思考：为什么 SQLite 不适合“大量并发写”的服务？
