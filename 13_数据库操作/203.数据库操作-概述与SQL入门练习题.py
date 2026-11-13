# ===== 第203课：数据库操作-概述与SQL入门 =====
# 知识点：
#   - 为什么用数据库：结构化存储、快速查询、事务保障
#   - SQLite：零配置的单文件数据库，Python 内置模块，适合学习和小项目
#   - SQL 分类：DDL 建表（CREATE）、DML 增删改（INSERT/UPDATE/DELETE）、
#     DQL 查询（SELECT）
#   - 标准流程：连接 → 游标 → 执行 SQL → 提交 → 关闭

import sqlite3

# :memory: 表示内存数据库，程序结束就消失，适合练习
conn = sqlite3.connect(":memory:")
cursor = conn.cursor()

# DDL：建表
cursor.execute("""
    CREATE TABLE student (
        id INTEGER PRIMARY KEY,
        name TEXT,
        score REAL
    )
""")

# DML：插入
cursor.execute("INSERT INTO student (name, score) VALUES ('小明', 95.5)")
conn.commit()      # 增删改必须提交才生效

# DQL：查询
rows = cursor.execute("SELECT * FROM student").fetchall()
print(rows)        # [(1, '小明', 95.5)]

conn.close()       # 用完关闭连接

# 说明：把 ':memory:' 换成 'demo.db' 就是文件数据库，数据永久保存（下一课演示）。

# ===== 练习题 =====
# 1. 给 student 表再插入两条记录，并查询全部。
# 2. 把 ':memory:' 换成 'course203.db' 运行两次，观察数据是否还在。
# 3. 验证：sqlite3.connect 指向不存在的文件路径时会发生什么？
#    （答案：自动新建一个空数据库文件）
# 4. 思考：什么时候用 SQLite 就够了，什么时候需要 MySQL 这类服务端数据库？
