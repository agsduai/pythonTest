# ===== 第630课：终端与命令行应用-退出码与错误信息 =====
# 知识点：
#   - 退出码 0 = 成功；非 0 = 失败。Shell 用 $? / %ERRORLEVEL% 判断
#   - 约定：1 通用错误、2 命令行用法错误（argparse 默认）、126/127 权限/找不到命令
#   - sys.exit(code) 抛 SystemExit；main() 返回 int 再由 sys.exit(main()) 退出最易测
#   - 正常信息走 stdout，错误/警告走 stderr；管道时 stdout 可被下游消费
#   - 错误信息要包含「出了什么错 + 相关对象 + 可行动建议」，不要只抛 traceback
#   - 自定义异常 + 顶层统一捕获，避免堆栈刷屏；调试模式用 --debug 打开堆栈
# 依赖：无（标准库）
import argparse
import contextlib
import io
import sys
import tempfile
from pathlib import Path

EXIT_OK, EXIT_USAGE, EXIT_RUNTIME, EXIT_NOT_FOUND = 0, 2, 1, 66


class AppError(Exception):
    """业务异常：带退出码与用户可读消息。"""

    def __init__(self, message, code=EXIT_RUNTIME, hint=""):
        super().__init__(message)
        self.message, self.code, self.hint = message, code, hint


def process(path: Path, min_lines: int) -> str:
    if not path.exists():
        raise AppError(f"找不到文件: {path.name}", EXIT_NOT_FOUND,
                       "检查路径拼写，或用 --create 先创建")
    lines = path.read_text("utf-8").splitlines()
    if len(lines) < min_lines:
        raise AppError(f"文件行数不足: {len(lines)} < {min_lines}", EXIT_RUNTIME,
                       "调小 --min-lines 或补充数据后重试")
    return f"OK: {path.name} 共 {len(lines)} 行，首行={lines[0][:30]!r}"


def build_parser():
    p = argparse.ArgumentParser(prog="checker")
    p.add_argument("path")
    p.add_argument("--min-lines", type=int, default=1)
    p.add_argument("--debug", action="store_true", help="出错时打印完整堆栈")
    return p


def main(argv=None, stdout=None, stderr=None) -> int:
    """返回退出码，不直接 sys.exit —— 便于单测断言。"""
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    try:
        args = build_parser().parse_args(argv)
        result = process(Path(args.path), args.min_lines)
        print(result, file=out)
        return EXIT_OK
    except AppError as e:
        print(f"错误: {e.message}", file=err)
        if e.hint:
            print(f"建议: {e.hint}", file=err)
        if "--debug" in (argv or []) and hasattr(e, "__traceback__"):
            import traceback
            traceback.print_exc(file=err)
        return e.code
    except SystemExit as e:
        # argparse 的用法错误（如缺参数、非法 choices）默认退出码 2
        return e.code if isinstance(e.code, int) else EXIT_USAGE


def run_capture(argv):
    """捕获 stdout/stderr，返回 (退出码, stdout, stderr)。"""
    o, e = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(o), contextlib.redirect_stderr(e):
        code = main(argv, stdout=o, stderr=e)
    return code, o.getvalue(), e.getvalue()


with tempfile.TemporaryDirectory() as tmp:
    good = Path(tmp) / "good.txt"
    good.write_text("\n".join(f"line{i}" for i in range(10)), "utf-8")
    empty = Path(tmp) / "empty.txt"
    empty.write_text("", "utf-8")

    print("== 各种输入对应的退出码与输出流 ==")
    cases = [
        ["good.txt"],
        ["good.txt", "--min-lines", "99"],
        ["missing.txt"],
        ["good.txt", "--min-lines", "abc"],
        [],
    ]
    # 把相对路径换成临时目录里的真实文件
    for case in cases:
        argv = case[:]
        if argv and not argv[0].startswith("-"):
            argv[0] = str(Path(tmp) / argv[0])
        code, so, se = run_capture(argv)
        label = " ".join(Path(x).name if x.startswith(str(tmp)) else x for x in argv) or "(无参数)"
        print(f"\n  $ checker {label}")
        print(f"    exit={code}  stdout={so.strip()!r}  stderr={se.strip().splitlines()[-1:]!r}")

    print("\n== --debug 打开堆栈 ==")
    code, _, se = run_capture([str(Path(tmp) / "missing.txt"), "--debug"])
    print(f"  exit={code}  stderr 含 traceback: {'Traceback' in se}")

print("\n== 退出码语义表 ==")
for code, name, desc in (
    (0, "OK", "成功"),
    (1, "ERROR", "通用运行错误"),
    (2, "USAGE", "命令行用法错误（argparse 默认）"),
    (66, "EX_NOINPUT", "输入文件不存在（sysexits 约定）"),
    (126, "NOEXEC", "找到但不可执行"),
    (127, "NOTFOUND", "命令不存在"),
    (130, "SIGINT", "被 Ctrl+C 中断（128+2）"),
):
    print(f"  {code:>4}  {name:<10} {desc}")

print("\n== stdout 与 stderr 分离 ==")
print("  正确结果 -> stdout：可被 `tool | jq` 继续处理")
print("  错误信息 -> stderr：即使 stdout 被重定向，用户仍能在终端看到")
print("  反例：把错误 print 到 stdout，会污染下游管道数据")

print("\n== sys.exit(main()) 模式 ==")
for line in [
    "模块顶层写 if __name__ == '__main__': sys.exit(main())",
    "main() 只返回 int，不直接退出，单测可直接调用并断言返回值",
    "顶层统一捕获 AppError，避免每个函数各自 print 错误",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加 --json 选项，把错误信息以 {"error":..., "code":...} 输出到 stderr。
# 2. 捕获 KeyboardInterrupt，返回 130 而不是打印 traceback。
# 3. 给 main 写单元测试，覆盖成功、业务异常、argparse 用法错误三类退出码。
# 4. 思考：为什么库代码里不要直接 sys.exit()，而应抛异常让 CLI 层决定退出码？
