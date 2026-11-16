# ===== 第633课：终端与命令行应用-命令管道与文本流处理 =====
# 知识点：
#   - Unix 管道哲学：每个程序只做一件事，输入输出都是文本流，用 | 组合
#   - Python 里用「生成器 + 可迭代行」模拟管道，惰性求值、内存恒定
#   - 常见过滤器：grep（筛）、sed（替换）、cut（取列）、sort、uniq、head、wc
#   - 逐行处理而不是 read() 全读入；大文件也能流式跑
#   - itertools.islice / groupby / tee 是实现流算子的好工具
#   - 与 subprocess.Popen(stdout=PIPE) 对接真实外部命令时，同样按行迭代
# 依赖：无（标准库）
import io
import itertools
from collections import Counter


def read_lines(text):
    """把一段文本变成惰性行迭代器（模拟 stdin）。"""
    for line in io.StringIO(text):
        yield line.rstrip("\n")


def grep(lines, pattern, invert=False):
    for line in lines:
        hit = pattern in line
        if hit != invert:
            yield line


def replace(lines, old, new, count=-1):
    for line in lines:
        yield line.replace(old, new) if count < 0 else line.replace(old, new, count)


def cut(lines, sep, fields):
    for line in lines:
        cols = line.split(sep)
        yield sep.join(cols[i] for i in fields if i < len(cols))


def head(lines, n):
    yield from itertools.islice(lines, n)


def upper(lines):
    for line in lines:
        yield line.upper()


def number(lines, start=1):
    for i, line in enumerate(lines, start):
        yield f"{i:>3}  {line}"


def unique(lines):
    """只去掉相邻重复行（等价于 uniq，需先 sort）。"""
    prev = object()
    for line in lines:
        if line != prev:
            yield line
        prev = line


def wordcount(lines):
    n = chars = 0
    for line in lines:
        n += 1
        chars += len(line)
    return n, chars


LOG = """\
2026-11-14 09:00 INFO  user=alice action=login
2026-11-14 09:01 ERROR user=bob action=pay code=500
2026-11-14 09:01 INFO  user=alice action=view
2026-11-14 09:02 WARN  user=carol action=pay code=402
2026-11-14 09:03 ERROR user=bob action=pay code=500
2026-11-14 09:04 INFO  user=dave action=logout
"""

print("== 管道 1：筛选 ERROR 并加行号 ==")
p1 = number(grep(read_lines(LOG), "ERROR"))
for line in p1:
    print("  " + line)

print("\n== 管道 2：取 user 列 + 去重 + 计数 ==")
# 先把 "user=xxx" 抽出来
def extract_user(lines):
    for line in lines:
        for part in line.split():
            if part.startswith("user="):
                yield part.split("=", 1)[1]

users = list(extract_user(read_lines(LOG)))
print("  原始:", users)
print("  去重:", sorted(set(users)))
print("  频次:", dict(Counter(users)))

print("\n== 管道 3：sort | uniq | head ==")
levels = [line.split()[2] for line in read_lines(LOG)]
uniq_sorted = list(head(unique(iter(sorted(levels))), 3))
print("  排序后相邻去重取前 3:", uniq_sorted)

print("\n== 管道 4：替换 + 转大写 ==")
p4 = head(upper(replace(grep(read_lines(LOG), "pay"), "pay", "PAYMENT")), 2)
for line in p4:
    print("  " + line)

print("\n== 管道 5：wc（-l 与 -c）==")
n, chars = wordcount(read_lines(LOG))
print(f"  行数={n}  字符数(不含换行)={chars}")
print(f"  词数={sum(len(l.split()) for l in read_lines(LOG))}")

print("\n== 惰性：处理 100 万行只取前 3 ==")
def infinite_counter():
    i = 0
    while True:
        yield f"line-{i}"
        i += 1

first3 = list(head(infinite_counter(), 3))
print("  前 3 行:", first3, "（无限流也能安全取 head）")

print("\n== 用 subprocess 对接真实命令（Windows 用 findstr 类比）==")
import subprocess
import sys
cmd = ["findstr", "ERROR"] if sys.platform == "win32" else ["grep", "ERROR"]
try:
    r = subprocess.run(cmd, input=LOG, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=10)
    print(f"  {' '.join(cmd)} -> 返回码={r.returncode}，命中 {len(r.stdout.splitlines())} 行")
except (FileNotFoundError, subprocess.TimeoutExpired) as e:
    print("  外部命令不可用（不影响本课主流程）:", type(e).__name__)

print("\n== 真实 stdin/stdout 写法 ==")
for line in (
    "for line in sys.stdin:      # 逐行，惰性",
    "    print(transform(line), end='')",
    "$ cat app.log | python filter.py | sort | uniq -c",
):
    print("  " + line)

print("\n== 工程要点 ==")
for line in [
    "生成器链惰性求值：任一下游提前 break，上游不会继续读文件",
    "每行只保留当前行，内存 O(1)，适合 GB 级日志",
    "sort 需要全量内存（或外部排序），是管道里少数的非惰性算子",
    "二进制流用 sys.stdin.buffer / sys.stdout.buffer，文本流才用 str",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 tail(n) 流算子（提示：collections.deque(maxlen=n)）。
# 2. 实现 awk 风格算子：按分隔符取第 N 列并支持条件表达式过滤。
# 3. 用 subprocess.Popen 逐行读取外部命令输出，边读边处理不落盘。
# 4. 思考：为什么 sort 无法做成真正的惰性算子？大数据量下怎么解决？
