# ===== 第204课：数据库操作-SQLite连接与建表 =====
# 知识点：
#   - connect(文件名)：文件不存在会自动创建，数据永久保存
#   - 常用类型：INTEGER / TEXT / REAL / BLOB（SQLite 类型宽松，按亲和存储）
#   - PRIMARY KEY AUTOINCREMENT：自增主键
#   - IF NOT EXISTS：避免重复建表报错
#   - NOT NULL / UNIQUE / DEFAULT：常见约束

import os
import sqlite3

DB_FILE = "course204.db"

# 重复运行先删掉旧库，方便练习
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# 建表：带约束
cursor.execute("""
    CREATE TABLE IF NOT EXISTS student (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER DEFAULT 18,
        score REAL,
        phone TEXT UNIQUE
    )
""")

# 查看当前库里的所有表
tables = cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()
print("当前所有表：", tables)

# 查看表结构
schema = cursor.execute("PRAGMA table_info(student)").fetchall()
for col in schema:
    print(col)     # (列序号, 列名, 类型, 是否可为空, 默认值, 是否主键)

conn.close()
print(f"数据库文件已生成：{DB_FILE}（下次运行如果不删除，数据仍然存在）")

# ===== 练习题 =====
# 1. 再建一张 teacher 表（id、name、subject），用 IF NOT EXISTS 防止重复建表。
# 2. 插入两条 phone 相同的数据，观察 UNIQUE 约束如何报错。
# 3. 用 PRAGMA table_info 查看 teacher 表的结构。
# 4. 思考：name TEXT NOT NULL 和 name TEXT 有什么实际区别？
