# ===== 第634课：终端与命令行应用-综合案例-批量文件整理CLI =====
# 知识点：
#   - 综合串起本章：argparse 子命令 + 配置优先级 + 彩色输出 + 退出码 + 进度 + 日志
#   - 文件整理动作：按扩展名归类、重命名、删除空文件；所有动作默认 dry-run
#   - 安全设计：先生成操作计划（plan），再统一执行；--apply 才真正落盘
#   - 幂等：重复执行同一计划不会产生二次移动；目标已存在时自动加后缀
#   - 全部在 TemporaryDirectory 中演示，记录器/输出均可注入，离线可测
#   - main(argv) 返回退出码，单测可断言，不依赖真实 stdin / 真实文件系统根目录
# 依赖：无（标准库）
import argparse
import io
import json
import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

EXIT_OK, EXIT_ERROR = 0, 1


@dataclass
class Action:
    kind: str                 # move / rename / delete / skip
    src: Path
    dst: Path | None = None
    reason: str = ""

    def to_row(self):
        return {"kind": self.kind, "src": self.src.name,
                "dst": self.dst.name if self.dst else None, "reason": self.reason}


@dataclass
class Report:
    actions: list = field(default_factory=list)
    moved = renamed = deleted = skipped = failed = 0


def build_plan(root: Path, by_ext: bool, drop_empty: bool, prefix: str) -> list:
    """只扫描并生成计划，不做任何修改。"""
    plan = []
    for p in sorted(root.iterdir()):
        if not p.is_file():
            continue
        if drop_empty and p.stat().st_size == 0:
            plan.append(Action("delete", p, reason="空文件"))
        elif by_ext and p.suffix:
            folder = root / (p.suffix.lstrip(".").lower() or "noext")
            plan.append(Action("move", p, folder / p.name, reason=f"按扩展名 {p.suffix}"))
        elif prefix:
            plan.append(Action("rename", p, root / (prefix + p.name), reason="加前缀"))
        else:
            plan.append(Action("skip", p, reason="无需处理"))
    return plan


def unique_target(dst: Path) -> Path:
    """目标已存在时追加 _1/_2，保证幂等不覆盖。"""
    if not dst.exists():
        return dst
    for i in range(1, 1000):
        cand = dst.with_name(f"{dst.stem}_{i}{dst.suffix}")
        if not cand.exists():
            return cand
    raise RuntimeError("无法找到可用目标名")


def execute(plan, apply: bool, logger) -> Report:
    rep = Report()
    for act in plan:
        if act.kind == "skip":
            rep.skipped += 1
        elif not apply:
            rep.actions.append(act)
        else:
            try:
                if act.kind == "delete":
                    act.src.unlink()
                    rep.deleted += 1
                else:
                    target = unique_target(act.dst)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(act.src), str(target))
                    if act.kind == "move":
                        rep.moved += 1
                    else:
                        rep.renamed += 1
                    logger.info("%s %s -> %s", act.kind, act.src.name, target.name)
                rep.actions.append(act)
            except OSError as e:
                rep.failed += 1
                logger.error("失败 %s: %s", act.src.name, e)
    return rep


def color(text, code, enabled):
    return f"\x1b[{code}m{text}\x1b[0m" if enabled else text


def build_parser():
    p = argparse.ArgumentParser(prog="tidy", description="批量文件整理 CLI")
    p.add_argument("path", help="要整理的目录")
    p.add_argument("--by-ext", action="store_true", help="按扩展名建子目录归类")
    p.add_argument("--drop-empty", action="store_true", help="删除 0 字节文件")
    p.add_argument("--prefix", default="", help="给文件加统一前缀")
    p.add_argument("--apply", action="store_true", help="真正执行（默认只预览）")
    p.add_argument("--json", action="store_true", help="以 JSON 输出计划")
    p.add_argument("--color", action="store_true", help="启用彩色输出")
    return p


