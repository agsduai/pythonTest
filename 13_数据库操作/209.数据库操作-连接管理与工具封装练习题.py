# ===== 第209课：数据库操作-连接管理与工具封装 =====
# 知识点：
#   - 用 contextmanager 封装“连接-提交/回滚-关闭”的固定流程
#   - sqlite3.Row 让查询结果支持按列名访问
#   - 封装常用函数：建表 / 写入 / 查询，业务代码不再到处 connect
#   - 项目里数据库代码应收敛到统一模块（配合第192课的上下文管理器）

from contextlib import contextmanager

import sqlite3


@contextmanager
def get_conn(db_path=":memory:"):
    """统一的连接管理：Row 工厂 + 自动提交/回滚 + 关闭。"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()           # 正常结束自动提交
    except Exception:
        conn.rollback()         # 出错自动回滚
        raise
    finally:
        conn.close()


def init_db(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS book (id INTEGER PRIMARY KEY, title TEXT, price REAL)"
    )


def add_book(conn, title, price):
    cursor = conn.execute("INSERT INTO book (title, price) VALUES (?, ?)", (title, price))
    return cursor.lastrowid     # 返回自增主键


def all_books(conn):
    return conn.execute("SELECT * FROM book ORDER BY price DESC").fetchall()


with get_conn() as conn:
    init_db(conn)
    add_book(conn, "Python编程", 89.0)
    add_book(conn, "数据结构", 59.5)
    add_book(conn, "机器学习", 129.0)
    for book in all_books(conn):
        print(f"{book['title']}：{book['price']} 元（id={book['id']}）")

# 出错自动回滚演示
try:
    with get_conn() as conn:
        init_db(conn)
        add_book(conn, "会被回滚的书", 1.0)
        raise RuntimeError("模拟异常")
except RuntimeError as exc:
    print(f"异常：{exc}")

with get_conn() as conn:
    init_db(conn)
    count = conn.execute("SELECT COUNT(*) FROM book").fetchone()[0]
    print("回滚后图书数量：", count)      # 0，写入被撤销

# ===== 练习题 =====
# 1. 给 get_conn 增加 timeout 参数并透传给 sqlite3.connect。
# 2. 把本课工具封装成 mydb.py 模块，在第210课案例中 import 使用。
# 3. 思考：为什么“查询函数”不需要 commit？什么操作必须 commit？
