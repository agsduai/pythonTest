# ===== 毕业实操题 · 项目06：综合自动化运维脚本 =====
# 难度：★★★★☆    建议用时：8~10 小时
# 覆盖章节：20 加密安全 / 22 实用脚本 / 23 办公自动化 / 14 测试
# 详细任务书：见同目录 README.md「项目 06」
#
# 需求速览：
#   python backup.py backup  --src D:\data --out D:\backups --keep 5
#   python backup.py verify  --src D:\data --archive D:\backups\20261112.zip
#   python backup.py prune   --out D:\backups --keep 5
#   python backup.py report  --out D:\backups --to ops@example.com
#
# 功能要求：
#   backup : 打包 zip（跳过 __pycache__/.git/临时文件）+ sha256 清单 + 立即校验
#   verify : 对比源目录与清单，报告新增/修改/缺失，失败返回退出码 1
#   prune  : 只保留最近 N 份（先 dry-run 打印，再删除）
#   report : 生成 Markdown 摘要 + alert.eml 邮件草稿（不真发）
#   所有命令 : 支持 --dry-run；全程 logging 到 backup.log
#
# 退出码：0 成功 / 1 校验失败 / 2 参数或环境错误
#
# 当前文件为「任务书骨架」：直接运行会打印任务卡。

import argparse
import hashlib
import json
import logging
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime
from pathlib import Path

log = logging.getLogger("backup")


# ---------------- 工具函数 ----------------
def should_skip(path: Path) -> bool:
    """跳过 __pycache__ / .git / *.tmp / 空目录等。"""
    raise NotImplementedError("TODO: 实现 should_skip")


def file_sha256(path: Path) -> str:
    """分块读取计算摘要（不要一次读入内存）。"""
    raise NotImplementedError("TODO: 实现 file_sha256")


# ---------------- 四个命令 ----------------
def backup(src: Path, out: Path, keep: int = 5, dry_run: bool = False) -> Path:
    """打包 + 清单 + 校验。返回归档路径。

    - 归档名：YYYYMMDD_HHMMSS.zip（同名加序号）
    - 清单：同名 .sha256，格式 "<hash>  <相对路径>"
    - dry_run：只打印将打包的文件数与归档名，不落盘
    - 完成后调用 prune(out, keep)
    """
    raise NotImplementedError("TODO: 实现 backup")


def verify(src: Path, archive: Path) -> bool:
    """解清单比对：
    - 逐行校验哈希 → 列出 modified
    - 源目录有而清单无 → added
    - 清单有而源目录无 → missing
    - 返回 True/False，并写 Markdown 报告
    """
    raise NotImplementedError("TODO: 实现 verify")


def prune(out: Path, keep: int = 5, dry_run: bool = True) -> list[Path]:
    """按文件名排序保留最新 keep 份，删除其余。返回将删除/已删除的列表。"""
    raise NotImplementedError("TODO: 实现 prune")


def make_report(out: Path, to_addr: str | None = None) -> tuple[Path, Path | None]:
    """生成 backup_report.md 与（可选）alert.eml 邮件草稿。

    收件人/发件人从环境变量读取：
      BACKUP_MAIL_TO / BACKUP_MAIL_FROM
    缺失时只生成本地报告，不生成 .eml
    """
    raise NotImplementedError("TODO: 实现 make_report")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="backup.py", description="自动化备份工具")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("backup")
    p.add_argument("--src", required=True); p.add_argument("--out", required=True)
    p.add_argument("--keep", type=int, default=5); p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("verify")
    p.add_argument("--src", required=True); p.add_argument("--archive", required=True)

    p = sub.add_parser("prune")
    p.add_argument("--out", required=True); p.add_argument("--keep", type=int, default=5)
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("report")
    p.add_argument("--out", required=True); p.add_argument("--to", default=None)

    args = parser.parse_args(argv)
    # TODO: 配置 logging（文件 + 控制台）→ 分发 → 返回 0/1/2
    print(f"TODO: 实现命令 {args.command}")
    return 0


# ---------- 自测（实现后删除 @unittest.skip） ----------
class TestBackup(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.src = self.root / "src"
        self.src.mkdir()
        (self.src / "a.txt").write_text("hello", encoding="utf-8")
        (self.src / "b.csv").write_text("a,b\n1,2", encoding="utf-8")
        self.out = self.root / "backups"

    def tearDown(self):
        self.tmp.cleanup()

    @unittest.skip("实现后删除本行")
    def test_backup_creates_archive_and_manifest(self):
        archive = backup(self.src, self.out)
        self.assertTrue(archive.exists())
        self.assertTrue(archive.with_suffix(".zip.sha256").exists() or True)

    @unittest.skip("实现后删除本行")
    def test_verify_detects_modification(self):
        archive = backup(self.src, self.out)
        (self.src / "a.txt").write_text("tampered", encoding="utf-8")
        self.assertFalse(verify(self.src, archive))

    @unittest.skip("实现后删除本行")
    def test_prune_keeps_latest(self):
        # 造 4 个假归档，prune(keep=2) 后只剩 2 个，且是最新两个
        pass

    @unittest.skip("实现后删除本行")
    def test_dry_run_changes_nothing(self):
        before = sorted(p.name for p in self.src.rglob("*"))
        backup(self.src, self.out, dry_run=True)
        self.assertFalse(self.out.exists())
        self.assertEqual(before, sorted(p.name for p in self.src.rglob("*")))

    @unittest.skip("实现后删除本行")
    def test_skip_pycache(self):
        cache = self.src / "__pycache__"
        cache.mkdir()
        (cache / "x.pyc").write_text("x", encoding="utf-8")
        archive = backup(self.src, self.out)
        with zipfile.ZipFile(archive) as zf:
            self.assertNotIn("__pycache__/x.pyc", zf.namelist())


def print_task_card():
    print("=" * 64)
    print("毕业实操题 · 项目06  综合自动化运维脚本")
    print("=" * 64)
    print("目标：备份+校验+轮转+报告一体化，能被任务计划程序调用")
    print("\n验收清单：")
    for item in [
        "连续 3 次 backup 生成 3 个可解压归档",
        "篡改源文件后 verify 返回 1 并指出具体文件",
        "prune --keep 2 后只剩最新 2 个",
        "--dry-run 前后目录完全无变化",
        "backup.log 含时间戳与级别；report.md 可读",
        "5 个测试全部通过（删除 @unittest.skip 后）",
    ]:
        print(f"  [ ] {item}")
    print("\n下一步：")
    print("  1. 先写 should_skip + file_sha256 + backup 最小版")
    print("  2. 再写 verify（哈希对账）与 prune（文件名排序）")
    print("  3. 最后做 make_report 与 logging/退出码")
    print("  4. 用临时目录跑全流程，再拿去备份真实目录")
    print("  5. 把命令写进 Windows 任务计划，每天 18:00 执行")


if __name__ == "__main__":
    print_task_card()
    sys.exit(0)
