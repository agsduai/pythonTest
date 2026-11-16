# ===== 第754课：编译原理与代码优化-综合案例-迷你编译器与优化管线 =====
# 知识点：
#   - 综合串起本章：词法 -> 语法 AST -> 三地址码 IR -> 优化 pass -> 栈式字节码 -> VM
#   - 优化管线：常量折叠/传播、公共子表达式、死代码消除、代数简化
#   - 每个 pass 是纯函数 IR -> IR，pass 之间可自由组合、反复跑到不动点
#   - 验证：优化前后在同一 env 下解释执行，结果必须一致（等价性检查）
#   - 统计：指令数、乘法次数、临时变量数的变化，量化优化收益
#   - 全部标准库 + 纯内存，离线可运行；目标语言是第74章的表达式子集
# 依赖：无（标准库）
from collections import Counter
from dataclasses import dataclass, field


# ---------- 1) 前端：词法 + 递归下降 ----------
def tokenize(src):
    out, i = [], 0
    while i < len(src):
        c = src[i]
        if c.isspace(): i += 1; continue
        if c.isdigit():
            j = i
            while j < len(src) and src[j].isdigit(): j += 1
            out.append(("N", int(src[i:j]))); i = j; continue
        if c.isalpha() or c == "_":
            j = i
            while j < len(src) and (src[j].isalnum() or src[j] == "_"): j += 1
            out.append(("V", src[i:j])); i = j; continue
        if src[i:i+2] in ("**", "//"):
            out.append(("O", src[i:i+2])); i += 2; continue
        if c in "+-*/%()": out.append((c, c)); i += 1; continue
        raise ValueError(f"非法字符 {c!r}")
    out.append(("EOF", "")); return out


@dataclass
class Node:
    kind: str
    value: object = None
    kids: list = field(default_factory=list)


def parse(src):
    t, pos = tokenize(src), [0]
    def cur(): return t[pos[0]]
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
        if v == "-":
            eat(); return Node("neg", kids=[primary()])
        raise SyntaxError(v)
    def power():
        n = primary()
        if cur()[1] in ("**", "//"):
            op = eat()[1]; return Node("bin", op, [n, primary()])
        return n
    def term():
        n = power()
        while cur()[1] in ("*", "/", "%"):
            op = eat()[1]; n = Node("bin", op, [n, power()])
        return n
    def expr():
        n = term()
        while cur()[1] in ("+", "-"):
            op = eat()[1]; n = Node("bin", op, [n, term()])
        return n
    out = expr()
    if cur()[0] != "EOF": raise SyntaxError("多余输入")
    return out


# ---------- 2) 中端：AST -> 三地址码 IR ----------
class IRGen:
    def __init__(self): self.code = []; self.n = 0
    def tmp(self): self.n += 1; return f"t{self.n}"
    def emit(self, dst, op, x=None, y=None): self.code.append((dst, op, x, y))
    def gen(self, node):
        if node.kind == "num":
            t = self.tmp(); self.emit(t, "const", node.value); return t
        if node.kind == "var": return node.value
        if node.kind == "neg":
            v = self.gen(node.kids[0]); t = self.tmp()
            self.emit(t, "*", v, -1); return t
        l = self.gen(node.kids[0]); r = self.gen(node.kids[1]); t = self.tmp()
        self.emit(t, node.value, l, r); return t


