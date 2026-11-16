# ===== 第685课：表达式解析与解释器-Pratt解析器与优先级 =====
# 知识点：
#   - Pratt（优先级爬升）解析器：给每个运算符一个 binding power，用一张表驱动
#   - nud（前缀/原子如何处理）、led（中缀如何处理）是核心两个扩展点
#   - 左结合用 (lbp, lbp+1)，右结合用 (lbp, lbp)；加新运算符只改表
#   - 相比递归下降：不用为每层优先级写一个函数，运算符多时更紧凑
#   - 三元条件 ?:、赋值、自定义运算符都能自然纳入 led
#   - 本课复用第684课 AST 节点，实现另一套解析器作对比
# 依赖：无（标准库）
from dataclasses import dataclass


@dataclass
class Num:
    value: float
@dataclass
class Var:
    name: str
@dataclass
class BinOp:
    op: str
    left: object
    right: object
@dataclass
class UnaryOp:
    op: str
    operand: object
@dataclass
class Cond:
    cond: object
    then: object
    else_: object


def tokenize(src):
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1; continue
        if c.isdigit() or (c == "." and i + 1 < n and src[i + 1].isdigit()):
            start, dot = i, False
            while i < n and (src[i].isdigit() or (src[i] == "." and not dot)):
                if src[i] == ".":
                    dot = True
                i += 1
            out.append(("NUM", src[start:i])); continue
        if c.isalpha() or c == "_":
            start = i
            while i < n and (src[i].isalnum() or src[i] == "_"):
                i += 1
            out.append(("IDENT", src[start:i])); continue
        two = src[i:i + 2]
        if two in ("**", "//", "==", "!=", ">=", "<="):
            out.append(("OP", two)); i += 2; continue
        if c in "+-*/%^()?:,=<>":
            out.append((c, c)); i += 1; continue
        raise ValueError(f"非法字符 {c!r} @ {i}")
    out.append(("EOF", ""))
    return out


# (左绑定力, 右绑定力)：右 < 左 => 左结合；右 == 左 => 右结合
INFIX = {
    "?": (10, 10),
    "or": (20, 21), "and": (30, 31),
    "==": (40, 41), "!=": (40, 41),
    "<": (50, 51), "<=": (50, 51), ">": (50, 51), ">=": (50, 51),
    "+": (60, 61), "-": (60, 61),
    "*": (70, 71), "/": (70, 71), "//": (70, 71), "%": (70, 71),
    "**": (90, 90),          # 右结合：右 bp == 左 bp
}
PREFIX_BP = {"+": 80, "-": 80, "not": 35}


class Pratt:
    def __init__(self, tokens):
        self.toks, self.i = tokens, 0

    @property
    def cur(self):
        return self.toks[self.i]

    def advance(self):
        t = self.cur
        self.i += 1
        return t

    def parse(self, rbp=0):
        t = self.advance()
        left = self.nud(t)
        while True:
            op = self.cur[1]
            if op not in INFIX or INFIX[op][0] <= rbp:
                break
            lbp, rbp_next = INFIX[op]
            left = self.led(op, left, rbp_next)
        return left

    def nud(self, t):
        kind, val = t
        if kind == "NUM":
            return Num(float(val))
        if kind == "IDENT":
            if val in PREFIX_BP:                 # not 作为前缀
                return UnaryOp(val, self.parse(PREFIX_BP[val]))
            return Var(val)
        if val in ("+", "-"):
            return UnaryOp(val, self.parse(PREFIX_BP[val]))
        if val == "(":
            node = self.parse(0)
            if self.advance()[1] != ")":
                raise SyntaxError("缺少 )")
            return node
        raise SyntaxError(f"无法作为前缀: {val!r}")

    def led(self, op, left, rbp):
        self.advance()                          # 吃掉运算符
        if op == "?":
            then = self.parse(0)
            if self.advance()[1] != ":":
                raise SyntaxError("三元表达式缺少 :")
            else_ = self.parse(rbp)
            return Cond(left, then, else_)
        right = self.parse(rbp)
        return BinOp(op, left, right)


def parse(src):
    p = Pratt(tokenize(src))
    node = p.parse(0)
    if p.cur[0] != "EOF":
        raise SyntaxError(f"多余输入: {p.cur[1]!r}")
    return node


def shape(n):
    if isinstance(n, BinOp):
        return f"({n.op} {shape(n.left)} {shape(n.right)})"
    if isinstance(n, UnaryOp):
        return f"({n.op}{shape(n.operand)})"
    if isinstance(n, Cond):
        return f"(?: {shape(n.cond)} {shape(n.then)} {shape(n.else_)})"
    if isinstance(n, Num):
        return f"{n.value:g}"
    return n.name


print("== 优先级表 ==")
for op, (l, r) in sorted(INFIX.items(), key=lambda kv: kv[1][0]):
    assoc = "右结合" if r == l else "左结合"
    print(f"  {op:<5} lbp={l:<3} rbp={r:<3} {assoc}")

print("\n== 解析结果（前缀记法） ==")
cases = [
    "1 + 2 * 3",
    "1 - 2 - 3",              # 左结合
    "2 ** 3 ** 2",            # 右结合
    "-2 ** 2",
    "a + b * c > 10 and x != 0",
    "x > 0 ? 1 : -1",
    "not a == b",
    "1 + 2 * 3 ** 2 - 4 / 2",
]
for c in cases:
    print(f"  {c:<32} -> {shape(parse(c))}")

print("\n== 结合性对照 ==")
print("  1-2-3 左结合 ->", shape(parse("1-2-3")), "（等价于 (1-2)-3）")
print("  2**3**2 右结合 ->", shape(parse("2**3**2")), "（等价于 2**(3**2)）")

print("\n== 新增运算符的成本 ==")
print("  Pratt: 在 INFIX 加一行 (lbp, rbp) 即可，无需新增解析函数")
print("  递归下降: 需在对应优先级层加分支，运算符多时函数膨胀")
print("  例：加 | 位或（lbp=25）只需 INFIX['|']=(25,26)")

print("\n== 错误输入 ==")
for bad in ("1 +", "? 2", "x ? 1", "(1", "1 ** ** 2"):
    try:
        parse(bad)
        print(f"  {bad!r:<12} 通过（需检查）")
    except (SyntaxError, ValueError) as e:
        print(f"  {bad!r:<12} -> {type(e).__name__}: {e}")

print("\n== Pratt vs 递归下降 ==")
for line in (
    "  递归下降: 产生式直观、易读，适合语法层级固定（如 SQL/配置）",
    "  Pratt   : 运算符表驱动，扩展运算符极廉价，适合表达式密集语言",
    "  两者可混用：语句用递归下降，表达式内嵌 Pratt",
    "  CPython 的 PEG 解析器是另一条路线（peg_generator）",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 给 Pratt 增加位运算 | & ^ << >>，并验证优先级低于比较、高于加减。
# 2. 实现赋值 = 的右结合 led，解析 a = b = 3。
# 3. 增加函数调用 f(x, y) 作为 nud 的一种形式。
# 4. 思考：为什么右结合运算符要让 rbp 等于 lbp？
