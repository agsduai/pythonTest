# ===== 第690课：表达式解析与解释器-综合案例-迷你公式DSL引擎 =====
# 知识点：
#   - 综合串起本章：lexer -> Pratt/递归下降 parser -> AST -> 编译字节码 -> VM 执行
#   - 一个可用的公式引擎：变量、算术、比较、逻辑、函数调用、条件表达式、注释
#   - 分层：Formula(编译一次) -> eval(env) 多次求值；符号表可注入、内置函数白名单
#   - 安全：不支持属性访问/下标/任意调用，无法逃逸到 Python 运行时
#   - 常量折叠与「编译缓存」：同一公式字符串只解析一次
#   - 应用：报表指标、风控规则、定价公式、动态配置（第673课规则引擎可复用）
# 依赖：无（标准库）
import math
import operator
from dataclasses import dataclass


# ---------- 1) Lexer ----------
def tokenize(src):
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1; continue
        if c == "#":                       # 行注释
            while i < n and src[i] != "\n": i += 1
            continue
        if c.isdigit() or (c == "." and i + 1 < n and src[i + 1].isdigit()):
            start, dot = i, False
            while i < n and (src[i].isdigit() or (src[i] == "." and not dot)):
                if src[i] == ".":
                    dot = True
                i += 1
            out.append(("NUM", src[start:i])); continue
        if c.isalpha() or c == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"): j += 1
            out.append(("IDENT", src[i:j])); i = j; continue
        two = src[i:i + 2]
        if two in ("**", "//", "==", "!=", ">=", "<=", "&&", "||"):
            out.append(("OP", two)); i += 2; continue
        if c in "+-*/%()?:,!<>":
            out.append((c, c)); i += 1; continue
        raise ValueError(f"非法字符 {c!r} @ {i}")
    out.append(("EOF", ""))
    return out


# ---------- 2) Parser（递归下降，带比较/逻辑/三元） ----------
@dataclass
class Node:
    kind: str
    value: object = None
    kids: list = None

    def __post_init__(self):
        if self.kids is None:
            self.kids = []


class Parser:
    def __init__(self, toks): self.t, self.i = toks, 0
    @property
    def cur(self): return self.t[self.i]
    def eat(self, v=None):
        x = self.cur
        if v is not None and x[1] != v:
            raise SyntaxError(f"期望 {v!r}，实际 {x[1]!r}")
        self.i += 1; return x
    def parse(self):
        n = self.expr()
        if self.cur[0] != "EOF": raise SyntaxError(f"多余输入 {self.cur[1]!r}")
        return n
    def expr(self):
        n = self.compare()
        if self.cur[1] == "?":
            self.eat("?"); then = self.expr(); self.eat(":"); other = self.expr()
            return Node("cond", kids=[n, then, other])
        return n
    def compare(self):
        n = self.logic_or()
        while self.cur[1] in ("==", "!=", ">", "<", ">=", "<="):
            op = self.eat()[1]; n = Node("bin", op, [n, self.logic_or()])
        return n
    def logic_or(self):
        n = self.logic_and()
        while self.cur[1] == "||":
            self.eat(); n = Node("bin", "or", [n, self.logic_and()])
        return n
    def logic_and(self):
        n = self.add()
        while self.cur[1] == "&&":
            self.eat(); n = Node("bin", "and", [n, self.add()])
        return n
    def add(self):
        n = self.mul()
        while self.cur[1] in ("+", "-"):
            op = self.eat()[1]; n = Node("bin", op, [n, self.mul()])
        return n
    def mul(self):
        n = self.unary()
        while self.cur[1] in ("*", "/", "//", "%"):
            op = self.eat()[1]; n = Node("bin", op, [n, self.unary()])
        return n
    def unary(self):
        if self.cur[1] in ("+", "-", "!"):
            op = self.eat()[1]; return Node("unary", op, [self.unary()])
        return self.power()
    def power(self):
        n = self.primary()
        if self.cur[1] == "**":
            self.eat(); return Node("bin", "**", [n, self.unary()])
        return n
    def primary(self):
        k, v = self.cur
        if k == "NUM":
            self.eat()
            return Node("num", float(v) if "." in v else int(v))
        if k == "IDENT":
            name = self.eat()[1]
            if name in ("true", "false"): return Node("num", name == "true")
            if self.cur[1] == "(":
                self.eat("("); args = []
                if self.cur[1] != ")":
                    args.append(self.expr())
                    while self.cur[1] == ",":
                        self.eat(","); args.append(self.expr())
                self.eat(")"); return Node("call", name, args)
            return Node("var", name)
        if v == "(":
            self.eat("("); n = self.expr(); self.eat(")"); return n
        raise SyntaxError(f"意外 token {v!r}")


