# ===== 第747课：编译原理与代码优化-编译流程与三地址码 =====
# 知识点：
#   - 编译流程：词法 -> 语法 -> 语义 -> IR -> 优化 -> 代码生成
#   - IR（中间表示）解耦前端与后端：同一 IR 可生成不同目标代码
#   - 三地址码 3AC：每条指令最多一个运算符、三个操作数，形如 x = y op z
#   - 常见指令：赋值、二元运算、一元运算、条件跳转 goto、标签 label、函数调用
#   - 临时变量 t1/t2 由编译器生成；控制流用 label + if/goto 展平
#   - 本课把第74章的 AST 降级成三地址码，并解释执行验证等价性
# 依赖：无（标准库）
from dataclasses import dataclass, field

# 极简 AST（复用第74章风格）
@dataclass
class Node:
    kind: str
    value: object = None
    kids: list = field(default_factory=list)


def parse_expr(src):
    """只处理 + - * / 与整数/变量/括号的递归下降。"""
    toks, i = [], 0
    while i < len(src):
        c = src[i]
        if c.isspace(): i += 1; continue
        if c.isdigit():
            j = i
            while j < len(src) and src[j].isdigit(): j += 1
            toks.append(("N", int(src[i:j]))); i = j; continue
        if c.isalpha() or c == "_":
            j = i
            while j < len(src) and (src[j].isalnum() or src[j] == "_"): j += 1
            toks.append(("V", src[i:j])); i = j; continue
        toks.append((c, c)); i += 1
    toks.append(("EOF", ""))
    pos = [0]
    def cur(): return toks[pos[0]]
    def eat(v=None):
        x = cur()
        if v is not None and x[1] != v: raise SyntaxError(f"期望 {v!r}")
        pos[0] += 1; return x
    def primary():
        k, v = cur()
        if k == "N": eat(); return Node("num", v)
        if k == "V": eat(); return Node("var", v)
        if v == "(":
            eat("("); n = expr(); eat(")"); return n
        raise SyntaxError(v)
    def term():
        n = primary()
        while cur()[1] in ("*", "/"):
            op = eat()[1]; n = Node("bin", op, [n, primary()])
        return n
    def expr():
        n = term()
        while cur()[1] in ("+", "-"):
            op = eat()[1]; n = Node("bin", op, [n, term()])
        return n
    out = expr()
    if cur()[0] != "EOF": raise SyntaxError("多余输入")
    return out


@dataclass
class Instr:
    op: str
    a: object = None
    b: object = None
    result: object = None

    def __str__(self):
        if self.op == "label": return f"L{self.result}:"
        if self.op == "goto": return f"  goto L{self.result}"
        if self.op == "if_false": return f"  if_false {self.a} goto L{self.result}"
        if self.op == "copy": return f"  {self.result} = {self.a}"
        if self.op == "unary": return f"  {self.result} = {self.a} {self.b}"
        return f"  {self.result} = {self.a} {self.op} {self.b}"


class IRGen:
    def __init__(self):
        self.code = []
        self.temp = 0
        self.label = 0

    def new_temp(self):
        self.temp += 1
        return f"t{self.temp}"

    def new_label(self):
        self.label += 1
        return self.label

    def emit(self, op, a=None, b=None, result=None):
        self.code.append(Instr(op, a, b, result))

    def gen_expr(self, node):
        if node.kind == "num":
            t = self.new_temp()
            self.emit("copy", result=t, a=node.value)
            return t
        if node.kind == "var":
            return node.value          # 变量直接当地址用
        if node.kind == "bin":
            l = self.gen_expr(node.kids[0])
            r = self.gen_expr(node.kids[1])
            t = self.new_temp()
            self.emit(node.value, a=l, b=r, result=t)
            return t
        if node.kind == "unary":
            v = self.gen_expr(node.kids[0])
            t = self.new_temp()
            self.emit("unary", a=node.value, b=v, result=t)
            return t
        raise ValueError(node.kind)

    def gen_if(self, cond_ast, then_ast, else_ast=None):
        """把 if 展平成 label + if_false + goto。"""
        c = self.gen_expr(cond_ast)
        l_else, l_end = self.new_label(), self.new_label()
        self.emit("if_false", a=c, result=l_else)
        self.gen_expr(then_ast)
        self.emit("goto", result=l_end)
        self.emit("label", result=l_else)
        if else_ast:
            self.gen_expr(else_ast)
        self.emit("label", result=l_end)


