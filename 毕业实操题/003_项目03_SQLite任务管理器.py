# ===== 毕业实操题 · 项目03：SQLite 任务管理器 =====
# 难度：★★★☆☆    建议用时：6~8 小时
# 覆盖章节：13 数据库操作 / 25 SQL进阶 / 14 测试 / 22 argparse
# 详细任务书：见同目录 README.md「项目 03」
#
# 需求速览（CLI）：
#   add <标题> [-p 1-5] [-d 2026-12-31]     新建任务
#   list [--status todo|done|all] [--overdue]
#   done <id>                                标记完成
#   delete <id> [--yes]                      删除（默认二次确认）
#   search <关键字>                          标题模糊查询（参数化 LIKE）
#   import <csv>                             事务批量导入，坏行整体回滚
#   export <json>                            导出全部
#
# 表结构：
#   tasks(id, title, priority CHECK 1..5, due_date, status, created_at)
#
# 实现要求：
#   1. 全部 SQL 参数化，禁止拼接（防注入）
#   2. 建联合索引 idx_tasks_status_due(status, due_date)
#   3. 建视图 v_overdue：未完成且 due_date < 今天
#   4. 事务导入：任何一行非法 → rollback，并报出行号
#   5. 测试用 :memory:，>=6 个用例（含回滚、重复 done、注入）
#
# 当前文件为「任务书骨架」：直接运行会打印任务卡。

from __future__ import annotations   # 注解延迟求值：类内 list 方法不遮蔽内置 list

import argparse
import csv
import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import contextmanager
from datetime import date
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    due_date TEXT,
    status TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'done')),
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_status_due ON tasks(status, due_date);
CREATE VIEW IF NOT EXISTS v_overdue AS
    SELECT * FROM tasks
    WHERE status = 'todo' AND due_date IS NOT NULL AND due_date < date('now');
"""


@contextmanager
def db_connect(path=":memory:"):
    """统一连接管理：Row 工厂 + 自动 commit/rollback + 关闭。"""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class TaskDB:

    def __init__(self, path=":memory:"):
        self.path = path
        with db_connect(self.path) as conn:
            conn.executescript(SCHEMA)

    # ---------- 增 ----------
    def add(self, title: str, priority: int = 3, due_date: str | None = None) -> int:
        """返回新 id；标题为空 / 优先级越界抛 ValueError。"""
        raise NotImplementedError("TODO: 实现 add（参数化 INSERT）")

    # ---------- 查 ----------
    def list(self, status="todo", overdue=False) -> list[sqlite3.Row]:
        """status: todo/done/all；按 priority 升序 + due_date 升序。"""
        raise NotImplementedError("TODO: 实现 list（动态 WHERE 但值必须参数化）")

    def search(self, keyword: str) -> list[sqlite3.Row]:
        raise NotImplementedError("TODO: 实现 search（LIKE ? 参数化）")

    # ---------- 改 / 删 ----------
    def complete(self, task_id: int) -> bool:
        """不存在返回 False；已完成的再次执行返回 False（幂等）。"""
        raise NotImplementedError("TODO: 实现 complete")

    def delete(self, task_id: int) -> bool:
        raise NotImplementedError("TODO: 实现 delete")

    # ---------- 批量 ----------
    def import_csv(self, path: Path) -> int:
        """事务导入：任一行非法 → 全部回滚，异常信息带行号。返回成功条数。"""
        raise NotImplementedError("TODO: 实现 import_csv")

    def export_json(self, out: Path) -> int:
        raise NotImplementedError("TODO: 实现 export_json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="task.py", description="SQLite 任务管理")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("add"); p.add_argument("title"); p.add_argument("-p", "--priority", type=int, default=3); p.add_argument("-d", "--due")
    p = sub.add_parser("list"); p.add_argument("--status", choices=["todo", "done", "all"], default="todo"); p.add_argument("--overdue", action="store_true")
    p = sub.add_parser("done"); p.add_argument("id", type=int)
    p = sub.add_parser("delete"); p.add_argument("id", type=int); p.add_argument("--yes", action="store_true")
    p = sub.add_parser("search"); p.add_argument("keyword")
    p = sub.add_parser("import"); p.add_argument("csv_path")
    p = sub.add_parser("export"); p.add_argument("out")
    return parser


def main(argv=None) -> int:
    """0 成功 / 1 业务错误（不存在、回滚） / 2 参数错误。"""
    args = build_parser().parse_args(argv)
    db = TaskDB("tasks.db")
    # TODO: 分发 + 友好错误提示
    print(f"TODO: 实现命令 {args.command}")
    return 0


# ---------- 自测（实现后删除 @unittest.skip） ----------
class TestTaskDB(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.db = TaskDB(":memory:")

    def tearDown(self):
        self.tmp.cleanup()

    @unittest.skip("实现后删除本行")
    def test_add_and_list(self):
        self.db.add("写周报", priority=1)
        self.db.add("买咖啡", priority=5)
        rows = self.db.list()
        self.assertEqual([r["title"] for r in rows], ["写周报", "买咖啡"])

    @unittest.skip("实现后删除本行")
    def test_priority_check(self):
        with self.assertRaises(ValueError):
            self.db.add("非法", priority=9)

    @unittest.skip("实现后删除本行")
    def test_complete_idempotent(self):
        tid = self.db.add("任务")
        self.assertTrue(self.db.complete(tid))
        self.assertFalse(self.db.complete(tid))

    @unittest.skip("实现后删除本行")
    def test_search_injection_safe(self):
        self.db.add("正常任务")
        self.assertEqual(self.db.search("' OR '1'='1"), [])   # 注入串当普通文本

    @unittest.skip("实现后删除本行")
    def test_import_rollback(self):
        csv_path = self.dir / "tasks.csv"
        csv_path.write_text("title,priority\n好任务,2\n坏任务,99\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.db.import_csv(csv_path)
        self.assertEqual(self.db.list(status="all"), [])       # 整体回滚

    @unittest.skip("实现后删除本行")
    def test_export_json(self):
        self.db.add("导出任务")
        out = self.dir / "tasks.json"
        self.assertEqual(self.db.export_json(out), 1)
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))[0]["title"], "导出任务")


def print_task_card():
    print("=" * 64)
    print("毕业实操题 · 项目03  SQLite 任务管理器")
    print("=" * 64)
    print("目标：7 个命令 + 参数化 SQL + 事务导入 + 索引/视图 + 集成测试")
    print("\n验收清单：")
    for item in [
        "7 个命令全部可用，错误输入不崩",
        "import 含坏行时条数不变（事务回滚）",
        "EXPLAIN QUERY PLAN 显示 list 查询走索引",
        "搜索无法被 SQL 注入绕过",
        "6 个测试全部通过（删除 @unittest.skip 后）",
    ]:
        print(f"  [ ] {item}")
    print("\n下一步：")
    print("  1. 先实现 TaskDB.add / list，跑通最小闭环")
    print("  2. 再补 complete / delete / search")
    print("  3. 最后做 import_csv（务必用事务）与 export_json")
    print("  4. 用 EXPLAIN QUERY PLAN 检查索引是否生效")
    print("  5. 删除测试上的 @unittest.skip")


if __name__ == "__main__":
    print_task_card()
    sys.exit(0)
