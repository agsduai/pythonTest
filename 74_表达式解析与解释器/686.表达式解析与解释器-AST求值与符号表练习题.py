# ===== 第686课：表达式解析与解释器-AST求值与符号表 =====
# 知识点：
#   - 求值器遍历 AST：Num 返回字面值、Var 查符号表、BinOp 递归算两边
#   - 符号表 env 是「变量名 -> 值」的链；函数调用时创建子环境（作用域）
#   - 内置函数用白名单 dict 提供，绝不把 eval/exec 暴露给表达式
#   - 短路求值：and/or 只在需要时算右操作数，也避免除零等副作用
#   - 类型检查与运行时错误：除零、未知变量、未知函数要给出清晰异常
#   - 与第661课模板受限求值对比：这里支持完整算术与函数，但仍是白名单
# 依赖：无（标准库）
import math
import operator

# ---- 复用第684课的 AST 与 Parser（此处内联简化版） ----
from dataclasses import dataclass


@dataclass
class Num:
    value: object          # 整数保留 int，供 round/range 等需要 int 的内置函数使用
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
        if two in ("**", "//"):
            out.append(("OP", two)); i += 2; continue
        if c in "+-*/%^(),":
            out.append((c, c)); i += 1; continue
        raise ValueError(f"非法字符 {c!r}")
    out.append(("EOF", ""))
    return out


class Parser:
    def __init__(self, t): self.t, self.i = t, 0
    @property
    def cur(self): return self.t[self.i]
    def eat(self, v=None):
        x = self.cur
        if v is not None and x[1] != v: raise SyntaxError(f"期望 {v!r} 实际 {x[1]!r}")
        self.i += 1; return x
    def parse(self):
        n = self.expr()
        if self.cur[0] != "EOF": raise SyntaxError("多余输入")
        return n
    def expr(self):
        n = self.term()
        while self.cur[1] in ("+", "-"):
            op = self.eat()[1]; n = BinOp(op, n, self.term())
        return n
    def term(self):
        n = self.unary()
        while self.cur[1] in ("*", "/", "//", "%"):
            op = self.eat()[1]; n = BinOp(op, n, self.unary())
        return n
    def unary(self):
        if self.cur[1] in ("+", "-"):
            return UnaryOp(self.eat()[1], self.unary())
        return self.power()
    def power(self):
        n = self.primary()
        if self.cur[1] == "**":
            self.eat(); return BinOp("**", n, self.unary())
        return n
    def primary(self):
        k, v = self.cur
        if k == "NUM":
            self.eat()
            return Num(float(v) if "." in v else int(v))
        if k == "IDENT":
            name = self.eat()[1]
            if self.cur[1] == "(":
                self.eat("("); args = []
                if self.cur[1] != ")":
                    args.append(self.expr())
                    while self.cur[1] == ",":
                        self.eat(","); args.append(self.expr())
                self.eat(")"); return Call(name, args)
            return Var(name)
        if v == "(":
            self.eat("("); n = self.expr(); self.eat(")"); return n
        raise SyntaxError(f"意外 {v!r}")


BINOPS = {
    "+": operator.add, "-": operator.sub, "*": operator.mul,
    "/": operator.truediv, "//": operator.floordiv, "%": operator.mod,
    "**": operator.pow,
}
UNARY = {"+": operator.pos, "-": operator.neg}
BUILTINS = {
    "abs": abs, "min": min, "max": max, "round": round,
    "sqrt": math.sqrt, "log": math.log, "sin": math.sin, "cos": math.cos,
    "pow": math.pow, "len": len, "sum": sum,
}


class EvalError(Exception):
    pass


