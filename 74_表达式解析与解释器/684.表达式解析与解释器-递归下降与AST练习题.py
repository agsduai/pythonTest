# ===== 第684课：表达式解析与解释器-递归下降与AST =====
# 知识点：
#   - 语法用「优先级分层」表达：expr -> term -> factor -> primary
#   - 每层对应一个函数，左结合用 while 循环消费同优先级运算符
#   - 右结合（如 **）用递归而非循环
#   - AST 节点：Num / Var / BinOp / UnaryOp / Call，用 dataclass 承载
#   - 产生式与代码一一对应，是最易读的手写解析器写法
#   - 解析只建树，不求值；求值与语法解耦（下一课）
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
class Call:
    name: str
    args: list


# ---- 复用极简 lexer ----
def tokenize(src):
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1; continue
        if c.isdigit() or (c == "." and i + 1 < n and src[i + 1].isdigit()):
            start = i; dot = False
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
        if c in "+-*/%^()<>,=":
            out.append(("OP" if c not in "()," else c, c)); i += 1; continue
        raise ValueError(f"非法字符 {c!r} @ {i}")
    out.append(("EOF", ""))
    return out


class Parser:
    """递归下降：expr(+-) -> term(*/) -> power(**) -> unary -> primary。"""
    def __init__(self, tokens):
        self.toks, self.i = tokens, 0

    @property
    def cur(self):
        return self.toks[self.i]

    def eat(self, value=None):
        t = self.cur
        if value is not None and t[1] != value:
            raise SyntaxError(f"期望 {value!r}，实际 {t[1]!r}")
        self.i += 1
        return t

    def parse(self):
        node = self.expr()
        if self.cur[0] != "EOF":
            raise SyntaxError(f"多余输入: {self.cur[1]!r}")
        return node

    def expr(self):
        node = self.term()
        while self.cur[1] in ("+", "-"):
            op = self.eat()[1]
            node = BinOp(op, node, self.term())
        return node

    def term(self):
        node = self.unary()
        while self.cur[1] in ("*", "/", "//", "%"):
            op = self.eat()[1]
            node = BinOp(op, node, self.unary())
        return node

    def unary(self):
        if self.cur[1] in ("+", "-"):
            op = self.eat()[1]
            return UnaryOp(op, self.unary())
        return self.power()

    def power(self):
        node = self.primary()
        if self.cur[1] == "**":
            self.eat()
            return BinOp("**", node, self.unary())   # 右结合
        return node

    def primary(self):
        kind, val = self.cur
        if kind == "NUM":
            self.eat()
            return Num(float(val))
        if kind == "IDENT":
            name = self.eat()[1]
            if self.cur[1] == "(":
                self.eat("(")
                args = []
                if self.cur[1] != ")":
                    args.append(self.expr())
                    while self.cur[1] == ",":
                        self.eat(",")
                        args.append(self.expr())
                self.eat(")")
                return Call(name, args)
            return Var(name)
        if val == "(":
            self.eat("(")
            node = self.expr()
            self.eat(")")
            return node
        raise SyntaxError(f"意外的 token: {val!r}")


def dump(node, indent=0):
    pad = "  " * indent
    if isinstance(node, Num):
        print(pad + f"Num({node.value:g})")
    elif isinstance(node, Var):
        print(pad + f"Var({node.name})")
    elif isinstance(node, UnaryOp):
        print(pad + f"Unary({node.op})"); dump(node.operand, indent + 1)
    elif isinstance(node, BinOp):
        print(pad + f"BinOp({node.op})")
        dump(node.left, indent + 1); dump(node.right, indent + 1)
    elif isinstance(node, Call):
        print(pad + f"Call({node.name}, {len(node.args)} args)")
        for a in node.args:
            dump(a, indent + 1)


def parse(src):
    return Parser(tokenize(src)).parse()

print("== AST：1 + 2 * 3 ==")
dump(parse("1 + 2 * 3"))

print("\n== AST：-2 ** 2（幂优先于一元负号） ==")
dump(parse("-2 ** 2"))

print("\n== AST：max(a+1, 3) ==")
dump(parse("max(a + 1, 3)"))

print("\n== 优先级与结合性验证（结构对比） ==")
cases = [
    "1+2*3", "(1+2)*3", "2**3**2", "-2**2", "(-2)**2",
    "a+b*c-d", "1/2/4", "10//3%2",
]
for c in cases:
    print(f"  {c:<12} -> ", end="")
    root = parse(c)
    # 只打印根与顶层右子树的运算符，直观看出结合性
    def shape(n):
        if isinstance(n, BinOp):
            right = n.right
            r = f" BinOp({right.op})" if isinstance(right, BinOp) else ""
            return f"BinOp({n.op})" + r
        if isinstance(n, UnaryOp):
            return f"Unary({n.op})->" + shape(n.operand)
        if isinstance(n, Call):
            return f"Call({n.name})"
        return type(n).__name__
    print(shape(root))

print("\n== 语法错误 ==")
for bad in ("1 +", "(1 + 2", "1 ** ** 2", "* 3", "max(1,)"):
    try:
        parse(bad)
        print(f"  {bad!r:<12} 通过（需检查）")
    except (SyntaxError, ValueError) as e:
        print(f"  {bad!r:<12} -> {type(e).__name__}: {e}")

print("\n== 产生式与代码对应 ==")
for line in (
    "  expr   := term (('+'|'-') term)*        左结合，while 循环",
    "  term   := unary (('*'|'/'|'//'|'%') unary)*",
    "  unary  := ('+'|'-') unary | power       递归，支持连续负号",
    "  power  := primary ('**' unary)?         右结合，递归到 unary",
    "  primary:= NUM | IDENT | IDENT '(' args ')' | '(' expr ')'",
):
    print(line)

# ===== 练习题 =====
# 1. 增加比较运算符（< <= > >= == !=）与 and/or/not，形成完整布尔表达式。
# 2. 实现 AST 的 to_source()，把树还原成带最少括号的表达式字符串。
# 3. 给 Parser 增加行号/列号，语法错误时报告精确位置。
# 4. 思考：为什么乘除用 while 循环（左结合），幂用递归（右结合）？
