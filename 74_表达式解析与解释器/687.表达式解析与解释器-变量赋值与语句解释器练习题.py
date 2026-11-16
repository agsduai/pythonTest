# ===== 第687课：表达式解析与解释器-变量赋值与语句解释器 =====
# 知识点：
#   - 从「表达式」升级到「语句」：赋值、print、if、while、块
#   - 程序 = 语句列表；解释器按顺序执行，语句可改变环境 env
#   - 语句用缩进块表示（简化：按行首空格数栈），不实现完整语法
#   - if/while 的条件复用表达式求值器，执行体是子语句列表
#   - 赋值既支持新建变量也支持更新；作用域先做单层（下一课做函数）
#   - 用「解析成语句 AST -> 执行」两段式，避免边读边执行的耦合
# 依赖：无（标准库）
from dataclasses import dataclass, field

# ---- 极简表达式求值（复用第686课思路，内联） ----
import operator

OPS = {"+": operator.add, "-": operator.sub, "*": operator.mul,
       "/": operator.truediv, "//": operator.floordiv, "%": operator.mod,
       "**": operator.pow,
       "==": operator.eq, "!=": operator.ne, ">": operator.gt,
       "<": operator.lt, ">=": operator.ge, "<=": operator.le}


def eval_expr(src, env):
    """受限求值：变量、数字、算术/比较、括号。用 token 扫描 + 递归下降。"""
    toks, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1; continue
        if c.isdigit():
            j = i
            while j < n and src[j].isdigit(): j += 1
            toks.append(("N", src[i:j])); i = j; continue
        if c.isalpha() or c == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"): j += 1
            toks.append(("V", src[i:j])); i = j; continue
        two = src[i:i+2]
        if two in ("==", "!=", ">=", "<=", "//", "**"):
            toks.append(("O", two)); i += 2; continue
        if c in "+-*/%()<>":
            toks.append((c, c)); i += 1; continue
        raise ValueError(f"非法字符 {c!r}")
    toks.append(("EOF", ""))
    pos = [0]

    def cur(): return toks[pos[0]]
    def eat(v=None):
        t = cur()
        if v is not None and t[1] != v: raise SyntaxError(f"期望 {v!r}")
        pos[0] += 1; return t

    def primary():
        k, v = cur()
        if k == "N": eat(); return float(v)
        if k == "V":
            eat()
            if v not in env: raise NameError(f"未定义变量 {v}")
            return env[v]
        if v == "(":
            eat("("); x = expr(); eat(")"); return x
        if v == "-":
            eat(); return -primary()
        raise SyntaxError(f"意外 {v!r}")

    def power():
        x = primary()
        if cur()[1] == "**": eat(); return x ** primary()
        return x

    def term():
        x = power()
        while cur()[1] in ("*", "/", "//", "%"):
            op = eat()[1]; x = OPS[op](x, power())
        return x

    def expr():
        x = term()
        while cur()[1] in ("+", "-"):
            op = eat()[1]; x = OPS[op](x, term())
        while cur()[1] in ("==", "!=", ">", "<", ">=", "<="):
            op = eat()[1]; x = OPS[op](x, term())
        return x

    out = expr()
    if cur()[0] != "EOF": raise SyntaxError("多余输入")
    return out


# ---- 语句 AST ----
@dataclass
class Assign:
    name: str
    expr: str
@dataclass
class Print:
    expr: str
@dataclass
class If:
    cond: str
    body: list
    else_body: list = field(default_factory=list)
@dataclass
class While:
    cond: str
    body: list


