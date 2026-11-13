# ===== 毕业实操题 · 项目04：电商数据报表流水线 =====
# 难度：★★★☆☆    建议用时：8~10 小时
# 覆盖章节：23 办公自动化 / 27 NumPy / 28 Pandas进阶 / 30 可视化进阶
# 详细任务书：见同目录 README.md「项目 04」
# 依赖：pip install pandas numpy matplotlib openpyxl python-docx
#
# 需求速览（分五步，每步可单独调用）：
#   generate   生成 5000 行订单 CSV（故意含缺失/重复/负金额/非法日期）
#   clean      清洗并输出清洗报告（每类脏数据条数与处理方式）
#   analyze    品类×城市 GMV、按月趋势、客单价分箱、Top10 用户
#   chart      3 张图：趋势折线 / 品类柱状 / 金额分布直方图
#   report     导出 report.xlsx（>=4 sheet）+ report.docx（摘要+Top3 表格）
#   all        一键跑全流程：python app.py all --month 2026-11
#
# 实现要求：
#   1. 清洗规则写进注释并输出统计，禁止静默丢数据
#   2. 透视用 pivot_table；分箱用 pd.cut；时间用 resample
#   3. 图表处理中文与负号；Agg 后端保存 PNG
#   4. xlsx 设置表头样式与列宽；docx 表格样式 Table Grid
#   5. 测试 >= 5 个：清洗规则、透视结果、分箱边界
#
# 当前文件为「任务书骨架」：直接运行会打印任务卡。

import argparse
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("output")


# ---------------- 1. 生成模拟数据（含脏数据） ----------------
def generate(path: Path, rows: int = 5000, seed: int = 42) -> Path:
    """生成订单 CSV：订单号/日期/用户/城市/品类/金额。

    脏数据要求（每类至少 20 条）：
      - 金额缺失（空字符串或 NaN）
      - 重复订单号
      - 负金额
      - 非法日期（如 2026-13-45）
    """
    raise NotImplementedError("TODO: 实现 generate")


# ---------------- 2. 清洗 ----------------
def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """返回 (干净数据, 清洗报告)。

    建议规则（与报告一一对应）：
      - 金额缺失 → 丢弃并计数
      - 重复订单号 → 保留第一条并计数
      - 负金额 → 丢弃并计数
      - 非法日期 → 丢弃并计数
      - 金额/日期类型转换失败 → 丢弃并计数
    报告格式：{"总行数": n, "金额缺失": x, "重复订单": x, "负金额": x,
               "非法日期": x, "保留行数": x}
    """
    raise NotImplementedError("TODO: 实现 clean")


# ---------------- 3. 分析 ----------------
def analyze(df: pd.DataFrame) -> dict:
    """返回四张分析结果表（DataFrame）：
    gmv_city_category  品类×城市 透视（sum 金额）
    monthly_trend      按月 GMV（resample("ME")）
    amount_bins        客单价分箱（pd.cut: 0-200/200-1000/1000-2000）
    top10_users        Top10 用户消费
    """
    raise NotImplementedError("TODO: 实现 analyze")


# ---------------- 4. 图表 ----------------
def chart(df: pd.DataFrame, out_dir: Path) -> list[Path]:
    """生成并保存 3 张 PNG（Agg 后端）。返回路径列表。

    要求：
      - rcParams 设置微软雅黑 + unicode_minus=False
      - 趋势图加 7 日均线
      - 柱状图柱顶标数值
      - 直方图标出中位数
    """
    raise NotImplementedError("TODO: 实现 chart")


# ---------------- 5. 报告 ----------------
def report(tables: dict, clean_report: dict, out_dir: Path) -> tuple[Path, Path]:
    """导出 xlsx（>=4 sheet）与 docx（摘要 + Top3 表格）。"""
    raise NotImplementedError("TODO: 实现 report")


def run_all(month: str | None = None) -> int:
    """一键流程：generate → clean → analyze → chart → report。"""
    raise NotImplementedError("TODO: 实现 run_all（含耗时打印）")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="report.py", description="电商订单报表流水线")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate")
    sub.add_parser("clean")
    sub.add_parser("analyze")
    sub.add_parser("chart")
    sub.add_parser("report")
    p_all = sub.add_parser("all"); p_all.add_argument("--month", default=None)
    args = parser.parse_args(argv)
    # TODO: 分发到对应步骤（中间数据落在 output/ 下，可复用）
    print(f"TODO: 实现命令 {args.command}")
    return 0


# ---------- 自测（实现后删除 @unittest.skip） ----------
class TestPipeline(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    @unittest.skip("实现后删除本行")
    def test_generate_has_dirty_rows(self):
        path = generate(self.dir / "orders.csv", rows=200)
        df = pd.read_csv(path, dtype=str)
        self.assertEqual(len(df), 200)
        self.assertTrue(df["金额"].isna().any() or (df["金额"] == "").any())

    @unittest.skip("实现后删除本行")
    def test_clean_removes_negatives(self):
        raw = pd.DataFrame({
            "订单号": ["A1", "A2"], "日期": ["2026-11-01", "2026-11-02"],
            "用户": ["u1", "u2"], "城市": ["北京", "上海"],
            "品类": ["数码", "服饰"], "金额": ["100", "-5"],
        })
        clean_df, report = clean(raw)
        self.assertEqual(len(clean_df), 1)
        self.assertEqual(report["负金额"], 1)

    @unittest.skip("实现后删除本行")
    def test_clean_dedup(self):
        raw = pd.DataFrame({
            "订单号": ["A1", "A1"], "日期": ["2026-11-01"] * 2,
            "用户": ["u1"] * 2, "城市": ["北京"] * 2,
            "品类": ["数码"] * 2, "金额": ["100", "100"],
        })
        clean_df, report = clean(raw)
        self.assertEqual(len(clean_df), 1)
        self.assertEqual(report["重复订单"], 1)

    @unittest.skip("实现后删除本行")
    def test_analyze_top10(self):
        # 造 12 个用户各 1 单，断言 top10_users 恰好 10 行
        pass

    @unittest.skip("实现后删除本行")
    def test_bin_boundaries(self):
        # 金额 199 / 200 / 999 / 1000 / 2000 的分箱归属
        pass


def print_task_card():
    print("=" * 64)
    print("毕业实操题 · 项目04  电商数据报表流水线")
    print("=" * 64)
    print("目标：脏数据清洗报告 + Pandas 透视 + 3 张图 + Excel/Word 成品")
    print("\n验收清单：")
    for item in [
        "4 类脏数据全部被识别并记录条数",
        "report.xlsx 有 >=4 个 sheet 且无乱码",
        "3 张 PNG 中文正常、带标注",
        "report.docx 含摘要段落 + Top3 表格",
        "5 个测试全部通过（删除 @unittest.skip 后）",
    ]:
        print(f"  [ ] {item}")
    print("\n下一步：")
    print("  1. 先写 generate，故意把 4 类脏数据塞进去")
    print("  2. clean 输出报告 dict，逐条对账")
    print("  3. analyze 用 pivot_table / resample / cut")
    print("  4. chart 注意 rcParams 中文设置与 Agg 后端")
    print("  5. report 用 ExcelWriter 多 sheet + python-docx 表格")


if __name__ == "__main__":
    print_task_card()
    sys.exit(0)
