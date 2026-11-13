# ===== 毕业实操题 · 项目02：并发日志分析器 =====
# 难度：★★★☆☆    建议用时：6~8 小时
# 覆盖章节：11 生成器 / 12 线程池 / 15 正则 / 16 标准库 / 21 性能剖析
# 详细任务书：见同目录 README.md「项目 02」
#
# 需求速览：
#   make_logs.py   生成 5 份样例日志（每份 5000 行）
#   analyze.py <目录> [--workers 4]
#     - 流式逐行读取（生成器，禁止一次性读入内存）
#     - 正则命名分组解析：时间 / 级别 / 方法 / 路径 / 耗时
#     - 输出：级别统计、接口平均耗时 Top5、慢请求清单（WARNING/ERROR 且 >=500ms）
#     - 写 report.json + report.md（含串行 vs 并行耗时对比）
#     - 用 cProfile 找一次热点，README 说明优化前后
#
# 实现要求：
#   1. 正则必须使用命名分组 (?P<level>...)
#   2. 坏行跳过并计数，不能中断整个分析
#   3. 多文件用 ThreadPoolExecutor；汇总统计只放在主线程
#   4. 测试 >= 5 个：解析、坏行、慢请求筛选、统计正确性
#
# 当前文件为「任务书骨架」：直接运行会打印任务卡。

import re
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# 日志行样例：
# 2026-11-12 10:23:01 [ERROR] GET /api/pay 失败 1500ms
LINE_RE = re.compile(
    r"(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) "
    r"\[(?P<level>INFO|WARNING|ERROR)\] "
    r"(?P<method>GET|POST) (?P<path>/\S+) .*? (?P<ms>\d+)ms"
)


def make_sample_logs(dir_path: Path, files: int = 5, lines: int = 5000) -> list[Path]:
    """生成样例日志（含少量坏行）。返回文件路径列表。"""
    raise NotImplementedError("TODO: 用 random + datetime 生成，级别/路径/耗时合理分布")


def iter_lines(path: Path):
    """生成器：逐行 yield 文本（strip 后可跳过空行）。"""
    raise NotImplementedError("TODO: 实现流式读取")


def parse_line(line: str) -> dict | None:
    """匹配成功返回 {time, level, path, ms}；不匹配返回 None（坏行）。"""
    raise NotImplementedError("TODO: 用 LINE_RE.match / fullmatch")


def analyze_file(path: Path) -> dict:
    """单文件统计：levels / path_totals / path_counts / slow / bad_lines / total。"""
    raise NotImplementedError("TODO: 逐行 parse_line 并累计")


def merge_stats(results: list[dict]) -> dict:
    """合并多文件统计（主线程调用，无需锁）。"""
    raise NotImplementedError("TODO: Counter 相加、defaultdict 累加")


def analyze_many(paths: list[Path], workers: int = 4) -> dict:
    """线程池并发分析；返回合并后的统计。"""
    raise NotImplementedError("TODO: ThreadPoolExecutor.map(analyze_file, paths)")


def write_reports(stats: dict, out_dir: Path, timings: dict) -> None:
    """写 report.json 与 report.md。"""
    raise NotImplementedError("TODO: json.dump + Markdown 表格")


def main(argv=None) -> int:
    """CLI：analyze <dir> [--workers N] [--out DIR]。"""
    raise NotImplementedError("TODO: argparse + 计时 + 串行/并行对比")


# ---------- 自测（实现后删除 @unittest.skip） ----------
class TestLogAnalyzer(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    @unittest.skip("实现后删除本行")
    def test_parse_ok(self):
        row = parse_line("2026-11-12 10:23:01 [ERROR] GET /api/pay 失败 1500ms")
        self.assertEqual(row["level"], "ERROR")
        self.assertEqual(row["path"], "/api/pay")
        self.assertEqual(row["ms"], 1500)

    @unittest.skip("实现后删除本行")
    def test_parse_bad_line(self):
        self.assertIsNone(parse_line("这不是一行合法日志"))

    @unittest.skip("实现后删除本行")
    def test_slow_filter(self):
        # 提示：先造 3 行（INFO 100ms / WARNING 800ms / ERROR 200ms），
        #       断言 slow 只包含 WARNING 那条
        pass

    @unittest.skip("实现后删除本行")
    def test_bad_lines_counted(self):
        # 写 2 行合法 + 1 行坏行，断言 bad_lines == 1
        pass

    @unittest.skip("实现后删除本行")
    def test_merge_totals(self):
        # 两个文件的 level 统计合并后总数 == 各自之和
        pass


def print_task_card():
    print("=" * 64)
    print("毕业实操题 · 项目02  并发日志分析器")
    print("=" * 64)
    print("目标：生成器流式读取 + 正则解析 + 线程池并发 + 剖析报告")
    print("\n验收清单：")
    for item in [
        "5 个日志文件的统计结果与逐个手跑一致",
        "10 万行时内存平稳（生成器生效）",
        "坏行被计数且不中断分析",
        "report.md 含串行 vs 并行耗时对比表",
        "5 个测试全部通过（删除 @unittest.skip 后）",
    ]:
        print(f"  [ ] {item}")
    print("\n下一步：")
    print("  1. 先用 make_sample_logs 造数据，肉眼验证格式")
    print("  2. 实现 parse_line → 用 3 行样例手动调试")
    print("  3. 实现 analyze_file / merge_stats / analyze_many")
    print("  4. 用 cProfile 跑一次，记录热点与优化前后耗时")
    print("  5. 补测试，删除 @unittest.skip")


if __name__ == "__main__":
    print_task_card()
    sys.exit(0)