def parse_program(lines):
    """按缩进解析语句列表；返回语句 AST 列表。"""
    prepared = []
    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        prepared.append((indent, line.strip()))
    def block(idx, level):
        out = []
        while idx < len(prepared):
            ind, text = prepared[idx]
            if ind < level:
                break
            if ind > level:
                raise SyntaxError(f"意外缩进: {text}")
            head = text.split(None, 1)[0]
            if head in ("if", "while"):
                rest = text[len(head):].strip()
                cond = rest[:-1].strip() if rest.endswith(":") else rest
                idx += 1
                body, idx = block(idx, level + 2)
                else_body = []
                if idx < len(prepared) and prepared[idx][1] == "else:" and prepared[idx][0] == level:
                    idx += 1
                    else_body, idx = block(idx, level + 2)
                node = If(cond, body, else_body) if head == "if" else While(cond, body)
                out.append(node)
            elif text.startswith("print "):
                out.append(Print(text[6:].strip())); idx += 1
            elif "=" in text:
                name, e = text.split("=", 1)
                out.append(Assign(name.strip(), e.strip())); idx += 1
            else:
                raise SyntaxError(f"无法解析语句: {text}")
        return out, idx
    stmts, _ = block(0, 0)
    return stmts


class Interp:
    def __init__(self, max_steps=1000):
        self.env = {}
        self.output = []
        self.steps = 0
        self.max_steps = max_steps

    def exec_block(self, stmts):
        for s in stmts:
            self.steps += 1
            if self.steps > self.max_steps:
                raise RuntimeError("超过最大执行步数，可能存在死循环")
            self.exec_stmt(s)

    def exec_stmt(self, s):
        if isinstance(s, Assign):
            self.env[s.name] = eval_expr(s.expr, self.env)
        elif isinstance(s, Print):
            self.output.append(str(eval_expr(s.expr, self.env)))
        elif isinstance(s, If):
            branch = s.body if eval_expr(s.cond, self.env) else s.else_body
            self.exec_block(branch)
        elif isinstance(s, While):
            guard = 0
            while eval_expr(s.cond, self.env):
                guard += 1
                if guard > self.max_steps:
                    raise RuntimeError("while 疑似死循环")
                self.exec_block(s.body)
        else:
            raise TypeError(f"未知语句: {s}")


PROGRAM = """\
# 计算 1..5 的累加与阶乘
n = 5
total = 0
i = 1
while i <= n:
  total = total + i
  i = i + 1
print total
fact = 1
j = 1
while j <= n:
  fact = fact * j
  j = j + 1
print fact
if fact > 100:
  print 999
else:
  print 0
"""

print("== 语句 AST ==")
prog = parse_program(PROGRAM.splitlines())
for s in prog:
    if isinstance(s, If):
        print(f"  If(cond={s.cond!r}, body={len(s.body)} 语句, "
              f"else={len(s.else_body)})")
    elif isinstance(s, While):
        print(f"  While(cond={s.cond!r}, body={len(s.body)} 语句)")
    else:
        print(f"  {s}")

print("\n== 执行结果 ==")
itp = Interp()
itp.exec_block(prog)
print("  output:", itp.output)
print("  期望: total=15, fact=120, 999")
print("  最终 env:", {k: int(v) if float(v).is_integer() else v
                    for k, v in itp.env.items()})

print("\n== if 分支选择 ==")
for src in ("x = 3\nif x > 5:\n  print 1\nelse:\n  print 2\n",
            "x = 9\nif x > 5:\n  print 1\nelse:\n  print 2\n"):
    i2 = Interp(); i2.exec_block(parse_program(src.splitlines()))
    print(f"  x={i2.env['x']:.0f} -> {i2.output}")

print("\n== 死循环保护 ==")
try:
    i3 = Interp(max_steps=50)
    i3.exec_block(parse_program("i = 0\nwhile i >= 0:\n  i = i + 1\n".splitlines()))
except RuntimeError as e:
    print("  ", type(e).__name__, e)

print("\n== 语句 vs 表达式 ==")
for line in (
    "  表达式: 有值、可嵌套、无副作用（本实现里）",
    "  语句  : 有副作用（改 env / 输出 / 控制流），顺序执行",
    "  解释器 = 语句求值器 + 共享 env；表达式求值器被反复调用",
    "  真实语言还需：函数、作用域、返回、异常、类型系统",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 增加 `if/elif/else` 链，支持多分支条件。
# 2. 实现 break / continue 语句（用专用异常跳出循环）。
# 3. 给 print 增加多参数与字符串字面量支持。
# 4. 思考：为什么解释器需要 max_steps 保护，而编译型语言不需要？