def evaluate(node, env=None, builtins=None):
    env = env if env is not None else {}
    builtins = builtins if builtins is not None else BUILTINS
    if isinstance(node, Num):
        return node.value
    if isinstance(node, Var):
        if node.name in env:
            return env[node.name]
        if node.name == "pi":
            return math.pi
        raise EvalError(f"未定义变量: {node.name}")
    if isinstance(node, UnaryOp):
        return UNARY[node.op](evaluate(node.operand, env, builtins))
    if isinstance(node, BinOp):
        a = evaluate(node.left, env, builtins)
        b = evaluate(node.right, env, builtins)
        if node.op in ("/", "//", "%") and b == 0:
            raise EvalError("除零错误")
        return BINOPS[node.op](a, b)
    if isinstance(node, Call):
        fn = builtins.get(node.name)
        if fn is None:
            raise EvalError(f"未知函数: {node.name}")
        args = [evaluate(a, env, builtins) for a in node.args]
        try:
            return fn(*args)
        except (TypeError, ValueError) as e:
            raise EvalError(f"{node.name}{tuple(args)} 调用失败: {e}") from e
    raise EvalError(f"未知节点: {type(node).__name__}")


def run(src, env=None):
    return evaluate(Parser(tokenize(src)).parse(), env)


ENV = {"x": 10, "y": 3, "items": [1, 2, 3, 4], "price": 19.9}

print("== 基础求值 ==")
for src in ("1 + 2 * 3", "(1 + 2) * 3", "2 ** 3 ** 2", "-2 ** 2",
            "x + y", "x / y", "10 // 3", "10 % 3", "pi * 2"):
    print(f"  {src:<20} = {run(src, ENV):.6g}")

print("\n== 内置函数（白名单）==")
for src in ("max(1, 5, 2)", "min(x, y)", "sqrt(16)", "round(3.14159, 2)",
            "abs(-7)", "len(items)", "sum(items)", "pow(2, 10)"):
    print(f"  {src:<22} = {run(src, ENV)}")

print("\n== 符号表：同一表达式、不同环境 ==")
for env in ({"x": 1, "y": 2}, {"x": 100, "y": 5}, {"x": -3, "y": 3}):
    print(f"  env={env} -> x*2+y = {run('x * 2 + y', env)}")

print("\n== 运行时错误（清晰异常，不崩溃）==")
for src in ("1 / 0", "unknown + 1", "nope(1)", "sqrt(-1)", "max()"):
    try:
        print(f"  {src:<16} = {run(src, ENV)}")
    except EvalError as e:
        print(f"  {src:<16} -> EvalError: {e}")

print("\n== 安全边界：不暴露任意代码 ==")
for src in ("__import__('os')", "open('/etc/passwd')", "eval('1+1')"):
    try:
        run(src)
        print(f"  {src}: 意外通过！")
    except (EvalError, SyntaxError, ValueError) as e:
        print(f"  {src:<28} -> 拒绝 ({type(e).__name__})")
print("  白名单里没有 __import__/open/eval，表达式语言天然沙箱化")

print("\n== 短路求值（用带副作用的函数计数验证）==")
calls = []
def risky(v):
    calls.append(v)          # 记录是否被求值
    return 1 / v             # v=0 会抛 ZeroDivisionError

custom = dict(BUILTINS, risky=risky)
# 手写 AST 分支：risky(0) 是「不应被求值」的那一支
bad_branch = Call("risky", [Num(0)])
safe_branch = Num(99)
# 模拟三元：flag 为真取 99，为假才去算 risky(0)
def eval_cond(flag, env):
    if flag:
        return evaluate(safe_branch, env, custom)
    return evaluate(bad_branch, env, custom)

for flag in (True, False):
    calls.clear()
    try:
        val = eval_cond(flag, {})
        print(f"  flag={flag}: 结果={val}  risky 调用次数={len(calls)}")
    except ZeroDivisionError:
        print(f"  flag={flag}: 触发除零（说明分支被求值了）")
print("  核心原则：先判断是否需要某分支，再决定是否 evaluate")

print("\n== 求值与解析解耦的收益 ==")
for line in [
    "  同一 AST 可多次用不同 env 求值（公式引擎、规则引擎）",
    "  可加常量折叠、类型检查、序列化、可视化，互不干扰",
    "  解析一次 + 求值 N 次，是表达式引擎的常见优化",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加 and/or/not 与短路求值，验证 `x != 0 and 10/x > 1` 不除零。
# 2. 实现常量折叠优化：遍历 AST 把纯字面量子树先算成 Num。
# 3. 给符号表增加作用域链（子 env 可遮蔽父 env 的变量）。
# 4. 思考：为什么白名单内置函数比「允许调用任意 Python 函数」安全得多？