def run_ir(code, env):
    """解释执行三地址码，验证降级没改变语义。"""
    labels = {ins.result: i for i, ins in enumerate(code) if ins.op == "label"}
    pc, steps = 0, 0
    while pc < len(code):
        steps += 1
        if steps > 1000: raise RuntimeError("死循环")
        ins = code[pc]; pc += 1
        if ins.op in ("label", "goto"):
            if ins.op == "goto": pc = labels[ins.result]
            continue
        if ins.op == "if_false":
            if not env.get(ins.a, 0): pc = labels[ins.result]
            continue
        if ins.op == "copy":
            env[ins.result] = ins.a
        elif ins.op == "unary":
            v = env.get(ins.b, ins.b)
            env[ins.result] = -v if ins.a == "-" else v
        else:
            x = env.get(ins.a, ins.a); y = env.get(ins.b, ins.b)
            env[ins.result] = {"+": lambda: x+y, "-": lambda: x-y,
                               "*": lambda: x*y, "/": lambda: x/y}[ins.op]()
    return env


print("== AST -> 三地址码 ==")
for src in ("1 + 2 * 3", "(a + b) * (c - d)", "x / 2 + y * 3"):
    g = IRGen()
    result = g.gen_expr(parse_expr(src))
    g.emit("copy", a=result, result="out")     # 把最终结果赋给 out
    print(f"\n  源表达式: {src}")
    for ins in g.code:
        print("   ", ins)
    env = {"a": 2, "b": 3, "c": 10, "d": 4, "x": 8, "y": 5}
    out = run_ir(g.code, dict(env))
    print(f"    解释执行 out={out['out']}   Python 直接算={eval(src, {}, env)}")

print("\n== 控制流展平：if / goto / label ==")
g2 = IRGen()
g2.gen_if(parse_expr("flag"), parse_expr("x + 1"), parse_expr("x - 1"))
for ins in g2.code:
    print("   ", ins)
for flag, x in ((1, 10), (0, 10)):
    env = {"flag": flag, "x": x}
    out = run_ir(g2.code, env)
    temps = {k: v for k, v in out.items() if k.startswith("t")}
    print(f"  flag={flag}, x={x} -> 临时变量结果={temps} "
          f"（应取 {'x+1' if flag else 'x-1'} = {x+1 if flag else x-1}）")

print("\n== 三地址码的特点 ==")
for line in (
    "  每条指令最多一次运算，便于做优化（公共子表达式、常量折叠）",
    "  临时变量显式化，数据流分析有明确的 def/use",
    "  控制流用 label+goto 展平，天然形成基本块（第749课）",
    "  与 AST 相比更接近机器指令，但仍与目标架构无关",
):
    print(" ", line)

print("\n== 编译流程分层 ==")
for stage, duty in (("前端", "词法/语法/语义，产出 AST 与符号表"),
                    ("中端", "AST -> IR，做与机器无关的优化"),
                    ("后端", "IR -> 目标代码，指令选择/寄存器分配/调度"),
                    ("运行时", "内存管理、GC、异常处理、动态链接")):
    print(f"  {stage:<8}: {duty}")

print("\n== 常见 IR 形态 ==")
for line in [
    "  三地址码 / 四元式：教学与简单编译器",
    "  SSA（静态单赋值）：LLVM IR、现代优化器基石（第748课）",
    "  字节码：CPython / JVM / CLR 的栈式或寄存器式 IR（第689课）",
    "  控制流图 CFG：把线性 IR 组织成基本块图（第749课）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给 IRGen 增加 while 循环的 label/goto 展平。
# 2. 把三地址码再降级成第689课的栈式字节码。
# 3. 实现「输出 IR 到文件 + 从文件读回执行」的序列化。
# 4. 思考：为什么编译器不直接从 AST 生成机器码，而要过一层 IR？