# ---------- 3) 编译器：AST -> 栈式指令 ----------
PUSH, LOAD, BIN, UNARY, CALL, JIF, JMP, HALT = (
    "PUSH", "LOAD", "BIN", "UNARY", "CALL", "JIF", "JMP", "HALT")


def compile_node(n, code):
    if n.kind == "num":
        code.append((PUSH, n.value))
    elif n.kind == "var":
        code.append((LOAD, n.value))
    elif n.kind == "unary":
        compile_node(n.kids[0], code); code.append((UNARY, n.value))
    elif n.kind == "bin":
        if n.value == "and":
            # 短路：左假直接把 False 留在栈顶并跳过右操作数
            compile_node(n.kids[0], code)
            jif = len(code); code.append((JIF, None))
            compile_node(n.kids[1], code)
            jmp = len(code); code.append((JMP, None))
            code[jif] = (JIF, len(code))       # 跳到「压入 False」
            code.append((PUSH, False))
            code[jmp] = (JMP, len(code))       # 真结果跳到末尾
        elif n.value == "or":
            compile_node(n.kids[0], code); compile_node(n.kids[1], code)
            code.append((BIN, "or"))
        else:
            compile_node(n.kids[0], code); compile_node(n.kids[1], code)
            code.append((BIN, n.value))
    elif n.kind == "cond":
        compile_node(n.kids[0], code)
        jif = len(code); code.append((JIF, None))
        compile_node(n.kids[1], code)
        jmp = len(code); code.append((JMP, None))
        code[jif] = (JIF, len(code))
        compile_node(n.kids[2], code)
        code[jmp] = (JMP, len(code))
    elif n.kind == "call":
        for a in n.kids: compile_node(a, code)
        code.append((CALL, (n.value, len(n.kids))))


BINFN = {
    "+": operator.add, "-": operator.sub, "*": operator.mul,
    "/": operator.truediv, "//": operator.floordiv, "%": operator.mod,
    "**": operator.pow,
    "==": operator.eq, "!=": operator.ne, ">": operator.gt,
    "<": operator.lt, ">=": operator.ge, "<=": operator.le,
    "or": lambda a, b: a or b,
}
UNARYFN = {"+": operator.pos, "-": operator.neg, "!": operator.not_}
BUILTINS = {
    "max": max, "min": min, "abs": abs, "round": round, "sqrt": math.sqrt,
    "log": math.log, "pow": math.pow, "ceil": math.ceil, "floor": math.floor,
    "clamp": lambda v, lo, hi: max(lo, min(hi, v)),
}


class VMRuntime:
    def __init__(self, code, env, builtins=None):
        self.code, self.env = code, env
        self.builtins = builtins or BUILTINS
        self.stack, self.pc = [], 0
        self.steps = 0

    def run(self, max_steps=10000):
        while self.pc < len(self.code):
            self.steps += 1
            if self.steps > max_steps: raise RuntimeError("超过最大指令数")
            op, arg = self.code[self.pc]; self.pc += 1
            if op == PUSH: self.stack.append(arg)
            elif op == LOAD:
                if arg not in self.env: raise NameError(f"未定义变量 {arg}")
                self.stack.append(self.env[arg])
            elif op == UNARY: self.stack.append(UNARYFN[arg](self.stack.pop()))
            elif op == BIN:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(BINFN[arg](a, b))
            elif op == CALL:
                name, n = arg
                args = [self.stack.pop() for _ in range(n)][::-1]
                fn = self.builtins.get(name)
                if fn is None: raise NameError(f"未知函数 {name}")
                self.stack.append(fn(*args))
            elif op == JIF:
                if not self.stack.pop(): self.pc = arg
            elif op == JMP: self.pc = arg
            elif op == HALT: break
            else: raise ValueError(op)
        return self.stack[-1] if self.stack else None


