# ===== 第629课：终端与命令行应用-终端输出与颜色 =====
# 知识点：
#   - ANSI 转义序列：\x1b[<code>m 设置样式，\x1b[0m 重置
#   - 前景 30~37 / 90~97，背景 40~47 / 100~107；1 加粗、4 下划线、2 暗色
#   - 256 色 38;5;N、真彩色 38;2;R;G;B
#   - 是否启用颜色：isatty() + NO_COLOR / FORCE_COLOR 环境变量 + 非 Windows 判断
#   - 日志/管道场景必须能关色，否则重定向后文件里全是乱码控制符
#   - 光标控制：\r 回车覆写进度、\x1b[K 清行、\x1b[?25l 隐藏光标
#   - 本课不真正打印控制符污染输出，而是生成字符串并展示其 repr / 结构
# 依赖：无（标准库）
import os
import sys

RESET = "\x1b[0m"
STYLES = {"bold": 1, "dim": 2, "italic": 3, "underline": 4, "reverse": 7}
FG = {"black": 30, "red": 31, "green": 32, "yellow": 33,
      "blue": 34, "magenta": 35, "cyan": 36, "white": 37}
BRIGHT = {f"bright_{k}": v + 60 for k, v in FG.items()}


def sgr(*codes) -> str:
    """生成 SGR（Select Graphic Rendition）转义序列。"""
    return "\x1b[" + ";".join(str(c) for c in codes) + "m"


def paint(text, color=None, bg=None, bold=False, enabled=True) -> str:
    """给文本加样式；enabled=False 时原样返回（管道/NO_COLOR 场景）。"""
    if not enabled:
        return text
    codes = []
    if bold:
        codes.append(STYLES["bold"])
    if color:
        code = FG.get(color) or BRIGHT.get(color)
        if code:
            codes.append(code)
    if bg:
        codes.append(FG.get(bg, 40) + 10)
    if not codes:
        return text
    return sgr(*codes) + text + RESET


def truecolor(text, r, g, b) -> str:
    return sgr(38, 2, r, g, b) + text + RESET


def color_enabled(env=None, is_tty=False) -> bool:
    """优先级：FORCE_COLOR > NO_COLOR > isatty。"""
    env = env if env is not None else dict(os.environ)
    if env.get("FORCE_COLOR"):
        return True
    if env.get("NO_COLOR") is not None:
        return False
    return is_tty


print("== 转义序列结构 ==")
print("  sgr(1, 32) =", repr(sgr(1, 32)))
print("  sgr(0)     =", repr(RESET))
print("  加粗绿字   =", repr(paint("OK", "green", bold=True)))

print("\n== 常用颜色表（生成的是字符串，不直接刷屏）==")
for name in list(FG)[:4] + ["bright_cyan"]:
    seq = paint(name, name)
    print(f"  {name:<16} 代码={sgr(FG.get(name) or BRIGHT.get(name))!r:<14} "
          f"长度={len(seq)} 字符（含控制符）")

print("\n== 256 色与真彩色 ==")
print("  256 色 :", repr(sgr(38, 5, 208) + "orange" + RESET))
print("  真彩色 :", repr(truecolor("sky", 135, 206, 235)))

print("\n== 是否启用颜色的判定 ==")
for label, env, tty in (
    ("TTY 终端", {}, True),
    ("重定向到文件", {}, False),
    ("NO_COLOR", {"NO_COLOR": "1"}, True),
    ("FORCE_COLOR", {"FORCE_COLOR": "1", "NO_COLOR": "1"}, False),
    ("CI 环境", {"CI": "true"}, False),
):
    print(f"  {label:<16} -> {color_enabled(env, tty)}")

sample = paint("SUCCESS", "green", bold=True)
print(f"\n  启用时: {sample!r}")
print(f"  关闭时: {paint('SUCCESS', 'green', bold=True, enabled=False)!r}")
visible = "".join(ch for ch in sample if ch.isprintable())
print(f"  去掉控制符后的可见文本: {visible!r}")

print("\n== 进度条（\r 回车覆写）==")
def render_progress(done, total, width=20, enabled=True):
    ratio = done / total
    filled = int(width * ratio)
    bar = "█" * filled + "░" * (width - filled)
    text = f"\r  [{bar}] {ratio:5.1%} ({done}/{total})"
    return paint(text, "cyan", enabled=enabled)

for done in (0, 3, 7, 10):
    print("  " + repr(render_progress(done, 10, enabled=False)))
print("  真实刷新用 print(..., end='', flush=True)，末尾再换行")

print("\n== 光标控制序列 ==")
for name, seq in (("清行", "\x1b[K"), ("隐藏光标", "\x1b[?25l"),
                  ("显示光标", "\x1b[?25h"), ("上移一行", "\x1b[1A")):
    print(f"  {name:<10}: {seq!r}")

print("\n== 表格对齐（不用第三方库）==")
def table(rows, headers):
    widths = [max(len(str(r[i])) for r in [headers, *rows]) for i in range(len(headers))]
    fmt = "  " + "  ".join(f"{{:<{w}}}" for w in widths)
    out = [fmt.format(*headers), "  " + "-" * (sum(widths) + 2 * (len(widths) - 1))]
    out += [fmt.format(*[str(v) for v in r]) for r in rows]
    return "\n".join(out)

print(table([("serve", "启动", 12), ("init", "初始化", 5), ("status", "状态", 3)],
            ("命令", "说明", "调用次数")))

print("\n== 兼容性建议 ==")
for line in [
    "Windows 10+ 终端支持 ANSI，老版需 colorama 或 os.system('') 启用 VT 模式",
    "写日志/输出到管道时强制关色，保留纯文本",
    "尊重 NO_COLOR 社区约定（https://no-color.org）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 strip_ansi(text) 用正则去掉所有转义序列，便于日志落盘。
# 2. 写一个支持标题/成功/警告/错误四级样式的 logger，并可用 NO_COLOR 关闭。
# 3. 用 \r + \x1b[K 实现一个不换行的多任务进度条。
# 4. 思考：为什么 print 到管道时默认关色，而不是让接收方自己处理？
