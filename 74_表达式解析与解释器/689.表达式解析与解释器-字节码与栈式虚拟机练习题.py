# ===== 第689课：表达式解析与解释器-字节码与栈式虚拟机 =====
# 知识点：
#   - AST 解释器遍历树；虚拟机先把 AST「编译」成线性指令，再循环执行
#   - 栈式 VM：PUSH / ADD / MUL / LOAD / STORE / JMP_IF_FALSE / CALL
#   - 指令 = (opcode, 参数)；用 list 表示程序，pc 程序计数器逐条前进
#   - 编译期做常量折叠、变量名解析；运行期只做栈操作，更接近真实 CPython
#   - dis 模块可查看 Python 真实字节码，与本课指令集对照
#   - 跳转指令让 VM 能表达 if/while，是「解释器 -> 编译器」的关键一步
# 依赖：无（标准库）
import dis
import operator
from dataclasses import dataclass

PUSH, LOAD, STORE, ADD, SUB, MUL, DIV, POW, NEG, CALL, JMP, JIF, HALT = (
    "PUSH", "LOAD", "STORE", "ADD", "SUB", "MUL", "DIV", "POW", "NEG",
    "CALL", "JMP", "JIF", "HALT")


@dataclass
class Instr:
    op: str
    arg: object = None

    def __repr__(self):
        return f"{self.op}" + (f" {self.arg!r}" if self.arg is not None else "")


OPS = {"+": ADD, "-": SUB, "*": MUL, "/": DIV, "**": POW}
BUILTINS = {"max": max, "min": min, "abs": abs, "round": round}


def compile_expr(node, code):
    """把第684课风格的 AST 编译成栈式指令（这里用嵌套 tuple 表示）。"""
    kind = node[0]
    if kind == "num":
        code.append(Instr(PUSH, node[1]))
    elif kind == "var":
        code.append(Instr(LOAD, node[1]))
    elif kind == "neg":
        compile_expr(node[1], code)
        code.append(Instr(NEG))
    elif kind == "bin":
        compile_expr(node[2], code)
        compile_expr(node[3], code)
        code.append(Instr(OPS[node[1]]))
    elif kind == "call":
        for a in node[2]:
            compile_expr(a, code)
        code.append(Instr(PUSH, len(node[2])))
        code.append(Instr(CALL, node[1]))
    else:
        raise ValueError(kind)


class VM:
    def __init__(self, code, env=None, builtins=None):
        self.code, self.env = code, env or {}
        self.builtins = builtins or BUILTINS
        self.stack = []
        self.pc = 0
        self.trace = []

    def run(self, max_steps=1000):
        steps = 0
        while self.pc < len(self.code):
            steps += 1
            if steps > max_steps:
                raise RuntimeError("超过最大指令数")
            ins = self.code[self.pc]
            op, arg = ins.op, ins.arg
            before = list(self.stack)
            self.pc += 1
            if op == PUSH:
                self.stack.append(arg)
            elif op == LOAD:
                if arg not in self.env:
                    raise NameError(f"未定义变量 {arg}")
                self.stack.append(self.env[arg])
            elif op == STORE:
                self.env[arg] = self.stack.pop()
            elif op in (ADD, SUB, MUL, DIV, POW):
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append({ADD: operator.add, SUB: operator.sub,
                                   MUL: operator.mul, DIV: operator.truediv,
                                   POW: operator.pow}[op](a, b))
            elif op == NEG:
                self.stack.append(-self.stack.pop())
            elif op == CALL:
                n = self.stack.pop()
                args = [self.stack.pop() for _ in range(n)][::-1]
                fn = self.builtins.get(arg)
                if fn is None:
                    raise NameError(f"未知函数 {arg}")
                self.stack.append(fn(*args))
            elif op == JMP:
                self.pc = arg
            elif op == JIF:                # 栈顶为假则跳转
                cond = self.stack.pop()
                if not cond:
                    self.pc = arg
            elif op == HALT:
                break
            else:
                raise ValueError(f"未知指令 {op}")
            self.trace.append((ins, before, list(self.stack)))
        return self.stack[-1] if self.stack else None


# AST 用 (kind, ...) 元组：(1 + 2) * 3
ast = ("bin", "*", ("bin", "+", ("num", 1), ("num", 2)), ("num", 3))
code = []
compile_expr(ast, code)
code.append(Instr(HALT))

print("== 编译结果：(1 + 2) * 3 ==")
for i, ins in enumerate(code):
    print(f"  {i:>2}: {ins}")

print("\n== 执行轨迹 ==")
vm = VM(code)
result = vm.run()
for ins, before, after in vm.trace:
    print(f"  {str(ins):<12} {str(before):<12} -> {after}")
print("  结果:", result)

print("\n== 变量与内置函数 ==")
ast2 = ("bin", "+", ("var", "x"), ("call", "max", [("num", 3), ("var", "y")]))
code2 = []
compile_expr(ast2, code2)
code2.append(Instr(HALT))
print("  指令:", code2)
print("  env={'x':10,'y':7} ->", VM(code2, {"x": 10, "y": 7}).run())

print("\n== 跳转指令：按 x 的真假选分支 ==")
# LOAD x; JIF else; 真分支; JMP end; 假分支; end
prog = [
    Instr(LOAD, "x"),          # 0 栈=[x]
    Instr(JIF, 4),             # 1 若 x 为假跳到 4
    Instr(PUSH, "yes"),        # 2 真分支
    Instr(JMP, 5),             # 3 跳到结束
    Instr(PUSH, "no"),         # 4 假分支
    Instr(HALT),               # 5
]
for x in (1, 0, -5, "abc"):
    print(f"  x={x!r:<8} -> {VM(prog, {'x': x}).run()!r}")

print("\n== STORE：把结果写回变量 ==")
assign = [Instr(PUSH, 2), Instr(PUSH, 3), Instr(ADD), Instr(STORE, "z"),
          Instr(LOAD, "z"), Instr(PUSH, 10), Instr(MUL), Instr(HALT)]
vm3 = VM(assign)
print("  程序:", assign)
print("  结果:", vm3.run(), " env[z]=", vm3.env.get("z"))

print("\n== 对照 CPython 真实字节码 ==")
import io
def real_fn(a, b):
    return (a + b) * 2
buf = io.StringIO()
dis.dis(real_fn, file=buf)
print("  dis.dis(real_fn) 片段:")
for line in buf.getvalue().splitlines()[:12]:
    print("   ", line)
print("  真实字节码同样基于栈，但指令更丰富、有局部变量表与跳转标签")

print("\n== AST 解释器 vs 栈式 VM ==")
for line in (
    "  AST 解释器: 递归遍历树，直观但每个节点都要分派，难优化",
    "  栈式 VM  : 线性指令 + pc 循环，便于做常量折叠、窥孔优化、JIT",
    "  编译一次可重复执行；指令集稳定后还能序列化到文件",
    "  CPython 3.11+ 用「自适应特化字节码」进一步加速热点指令",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 增加比较指令（GT/LT/EQ），让 VM 能编译 if 条件表达式。
# 2. 实现常量折叠：编译期把 ("bin","+",("num",1),("num",2)) 直接变成 PUSH 3。
# 3. 给 VM 增加 CALL 的用户自定义函数（跳转 + 新帧 + RET 指令）。
# 4. 思考：为什么把 AST 编译成线性指令后更容易做优化？
