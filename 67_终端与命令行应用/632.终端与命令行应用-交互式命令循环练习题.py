# ===== 第632课：终端与命令行应用-交互式命令循环 =====
# 知识点：
#   - REPL（Read-Eval-Print-Loop）：读取一行 -> 解析 -> 执行 -> 打印结果 -> 循环
#   - 用可注入的 input_fn / output_fn 代替真实 stdin/stdout，整个循环可单测
#   - 命令表用 dict[str, callable] 分发，新增命令只改表、不改循环
#   - 解析：shlex.split() 正确处理引号与转义，比 str.split() 稳健
#   - 退出用专用异常或哨兵值，不要用 sys.exit() 打断可测试的循环
#   - 未知命令给出 help 提示；空行与注释行直接跳过
# 依赖：无（标准库）
import io
import shlex


class QuitLoop(Exception):
    """用于退出 REPL 的内部信号。"""


class Shell:
    def __init__(self):
        self.vars = {}
        self.history = []
        self.commands = {
            "set": self.cmd_set, "get": self.cmd_get, "del": self.cmd_del,
            "list": self.cmd_list, "add": self.cmd_add, "echo": self.cmd_echo,
            "history": self.cmd_history, "help": self.cmd_help,
            "quit": self.cmd_quit, "exit": self.cmd_quit,
        }

    def cmd_set(self, args, out):
        if len(args) != 2:
            raise ValueError("用法: set <key> <value>")
        self.vars[args[0]] = args[1]
        print(f"已设置 {args[0]}={args[1]}", file=out)

    def cmd_get(self, args, out):
        if len(args) != 1:
            raise ValueError("用法: get <key>")
        print(self.vars.get(args[0], "(未设置)"), file=out)

    def cmd_del(self, args, out):
        if len(args) != 1:
            raise ValueError("用法: del <key>")
        removed = self.vars.pop(args[0], None)
        print(f"已删除 {args[0]}" if removed is not None else f"{args[0]} 不存在", file=out)

    def cmd_list(self, args, out):
        if not self.vars:
            print("(空)", file=out)
        for k, v in sorted(self.vars.items()):
            print(f"  {k} = {v}", file=out)

    def cmd_add(self, args, out):
        if not args:
            raise ValueError("用法: add <数字...>")
        nums = [float(x) for x in args]
        print(f"和 = {sum(nums):g}", file=out)

    def cmd_echo(self, args, out):
        print(" ".join(args), file=out)

    def cmd_history(self, args, out):
        for i, line in enumerate(self.history, 1):
            print(f"  {i:>2}  {line}", file=out)

    def cmd_help(self, args, out):
        print("可用命令: " + ", ".join(sorted(self.commands)), file=out)

    def cmd_quit(self, args, out):
        print("bye", file=out)
        raise QuitLoop

    def execute(self, line: str, out) -> bool:
        """执行一行，返回是否继续循环。"""
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            return True
        self.history.append(stripped)
        try:
            parts = shlex.split(stripped)
        except ValueError as e:
            print(f"解析错误: {e}", file=out)
            return True
        cmd, args = parts[0], parts[1:]
        fn = self.commands.get(cmd)
        if fn is None:
            print(f"未知命令: {cmd}（输入 help 查看可用命令）", file=out)
            return True
        try:
            fn(args, out)
        except (ValueError, KeyError) as e:
            print(f"错误: {e}", file=out)
        return True

    def run(self, lines, out):
        """从可迭代的输入行驱动 REPL，便于测试与回放。"""
        for line in lines:
            try:
                if not self.execute(line, out):
                    break
            except QuitLoop:
                break


script = [
    "# 这是一行注释",
    "",
    "help",
    "set name 'Zhang San'",
    "set city Beijing",
    'echo "hello world"',
    "get name",
    "add 1 2 3 4.5",
    "list",
    "del city",
    "get city",
    "unknown_cmd",
    "set broken",
    "add a b",
    "history",
    "quit",
    "echo 这行不会执行",
]
out = io.StringIO()
shell = Shell()
shell.run(script, out)
print("== REPL 回放输出 ==")
print(out.getvalue(), end="")

print("\n== 状态快照 ==")
print("  最终变量:", shell.vars)
print(f"  历史条数: {len(shell.history)}（注释与空行未计入）")
print("  退出后不再执行后续输入:", "这行不会执行" not in out.getvalue())

print("\n== shlex 与 str.split 的差异 ==")
for text in ('echo "hello world"', "set path 'C:\\my docs'", "echo a\\ b"):
    print(f"  {text!r}")
    print(f"    str.split -> {text.split()}")
    print(f"    shlex     -> {shlex.split(text)}")

print("\n== 命令表分发 ==")
print("  命令数:", len(shell.commands))
print("  dict 查找 O(1)；新增命令只需注册一个函数，循环体不变")

print("\n== 工程要点 ==")
for line in [
    "input_fn/output_fn 注入：测试用列表回放，生产接 sys.stdin/sys.stdout",
    "退出用异常/哨兵，不用 sys.exit()，否则单测会捕获到 SystemExit",
    "命令函数只负责业务，不直接读全局 stdin，便于组合与复用",
    "生产 REPL 还应处理 Ctrl+C（KeyboardInterrupt）与 EOF（EOFError）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加 save/load 命令，把变量持久化到 JSON 文件（用临时目录）。
# 2. 实现命令补全提示：输入前缀时列出所有匹配的命令名。
# 3. 处理 KeyboardInterrupt 与 EOFError，让 REPL 优雅退出而不是崩溃。
# 4. 思考：为什么用 shlex.split 而不是 str.split？哪些字符需要转义？
