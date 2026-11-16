# ===== 第441课：SQLite高级-备份与数据库迁移 =====
# 知识点：
#   - conn.backup(dst)：在线备份，不用停服务
#   - conn.iterdump()：导出 SQL 文本，便于审查/迁移到其他库
#   - PRAGMA user_version：在库里存“模式版本号”，迁移脚本据此判断
#   - 迁移套路：读版本 → 按版本逐步执行 ALTER/CREATE → 更新版本
#   - 迁移前必须先备份：改表失败时可以回滚到文件
#   - 与第278课“文件备份”的区别：这里是数据库级别的逻辑备份
# 依赖：无（sqlite3 内置）

import sqlite3
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    db_path = tmp / "app.db"

    # ---- 1. 建库（模式版本 1）----
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA user_version = 1")
    conn.execute("CREATE TABLE user (id INTEGER PRIMARY KEY, name TEXT)")
    conn.executemany("INSERT INTO user (name) VALUES (?)", [("小明",), ("小红",)])
    conn.commit()
    print("初始版本：", conn.execute("PRAGMA user_version").fetchone()[0])
    print("用户：", [tuple(r) for r in conn.execute("SELECT * FROM user")])

    # ---- 2. 在线备份 ----
    backup_path = tmp / "app_backup.db"
    dst = sqlite3.connect(backup_path)
    conn.backup(dst)                      # 目标连接：完整的数据库副本
    dst.close()
    print(f"\n备份文件：{backup_path.name}（{backup_path.stat().st_size} 字节）")

    check = sqlite3.connect(backup_path)
    print("备份中用户数：", check.execute("SELECT COUNT(*) FROM user").fetchone()[0])
    print("备份中版本：", check.execute("PRAGMA user_version").fetchone()[0])
    check.close()

    # ---- 3. 导出 SQL 文本（iterdump）----
    dump_path = tmp / "app_dump.sql"
    with open(dump_path, "w", encoding="utf-8") as f:
        for line in conn.iterdump():
            f.write(line + "\n")
    print(f"\nSQL 导出：{dump_path.name}（{dump_path.stat().st_size} 字节）")
    print("前 4 行：")
    for line in dump_path.read_text(encoding="utf-8").splitlines()[:4]:
        print("  ", line)

    # ---- 4. 迁移：v1 → v2 增加 email 列 ----
    print("\n== 迁移 v1 → v2 ==")
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version == 1:
        conn.execute("ALTER TABLE user ADD COLUMN email TEXT")
        conn.execute("PRAGMA user_version = 2")
        conn.commit()
        print("  已添加 email 列，版本升至 2")

    # ---- 5. 迁移：v2 → v3 建索引 ----
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version == 2:
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_email ON user(email)")
        conn.execute("PRAGMA user_version = 3")
        conn.commit()
        print("  已建唯一索引，版本升至 3")

    print("  当前列：", [r[1] for r in conn.execute("PRAGMA table_info(user)")])
    print("  当前版本：", conn.execute("PRAGMA user_version").fetchone()[0])

    # ---- 6. 迁移失败时：从备份恢复 ----
    print("\n== 模拟迁移失败 ==")
    try:
        conn.execute("ALTER TABLE user ADD COLUMN email TEXT")   # 重复列会失败
    except sqlite3.OperationalError as exc:
        print("  迁移报错：", exc)
        print("  处理：修复迁移脚本，或用备份文件覆盖回滚")

    # 用备份恢复（演示思路）
    conn.close()
    restore = sqlite3.connect(db_path)
    backup_conn = sqlite3.connect(backup_path)
    backup_conn.backup(restore)            # 反向覆盖
    print("  恢复后用户数：", restore.execute("SELECT COUNT(*) FROM user").fetchone()[0])
    print("  恢复后版本：", restore.execute("PRAGMA user_version").fetchone()[0])
    restore.close()
    backup_conn.close()

# 迁移清单：
#   1) 每次改表都写一个带版本号的迁移函数（migrate_v1_to_v2 ...）
#   2) 执行前自动备份（文件名带时间戳，第278课）
#   3) 迁移脚本要可重复执行（IF NOT EXISTS / 先查 user_version）
#   4) 生产环境先在副本上演练

# ===== 练习题 =====
# 1. 把迁移逻辑写成函数 migrate(conn) 循环执行，直到版本最新。
# 2. 用 iter dump 把数据库导出后，导入到一个全新的库并校验行数。
# 3. 给备份文件名加时间戳，保留最近 5 份（结合第278课）。
# 4. 思考：为什么“先备份再迁移”比“迁移失败再想办法”可靠得多？
