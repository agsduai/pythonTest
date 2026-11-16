# ===== 第751课：编译原理与代码优化-常量传播与死代码消除 =====
# 知识点：
#   - 常量折叠 const folding：编译期把 2*3 直接算成 6（第694课）
#   - 常量传播 const propagation：把已知常量沿 def-use 替换到使用点
#   - 稀疏条件常量传播 SCCP：在 SSA/CFG 上同时做传播与可达性判定，能删不可达分支
#   - 死代码消除 DCE：删「定义了但从未被使用」的指令（第750课活跃分析）
#   - 复制传播 copy propagation：x=y 后把 y 替成 x 的值
#   - 优化要迭代到不动点：一次传播可能解锁新的折叠机会
# 依赖：无（标准库）
from collections import defaultdict

OPS = {
    "+": lambda a,b: a+b, "-": lambda a,b: a-b, "*": lambda a,b: a*b,
    "/": lambda a,b: a//b if b else None, "%": lambda a,b: a%b if b else None,
}

# 三地址码：(dst, op, x, y)；op 为 "const"/"copy"/算术/if
Program = list

SOURCE: Program = [
    ("a", "const", 10, None),
    ("b", "const", 20, None),
    ("c", "*", "a", "b"),          # 10*20 -> 200
    ("d", "+", "c", 5),           # 200+5 -> 205
    ("e", "const", 3, None),
    ("f", "*", "d", "e"),         # 205*3 -> 615
    ("dead", "+", "a", "b"),      # 从未被使用
    ("g", "copy", "f", None),
    ("h", "-", "g", 15),
    ("out", "copy", "h", None),
    ("unused2", "const", 999, None),
]
LIVE_ROOTS = {"out"}


def fold_consts(prog):
    """常量折叠 + 复制传播 + 常量传播，迭代到不动点。"""
    prog = [list(i) for i in prog]
    for _ in range(20):
        env, changed = {}, False
        for ins in prog:
            dst, op, x, y = ins
            xv = env.get(x, x) if isinstance(x, str) else x
            yv = env.get(y, y) if isinstance(y, str) else y
            if op == "const":
                env[dst] = xv
            elif op == "copy":
                if isinstance(xv, (int, float)):
                    env[dst] = xv
                    if ins[2] != xv:
                        ins[2] = xv; changed = True
            elif op in OPS and isinstance(xv, (int,float)) and isinstance(yv, (int,float)):
                v = OPS[op](xv, yv)
                if v is not None:
                    env[dst] = v
                    if ins[1] != "const" or ins[2] != v:
                        ins[:] = [dst, "const", v, None]
                        changed = True
            else:
                env.pop(dst, None)
                if x != xv: ins[2] = xv; changed = True
                if y != yv and y is not None: ins[3] = yv; changed = True
        if not changed:
            break
    return [tuple(i) for i in prog]


def dce(prog, roots):
    """从根变量反向标记 use，删掉未被使用的定义。"""
    needed, work = set(), list(roots)
    while work:
        v = work.pop()
        if v in needed: continue
        needed.add(v)
        for ins in prog:
            dst, op, x, y = ins
            if dst == v:
                for t in (x, y):
                    if isinstance(t, str) and t not in needed:
                        work.append(t)
    return [ins for ins in prog if ins[0] in needed]


def render(prog):
    for dst, op, x, y in prog:
        if op == "const": print(f"    {dst} = {x}")
        elif op == "copy": print(f"    {dst} = {x}")
        else: print(f"    {dst} = {x} {op} {y}")


def eval_prog(prog):
    env = {}
    for dst, op, x, y in prog:
        xv = env.get(x, x) if isinstance(x, str) else x
        yv = env.get(y, y) if isinstance(y, str) else y
        if op in ("const", "copy"): env[dst] = xv
        else: env[dst] = OPS[op](xv, yv)
    return env.get("out")


print("== 原始 IR ==")
render(SOURCE)
print(f"  解释执行 out = {eval_prog(SOURCE)}")

print("\n== 常量折叠 + 传播（迭代不动点）==")
folded = fold_consts(SOURCE)
render(folded)
print(f"  执行结果 out = {eval_prog(folded)}（应与原程序一致）")

print("\n== 死代码消除（保留 out 及其依赖链）==")
dead = dce(folded, LIVE_ROOTS)
render(dead)
print(f"  指令数 {len(SOURCE)} -> {len(dead)}，删掉 "
      f"{sorted(set(i[0] for i in folded) - set(i[0] for i in dead))}")

print("\n== 条件常量传播：删不可达分支 ==")
COND: Program = [
    ("flag", "const", 0, None),
    ("t", "const", 1, None),
    ("f", "const", 2, None),
    ("r", "select", "flag", ("t", "f")),   # select cond, (真值, 假值)
    ("out", "copy", "r", None),
]
def sccp_select(prog):
    env, prog2 = {}, []
    for ins in prog:
        dst, op, x, y = list(ins) + [None] * (4 - len(ins))
        if op == "const":
            env[dst] = x
        elif op == "select" and x in env:
            chosen = y[0] if env[x] else y[1]
            v = env.get(chosen, chosen)
            env[dst] = v
            prog2.append((dst, "const", v, None))
            continue
        elif op == "copy":
            v = env.get(x, x)
            env[dst] = v
            prog2.append((dst, "const", v, None) if isinstance(v, (int,float)) else ins)
            continue
        prog2.append(ins)
    return prog2

print("  条件版原始:")
for i in COND: print("   ", i)
opt = sccp_select(COND)
print("  优化后:")
for i in opt: print("   ", i)
print("  flag=0 使 f 分支不可达，整条选择被折叠成常量")

print("\n== 优化组合的顺序很重要 ==")
for line in (
    "  常量传播 -> 产生新的常量表达式 -> 再折叠 -> 再传播（需迭代）",
    "  折叠后某些分支条件变成常量 -> CFG 简化 -> 更多死代码",
    "  DCE 通常放在最后：前面优化制造的垃圾由它统一清理",
    "  编译器 pass manager 会反复跑这组 pass 直到不再变化",
):
    print(" ", line)

print("\n== 与第750课数据流的关系 ==")
for line in [
    "  常量传播是「正向 may/must」分析的特例（格：未定义/常量/非常量）",
    "  DCE 依赖活跃变量分析的 LiveOut 结果",
    "  SSA 让 def-use 显式，SCCP 可以只在相关边上传递，更快",
    "  三类格值：⊤(未知) / 常量 c / ⊥(非常量)，交汇规则要单调",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 SCCP 的三值格（未定义/常量/非常量）并遍历 CFG 求不动点。
# 2. 增加公共子表达式消除（值编号），删除 `a+b` 的重复计算。
# 3. 实现复制传播后把 `x = y` 本身也删掉。
# 4. 思考：为什么常量传播必须迭代到不动点，跑一次不够？
