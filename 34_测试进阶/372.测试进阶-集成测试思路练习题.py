# ===== 第372课：测试进阶-集成测试思路 =====
# 知识点：
#   - 集成测试：用“真实依赖 + 受控环境”（内存 sqlite、临时文件）
#   - 与单元测试分工：单元 mock 快而多，集成真实而少 —— 测试金字塔
#   - 内存数据库 :memory:：真的 SQL 引擎，但零落盘、随测随建
#   - setUp/tearDown 保证每个用例拿到全新环境（第213课）
import sqlite3
import unittest


class StudentDB:
    """被测组件：真实操作 sqlite。"""

    def __init__(self, conn):
        self.conn = conn
        conn.execute("CREATE TABLE IF NOT EXISTS student (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()

    def add(self, name):
        cur = self.conn.execute("INSERT INTO student (name) VALUES (?)", (name,))
        self.conn.commit()
        return cur.lastrowid

    def get(self, sid):
        row = self.conn.execute("SELECT name FROM student WHERE id = ?", (sid,)).fetchone()
        return row[0] if row else None

    def delete(self, sid):
        cur = self.conn.execute("DELETE FROM student WHERE id = ?", (sid,))
        self.conn.commit()
        return cur.rowcount == 1


class TestStudentDBIntegration(unittest.TestCase):
    """集成测试：不 mock 数据库，用内存 sqlite 走真 SQL。"""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.db = StudentDB(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_add_then_get(self):
        sid = self.db.add("小明")
        self.assertEqual(self.db.get(sid), "小明")

    def test_get_missing(self):
        self.assertIsNone(self.db.get(999))

    def test_delete_then_get(self):
        sid = self.db.add("小红")
        self.assertTrue(self.db.delete(sid))
        self.assertIsNone(self.db.get(sid))

    def test_ids_increment(self):
        a = self.db.add("甲")
        b = self.db.add("乙")
        self.assertEqual(b, a + 1)              # 验证自增主键行为（真实约束）


if __name__ == "__main__":
    unittest.main(verbosity=2)

# ===== 练习题 =====
# 1. 给 StudentDB 加 update 方法，集成测试走一遍“增改查删”。
# 2. 思考：本课为何不用 mock？（我们要测的恰恰是“SQL 写得对不对”）
# 3. 按测试金字塔给本项目排个比：哪类测试最多？哪类最少？
