# ===== 毕业实操题 · 项目01：命令行学生成绩系统 =====
# 难度：★★☆☆☆    建议用时：4~6 小时
# 覆盖章节：03 数据容器 / 04 函数 / 14 测试 / 22 argparse / 31 OOP进阶
# 详细任务书：见同目录 README.md「项目 01」
#
# 需求速览：
#   add <姓名> <分数> [-s 科目]   添加成绩（0~100 校验，同名同科目去重）
#   list [--sort score|name]      列表（默认分数降序）
#   search <关键字>               姓名模糊查询
#   rank [-n 3]                   前 N 名
#   stats                         人数 / 平均 / 最高 / 最低 / 及格率
#   export <out.csv>              导出 CSV（utf-8-sig）
#
# 实现要求：
#   1. Student 用 @dataclass；数据存 students.json（with + encoding="utf-8"）
#   2. 非法分数 / JSON 损坏 → 中文友好提示 + 退出码 2，不许崩 traceback
#   3. 测试用 TemporaryDirectory，不得污染真实数据
#   4. 完成所有 TODO 后，删除测试方法上的 @unittest.skip 并跑通
#
# 当前文件为「任务书骨架」：直接运行会打印任务卡；实现后即可当 CLI 使用。

from __future__ import annotations   # 注解延迟求值：类内 list 方法不遮蔽内置 list

import argparse
import csv
import json
import sys
import tempfile
import unittest
from dataclasses import asdict, dataclass
from pathlib import Path

DATA_FILE = Path("students.json")


@dataclass
class Student:
    name: str
    score: float
    subject: str = "语文"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        # TODO: 校验 data 字段完整与类型，非法数据抛 ValueError
        return cls(name=data["name"], score=float(data["score"]),
                   subject=data.get("subject", "语文"))


class StudentStore:
    """负责持久化与查询；CLI 只调用这一层。"""

    def __init__(self, path: Path = DATA_FILE):
        self.path = Path(path)

    # ---------- 存储 ----------
    def load(self) -> list[Student]:
        """读 JSON；文件不存在返回 []；JSON 损坏抛 ValueError（带中文提示）。"""
        raise NotImplementedError("TODO: 实现 load")

    def save(self, students: list[Student]) -> None:
        """原子写入：先写临时文件再替换，避免写一半损坏。"""
        raise NotImplementedError("TODO: 实现 save")

    # ---------- 业务 ----------
    def add(self, name: str, score: float, subject: str = "语文") -> Student:
        """校验 → 查重 → 追加 → 保存。分数越界抛 ValueError。"""
        raise NotImplementedError("TODO: 实现 add")

    def list(self, sort_by: str = "score", desc: bool = True) -> list[Student]:
        """sort_by 只接受 score / name。"""
        raise NotImplementedError("TODO: 实现 list")

    def search(self, keyword: str) -> list[Student]:
        raise NotImplementedError("TODO: 实现 search")

    def rank(self, top: int = 3) -> list[Student]:
        raise NotImplementedError("TODO: 实现 rank")

    def stats(self) -> dict:
        """返回 {count, average, max, min, pass_rate}；空数据要有合理默认。"""
        raise NotImplementedError("TODO: 实现 stats")

    def export_csv(self, out: Path) -> int:
        """返回导出条数；编码用 utf-8-sig（Excel 不乱码）。"""
        raise NotImplementedError("TODO: 实现 export_csv")


# ---------- CLI（框架已给出，补全 main 的分发逻辑） ----------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="app.py", description="学生成绩管理")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="添加成绩")
    p_add.add_argument("name")
    p_add.add_argument("score", type=float)
    p_add.add_argument("-s", "--subject", default="语文")

    p_list = sub.add_parser("list", help="列出成绩")
    p_list.add_argument("--sort", choices=["score", "name"], default="score")

    p_search = sub.add_parser("search", help="模糊查询")
    p_search.add_argument("keyword")

    p_rank = sub.add_parser("rank", help="排名")
    p_rank.add_argument("-n", type=int, default=3)

    sub.add_parser("stats", help="统计")

    p_export = sub.add_parser("export", help="导出 CSV")
    p_export.add_argument("out")
    return parser


def main(argv=None) -> int:
    """返回退出码：0 成功 / 2 参数或数据错误。"""
    args = build_parser().parse_args(argv)
    store = StudentStore()
    # TODO: 按 args.command 分发到 store 的方法
    #       捕获 ValueError / OSError，打印到 stderr 并 return 2
    print(f"TODO: 实现命令 {args.command} 的分发逻辑")
    return 0


# ---------- 自测（实现后删除 @unittest.skip） ----------
class TestStudentStore(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = StudentStore(Path(self.tmp.name) / "students.json")

    def tearDown(self):
        self.tmp.cleanup()

    @unittest.skip("实现 StudentStore 后删除本行")
    def test_add_and_reload(self):
        self.store.add("小明", 92)
        reloaded = StudentStore(self.store.path).load()
        self.assertEqual(reloaded[0].name, "小明")
        self.assertEqual(reloaded[0].score, 92)

    @unittest.skip("实现 StudentStore 后删除本行")
    def test_score_validation(self):
        with self.assertRaises(ValueError):
            self.store.add("小明", 101)
        with self.assertRaises(ValueError):
            self.store.add("小红", -1)

    @unittest.skip("实现 StudentStore 后删除本行")
    def test_duplicate_rejected(self):
        self.store.add("小明", 92)
        with self.assertRaises(ValueError):
            self.store.add("小明", 80)

    @unittest.skip("实现 StudentStore 后删除本行")
    def test_stats(self):
        for name, score in [("A", 90), ("B", 80), ("C", 50), ("D", 60)]:
            self.store.add(name, score)
        s = self.store.stats()
        self.assertEqual(s["count"], 4)
        self.assertEqual(s["pass_rate"], 75.0)

    @unittest.skip("实现 StudentStore 后删除本行")
    def test_broken_json(self):
        self.store.path.write_text("{坏数据", encoding="utf-8")
        with self.assertRaises(ValueError):
            StudentStore(self.store.path).load()


def print_task_card():
    print("=" * 64)
    print("毕业实操题 · 项目01  命令行学生成绩系统")
    print("=" * 64)
    print("目标：6 个命令 + JSON 持久化 + 输入校验 + 5 个以上测试")
    print("\n验收清单：")
    for item in [
        "add / list / search / rank / stats / export 全部可用",
        "连续 add 后重启程序，数据仍在",
        "abc、-5、101 均被拦截且有中文提示",
        "export 的 CSV 用 Excel 打开不乱码",
        "5 个测试全部通过（删除 @unittest.skip 后）",
    ]:
        print(f"  [ ] {item}")
    print("\n下一步：")
    print("  1. 打开同目录 README.md 阅读完整任务书")
    print("  2. 逐个实现 Student / StudentStore 的 TODO")
    print("  3. 补全 main() 的命令分发")
    print("  4. 删除测试上的 @unittest.skip，运行：")
    print("     python -m unittest 001_项目01_命令行学生成绩系统.py -v")
    print("  5. 用 python 本文件.py --help 检查帮助是否完整")


if __name__ == "__main__":
    print_task_card()
    sys.exit(0)
