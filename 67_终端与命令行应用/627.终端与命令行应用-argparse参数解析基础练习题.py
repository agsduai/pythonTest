# ===== 第627课：终端与命令行应用-argparse参数解析基础 =====
# 知识点：
#   - argparse：把 sys.argv 解析成结构化参数，自动生成 -h/--help 与错误提示
#   - add_argument 的常用参数：type、default、choices、required、nargs、action
#   - 位置参数（无前缀）与可选参数（-x/--xxx）的区别
#   - action="store_true"/"count"/"append"：标志位、计数、多值
#   - parse_args() 读真实命令行；parse_args(list) 可传入列表，便于测试
#   - 生产 CLI 把 main(argv=None) 暴露出来，单测时传列表，避免依赖真实 stdin
# 依赖：无（标准库）
import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="demo",
        description="argparse 基础演示：一个假想的文件统计工具",
        epilog="示例：python demo.py data.txt -n 3 -v --mode fast",
    )
    p.add_argument("path", help="要处理的文件路径（位置参数）")
    p.add_argument("-n", "--lines", type=int, default=5, help="显示行数（默认 5）")
    p.add_argument("--mode", choices=("fast", "slow", "auto"), default="auto",
                   help="运行模式")
    p.add_argument("-v", "--verbose", action="store_true", help="输出详细信息")
    p.add_argument("-q", "--quiet", action="count", default=0, help="降低噪声，可重复 -qq")
    p.add_argument("--tag", action="append", default=[], help="附加标签，可重复")
    p.add_argument("--ratio", type=float, default=1.0, help="浮点比例")
    p.add_argument("--no-cache", dest="cache", action="store_false",
                   help="关闭缓存（默认开启）")
    p.set_defaults(cache=True)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    print("== 解析结果 ==")
    print(f"  path   = {args.path}")
    print(f"  lines  = {args.lines}  mode = {args.mode}  ratio = {args.ratio}")
    print(f"  verbose= {args.verbose}  quiet = {args.quiet}  cache = {args.cache}")
    print(f"  tags   = {args.tag}")
    return 0


print("== 模拟不同命令行 ==")
cases = [
    ["data.txt"],
    ["data.txt", "-n", "3", "-v", "--mode", "fast"],
    ["data.txt", "-qq", "--tag", "a", "--tag", "b", "--no-cache"],
]
for case in cases:
    print(f"\n$ demo {' '.join(case)}")
    main(case)

print("\n== 帮助文本（前 12 行）==")
help_text = build_parser().format_help()
for line in help_text.splitlines()[:12]:
    print("  " + line)

print("\n== 错误提示示例 ==")
p = build_parser()
try:
    p.parse_args(["data.txt", "--mode", "unknown"])
except SystemExit as e:
    print(f"  非法 choices 触发 SystemExit(code={e.code})，argparse 会打印用法到 stderr")

print("\n== 参数类型陷阱 ==")
for raw in ("5", "abc"):
    try:
        p.parse_args(["data.txt", "-n", raw])
        print(f"  -n {raw!r}: 解析成功")
    except SystemExit:
        print(f"  -n {raw!r}: type=int 转换失败，argparse 自动报错并退出")

print("\n== 真实 argv ==")
print("  sys.argv =", sys.argv[:1], "...（本示例统一用可注入的 argv 做演示）")

# ===== 练习题 =====
# 1. 增加 --output 参数，用 type=argparse.FileType("w") 直接得到文件对象。
# 2. 用 mutually_exclusive_group() 让 --fast 与 --safe 互斥。
# 3. 给 main() 写 3 组单元测试，覆盖默认值、choices 报错、action="append"。
# 4. 思考：为什么把 parser 构造放进函数、main 接收 argv，比在模块顶层直接 parse_args() 更好测？