# ---------- 3) 优化 pass（IR -> IR 的纯函数） ----------
OPS = {"+": lambda a,b:a+b, "-": lambda a,b:a-b, "*": lambda a,b:a*b,
       "/": lambda a,b:a//b if b else 0, "%": lambda a,b:a%b if b else 0,
       "**": lambda a,b:a**b, "//": lambda a,b:a//b if b else 0}


def pass_fold(ir):
    """常量折叠 + 传播 + 代数简化，迭代到不动点。"""
    ir = [list(i) for i in ir]
    for _ in range(30):
        env, changed = {}, False
        for ins in ir:
            dst, op, x, y = ins
            xv = env.get(x, x) if isinstance(x, str) else x
            yv = env.get(y, y) if isinstance(y, str) else y
            if op == "const":
                env[dst] = xv
            elif op in OPS and isinstance(xv,(int,float)) and isinstance(yv,(int,float)):
                try: v = OPS[op](xv, yv)
                except (OverflowError, ZeroDivisionError): v = None
                if v is not None:
                    env[dst] = v
                    if ins[1] != "const" or ins[2] != v:
                        ins[:] = [dst, "const", v, None]; changed = True
            elif op in ("+","*") and yv == 0 and op == "+":
                ins[:] = [dst, "copy", xv, None]; env.pop(dst, None); changed = True
            elif op == "*" and yv == 1:
                ins[:] = [dst, "copy", xv, None]; env.pop(dst, None); changed = True
            elif op == "*" and yv == 0:
                ins[:] = [dst, "const", 0, None]; env[dst] = 0; changed = True
            else:
                env.pop(dst, None)
                if x != xv: ins[2] = xv; changed = True
                if y != yv and y is not None: ins[3] = yv; changed = True
        if not changed: break
    return [tuple(i) for i in ir]


def pass_cse(ir):
    """公共子表达式消除：值编号，重复计算改成 copy。"""
    seen, out = {}, []
    for dst, op, x, y in ir:
        if op in OPS:
            key = (op, x, y)
            if key in seen:
                out.append((dst, "copy", seen[key], None)); continue
            seen[key] = dst
        out.append((dst, op, x, y))
    return out


def pass_dce(ir, roots=("out",)):
    needed, work = set(), list(roots)
    while work:
        v = work.pop()
        if v in needed: continue
        needed.add(v)
        for dst, op, x, y in ir:
            if dst == v:
                for t in (x, y):
                    if isinstance(t, str) and t not in needed: work.append(t)
    return [i for i in ir if i[0] in needed]


def run(ir, env0, out_var="out"):
    env = dict(env0)
    for dst, op, x, y in ir:
        xv = env.get(x, x) if isinstance(x, str) else x
        yv = env.get(y, y) if isinstance(y, str) else y
        if op in ("const", "copy"): env[dst] = xv
        else: env[dst] = OPS[op](xv, yv)
    return env.get(out_var)


def compile_expr(src, optimize=True):
    g = IRGen()
    result = g.gen(parse(src))
    g.emit("out", "copy", result)
    ir = g.code
    if optimize:
        ir = pass_fold(ir)
        ir = pass_cse(ir)
        ir = pass_dce(ir)
        ir = pass_fold(ir)          # 再跑一轮：DCE 可能解锁新折叠
    return ir


def stats(ir):
    c = Counter(op for _, op, _, _ in ir)
    return {"指令": len(ir), "算术": sum(c[k] for k in OPS),
            "乘法": c["*"], "临时变量": len({d for d, *_ in ir})}


print("== 编译管线：AST -> IR -> 优化 -> 执行 ==")
EXPRESSIONS = [
    "2 * 3 + 4",
    "x * 1 + 0",
    "a + b + (a + b)",
    "2 * 3 * x + 10 * 2",
    "n * 0 + 42",
    "(1 + 2) * (3 + 4) - y",
]
ENV = {"x": 7, "a": 3, "b": 5, "y": 2, "n": 99}

for src in EXPRESSIONS:
    ir0 = compile_expr(src, optimize=False)
    ir1 = compile_expr(src, optimize=True)
    v0, v1 = run(ir0, ENV), run(ir1, ENV)
    print(f"\n  源码: {src}")
    print(f"    未优化 {stats(ir0)}  -> 结果 {v0}")
    print(f"    优化后 {stats(ir1)}  -> 结果 {v1}  等价={v0 == v1}")

print("\n== 单个例子的 IR 逐步展开 ==")
src = "2 * 3 * x + 10 * 2"
g = IRGen(); r = g.gen(parse(src)); g.emit("out", "copy", r)
stages = [("生成 IR", g.code),
          ("常量折叠", pass_fold(g.code)),
          ("公共子表达式", pass_cse(pass_fold(g.code))),
          ("死代码消除", pass_dce(pass_cse(pass_fold(g.code))))]
for name, ir in stages:
    print(f"  [{name}] {stats(ir)}")
    for ins in ir:
        print("     ", ins)

print("\n== 优化收益汇总 ==")
tot0 = tot1 = 0
for src in EXPRESSIONS:
    a, b = stats(compile_expr(src, False)), stats(compile_expr(src, True))
    tot0 += a["指令"]; tot1 += b["指令"]
print(f"  6 个表达式总指令数: {tot0} -> {tot1}，减少 {1-tot1/tot0:.0%}")

print("\n== Pass 顺序的影响 ==")
for line in (
    "  先折叠才能暴露 CSE 机会；先 DCE 再折叠可清掉传播后的垃圾",
    "  Pass 之间要迭代到不动点（本例显式跑了两轮 fold）",
    "  LLVM 的 pass manager 用分析保留/失效机制避免重复计算",
    "  每个 pass 独立可测：输入 IR -> 输出 IR + 等价性断言",
):
    print(" ", line)

print("\n== 分层回顾 ==")
for line in [
    "  前端  : 词法 tokenize + 递归下降 AST（第683/684课）",
    "  中端  : AST -> 三地址码 IR（第747课）",
    "  优化  : fold / CSE / DCE / 代数简化（第751/752课）",
    "  分析  : 活跃变量驱动 DCE（第750课）、干扰图可接寄存器分配（第753课）",
    "  后端  : 可继续降级到栈式字节码 VM（第689课）",
    "  验证  : 优化前后解释执行结果一致 + 指令数统计",
]:
    print("  -", line)

print("\n== 与真实编译器的差距 ==")
for line in [
    "  无 CFG/基本块/SSA/循环优化（第748/749/752课）",
    "  无真实后端：无指令选择、寄存器分配、目标文件生成",
    "  只支持表达式，无函数/控制流/类型系统/错误处理",
    "  目标是把本章各阶段串成一条可验证的完整链路",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加 pass_strength_reduce，把 x*2 改成 x+x 或移位。
# 2. 把优化后的 IR 降级成第689课的栈式字节码并执行。
# 3. 增加 if 表达式，用 SSA + φ 做条件常量传播（第748/751课）。
# 4. 思考：为什么优化 pass 要反复跑到不动点，而不是固定跑一遍？