class Formula:
    """编译一次，重复求值。"""
    _cache = {}

    def __init__(self, src):
        self.src = src
        if src not in Formula._cache:
            ast = Parser(tokenize(src)).parse()
            code = []
            compile_node(ast, code)
            code.append((HALT, None))
            Formula._cache[src] = code
        self.code = Formula._cache[src]

    def eval(self, env=None):
        return VMRuntime(self.code, env or {}).run()

    def __repr__(self):
        return f"Formula({self.src!r}, {len(self.code)} 指令)"


RULES = [
    ("基础算术", "1 + 2 * 3", {}),
    ("幂与括号", "(1 + 2) ** 2 // 4", {}),
    ("变量", "price * qty * (1 - discount)", {"price": 99, "qty": 3, "discount": 0.1}),
    ("比较与逻辑", "score >= 60 && absent <= 3", {"score": 85, "absent": 1}),
    ("三元条件", "amount > 1000 ? amount * 0.9 : amount", {"amount": 1500}),
    ("内置函数", "clamp(score, 0, 100) + round(bonus, 1)",
     {"score": 128, "bonus": 3.14159}),
    ("风控规则", "risk == 'high' || amount > 50000 ? '拒绝' : '通过'",
     {"risk": "low", "amount": 200}),
    ("注释", "price * 1.06  # 含税", {"price": 100}),
]

print("== 公式引擎求值 ==")
for name, src, env in RULES:
    # 字符串字面量：本例 env 提供，公式里用变量引用
    expr = src.replace("'high'", "risk_high").replace("'拒绝'", "reject").replace("'通过'", "pass_")
    e2 = dict(env, risk_high="high", reject="拒绝", pass_="通过")
    f = Formula(expr)
    try:
        val = f.eval(e2)
        print(f"  {name:<10} {f!r:<44} -> {val!r}")
    except (NameError, KeyError, SyntaxError, ValueError) as e:
        print(f"  {name:<10} -> {type(e).__name__}: {e}")

print("\n== 编译缓存与重复求值 ==")
Formula._cache.clear()
f = Formula("x * 2 + 1")
print("  编译后指令:", f.code)
for x in (1, 5, 10):
    print(f"  x={x:<3} -> {f.eval({'x': x})}")
print("  缓存条目数:", len(Formula._cache), "（同一公式只编译一次）")
Formula("x * 2 + 1")
print("  再次构造后仍为:", len(Formula._cache))

print("\n== 常量折叠（编译期优化示意）==")
# 手工演示：1+2*3 的指令里可以折叠成 PUSH 7
f2 = Formula("1 + 2 * 3")
print("  未优化指令:", f2.code)
print("  折叠后理论指令: [('PUSH', 7), ('HALT', None)]")
print("  真实优化器遍历 AST，把纯字面量子树替换成 Num 节点再编译")

print("\n== 安全边界 ==")
for bad in ("__import__('os')", "x.__class__", "open('/x')", "eval('1')"):
    try:
        Formula(bad).eval({})
        print(f"  {bad:<24} 意外通过")
    except (SyntaxError, ValueError, NameError, KeyError) as e:
        print(f"  {bad:<24} -> 拒绝 ({type(e).__name__})")
print("  无属性访问 / 无任意调用 / 内置函数白名单 -> 天然沙箱")

print("\n== 分层回顾 ==")
for line in [
    "  Lexer   : 字符 -> Token，跳过空白与注释（第683课）",
    "  Parser  : 递归下降建 AST，优先级/结合性分层（第684/685课）",
    "  Compiler: AST -> 线性栈式指令，含跳转（第689课）",
    "  VM      : pc + 栈循环执行，env 与 builtins 可注入（第686/689课）",
    "  Formula : 编译缓存 + eval(env) 多次复用，供规则/报表引擎调用",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现真正的常量折叠优化器，折叠后打印指令数变化。
# 2. 增加 && / || 的完整短路编译（当前 or 走的是普通 BIN）。
# 3. 支持字符串字面量与字符串拼接，让风控规则能直接写 '拒绝'。
# 4. 思考：为什么「编译一次 + eval 多次」比每次都重新解析更适合规则引擎？