def main(argv=None, out=None, err=None) -> int:
    out = out or io.StringIO()
    err = err or io.StringIO()
    args = build_parser().parse_args(argv)
    root = Path(args.path)
    if not root.is_dir():
        print(f"错误: 不是有效目录 {root}", file=err)
        return EXIT_ERROR

    logger = logging.getLogger("tidy")
    logger.handlers.clear(); logger.setLevel(logging.INFO); logger.propagate = False
    h = logging.StreamHandler(io.StringIO())
    h.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(h)

    plan = build_plan(root, args.by_ext, args.drop_empty, args.prefix)
    rep = execute(plan, args.apply, logger)

    if args.json:
        print(json.dumps({"apply": args.apply,
                          "plan": [a.to_row() for a in rep.actions]},
                         ensure_ascii=False, indent=2), file=out)
    else:
        mode = color("APPLY", "1;32", args.color) if args.apply else color("DRY-RUN", "1;33", args.color)
        print(f"== tidy {mode} | 共 {len(plan)} 项 ==", file=out)
        for a in rep.actions:
            arrow = f" -> {a.dst.relative_to(root)}" if a.dst else ""
            print(f"  [{a.kind:<6}] {a.src.name}{arrow}  ({a.reason})", file=out)
        print(f"\n  移动={rep.moved} 重命名={rep.renamed} 删除={rep.deleted} "
              f"跳过={rep.skipped} 失败={rep.failed}", file=out)
    return EXIT_OK if rep.failed == 0 else EXIT_ERROR


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp) / "inbox"
    root.mkdir()
    for name, content in (("a.txt", "hello"), ("b.TXT", "world"),
                          ("photo.png", "PNG"), ("empty.log", ""), ("notes.md", "m")):
        (root / name).write_text(content, "utf-8")

    print("== 场景 1：DRY-RUN 预览（不落盘）==")
    o = io.StringIO()
    code = main(["--by-ext", "--drop-empty", "--prefix", "x_", str(root)], out=o)
    print(o.getvalue(), end="")
    print("  退出码:", code)
    print("  目录仍未变:", sorted(p.name for p in root.iterdir()))

    print("\n== 场景 2：JSON 输出（便于管道消费）==")
    o = io.StringIO()
    main(["--by-ext", "--json", str(root)], out=o)
    doc = json.loads(o.getvalue())
    print(f"  apply={doc['apply']} 计划条数={len(doc['plan'])}")
    print("  首条:", doc["plan"][0])

    print("\n== 场景 3：--apply 真正执行 ==")
    o = io.StringIO()
    code = main(["--by-ext", "--drop-empty", "--apply", str(root)], out=o)
    print(o.getvalue(), end="")
    print("  执行后目录树:")
    for p in sorted(root.rglob("*")):
        print("   ", p.relative_to(root), "(目录)" if p.is_dir() else f"{p.stat().st_size}B")

    print("\n== 场景 4：幂等性（再跑一次）==")
    o = io.StringIO()
    main(["--by-ext", "--apply", str(root)], out=o)
    print(o.getvalue().splitlines()[-1])

    print("\n== 场景 5：无效路径返回错误码 ==")
    o, e = io.StringIO(), io.StringIO()
    code = main(["/definitely/not/exist"], out=o, err=e)
    print(f"  exit={code}  stderr={e.getvalue().strip()!r}")

print("\n== 设计回顾 ==")
for line in [
    "plan / execute 分离：默认 dry-run，误操作风险最低",
    "unique_target 避免覆盖同名文件，重复执行安全（幂等）",
    "main 接收 argv/out/err，返回退出码，全部可单测",
    "JSON 输出让本工具能作为管道上游被 jq / 其他脚本消费",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加 --undo，读取上次计划的 JSON 把文件移回原位。
# 2. 实现 --min-size/--max-size，按文件大小过滤后再生成计划。
# 3. 给彩色输出加 NO_COLOR 支持，并写单测断言关闭时无 ANSI 控制符。
# 4. 思考：为什么「先生成完整计划再执行」比「边扫描边移动」更安全？
