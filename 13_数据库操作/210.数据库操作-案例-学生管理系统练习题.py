# ===== 第210课：数据库操作-案例-学生管理系统 =====
# 知识点：
#   - 综合运用本章：建表 + 参数化增删改查 + 事务 + 统一连接管理
#   - 用类封装业务逻辑，方法对应一次数据库操作
#   - 数据存进文件数据库，程序重启数据不丢

import os
import sqlite3

DB_FILE = "students_210.db"


class StudentDB:

    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS student (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                score REAL
            )
        """)
        self.conn.commit()

    def add(self, name, age, score):
        cur = self.conn.execute(
            "INSERT INTO student (name, age, score) VALUES (?, ?, ?)",
            (name, age, score),
        )
        self.conn.commit()
        return cur.lastrowid

    def list_all(self):
        return self.conn.execute("SELECT * FROM student ORDER BY id").fetchall()

    def find_by_name(self, keyword):
        return self.conn.execute(
            "SELECT * FROM student WHERE name LIKE ?", (f"%{keyword}%",)
        ).fetchall()

    def update_score(self, student_id, new_score):
        cur = self.conn.execute(
            "UPDATE student SET score = ? WHERE id = ?", (new_score, student_id)
        )
        self.conn.commit()
        return cur.rowcount == 1

    def delete(self, student_id):
        cur = self.conn.execute("DELETE FROM student WHERE id = ?", (student_id,))
        self.conn.commit()
        return cur.rowcount == 1

    def close(self):
        self.conn.close()


def show(rows):
    if not rows:
        print("（无数据）")
    for r in rows:
        print(f"id={r['id']} 姓名={r['name']} 年龄={r['age']} 成绩={r['score']}")


if os.path.exists(DB_FILE):
    os.remove(DB_FILE)          # 每次演示重新开始

db = StudentDB(DB_FILE)
db.add("小明", 15, 92)
db.add("小红", 14, 88)
db.add("小刚", 15, 76)

print("== 全部学生 ==")
show(db.list_all())

print("== 模糊查询：小 ==")
show(db.find_by_name("小"))

print("== 修改 id=3 的成绩为 80 ==")
print("修改成功" if db.update_score(3, 80) else "修改失败")
print("== 删除 id=2 ==")
print("删除成功" if db.delete(2) else "删除失败")

print("== 最终数据 ==")
show(db.list_all())
db.close()

# ===== 练习题 =====
# 1. 增加菜单循环：input 选择 1增 2查 3改 4删 0退出，做成完整命令行系统。
# 2. 给 StudentDB 加分页方法 page(page_no, page_size)，用 LIMIT + OFFSET 实现。
# 3. 增加“按成绩排名”查询：ORDER BY score DESC。
# 4. 思考：把 DB_FILE 改成参数传入，测试/生产环境怎么切换？
