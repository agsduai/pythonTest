# ===== 第843课：符号计算与自动微分-表达式树与符号运算 =====
# 知识点：
#   - 符号计算：表达式不是「马上算出一个数」，而是「保存成可操作的数据」
#   - 表达式树（AST）：叶子 = 常数/变量，内部节点 = 运算符/函数
#   - 求值 = 后序遍历（先算子树再算根）；符号变换 = 树的重写
#   - 自由变量收集、变量替换、结构指标 —— 一切符号系统的地基
#   - sympy 的 Add/Mul/Symbol 类与本课的元组节点同构，思想一致
# 依赖：无（标准库）
import math

FUNCS = ("sin", "cos", "exp", "log")
UNARY = ("neg",) + FUNCS


# ---- 构造函数：节点用元组表示（不可变、可共享、可递归处理）----
def num(v):
    return ("num", float(v))


def var(name):
    return ("var", name)


def add(a, b):
    return ("+", a, b)


def sub(a, b):
    return ("-", a, b)


def mul(a, b):
    return ("*", a, b)


def div(a, b):
    return ("/", a, b)


def pow_(a, n):
    """数值指数幂（本课限定 n 为数，符号指数见练习）。"""
    return ("^", a, num(n))


def neg(a):
    return ("neg", a)


def sin_(a):
    return ("sin", a)


def cos_(a):
    return ("cos", a)


def exp_(a):
    return ("exp", a)


def log_(a):
    return ("log", a)


# ---- 字符串化：按优先级加最小括号 ----
_PREC = {"+": 1, "-": 1, "*": 2, "/": 2, "neg": 3, "^": 4}


def to_string(e, prec=0):
    """prec = 上下文要求的最低优先级，低于自身优先级时加括号。"""
    tag = e[0]
    if tag == "num":
        v = e[1]
        s = str(int(v)) if v == int(v) else f"{v:g}"
        return f"({s})" if v < 0 and prec > 4 else s
    if tag == "var":
        return e[1]
    if tag == "neg":
        s = "-" + to_string(e[1], 3)
        return f"({s})" if prec >= 3 else s
    if tag in FUNCS:
        return f"{tag}({to_string(e[1], 0)})"
    p = _PREC[tag]
    if tag == "^":                       # 右结合
        s = f"{to_string(e[1], p + 1)}^{to_string(e[2], p)}"
    else:
        s = f"{to_string(e[1], p)} {tag} {to_string(e[2], p + 1)}"
    return f"({s})" if prec > p else s


def evaluate(e, env):
    """后序遍历求值；env 提供变量值。"""
    tag = e[0]
    if tag == "num":
        return e[1]
    if tag == "var":
        if e[1] not in env:
            raise KeyError(f"变量 {e[1]} 未在环境中提供")
        return float(env[e[1]])
    if tag == "+":
        return evaluate(e[1], env) + evaluate(e[2], env)
    if tag == "-":
        return evaluate(e[1], env) - evaluate(e[2], env)
    if tag == "*":
        return evaluate(e[1], env) * evaluate(e[2], env)
    if tag == "/":
        d = evaluate(e[2], env)
        if d == 0:
            raise ZeroDivisionError("表达式求值时除零")
        return evaluate(e[1], env) / d
    if tag == "^":
        return evaluate(e[1], env) ** evaluate(e[2], env)
    if tag == "neg":
        return -evaluate(e[1], env)
    if tag == "sin":
        return math.sin(evaluate(e[1], env))
    if tag == "cos":
        return math.cos(evaluate(e[1], env))
    if tag == "exp":
        v = evaluate(e[1], env)
        if v > 700:
            raise OverflowError("exp 参数过大")
        return math.exp(v)
    if tag == "log":
        v = evaluate(e[1], env)
        if v <= 0:
            raise ValueError("log 的定义域为正数")
        return math.log(v)
    raise ValueError(f"未知节点类型 {tag}")


def collect_vars(e, acc=None):
    """收集表达式的全部自由变量名。"""
    if acc is None:
        acc = set()
    tag = e[0]
    if tag == "var":
        acc.add(e[1])
    elif tag == "num":
        pass
    elif tag in UNARY:
        collect_vars(e[1], acc)
    else:
        collect_vars(e[1], acc)
        collect_vars(e[2], acc)
    return acc


def substitute(e, name, replacement):
    """把所有名为 name 的变量替换为 replacement 子树。"""
    tag = e[0]
    if tag == "num":
        return e
    if tag == "var":
        return replacement if e[1] == name else e
    if tag in UNARY:
        return (tag, substitute(e[1], name, replacement))
    return (tag, substitute(e[1], name, replacement),
            substitute(e[2], name, replacement))


def node_count(e):
    if e[0] in ("num", "var"):
        return 1
    if e[0] in UNARY:
        return 1 + node_count(e[1])
    return 1 + node_count(e[1]) + node_count(e[2])


def depth(e):
    if e[0] in ("num", "var"):
        return 1
    if e[0] in UNARY:
        return 1 + depth(e[1])
    return 1 + max(depth(e[1]), depth(e[2]))


def tree_lines(e, indent=0):
    pad = "  " * indent
    tag = e[0]
    if tag == "num":
        return [f"{pad}num {e[1]:g}"]
    if tag == "var":
        return [f"{pad}var {e[1]}"]
    if tag in UNARY:
        return [f"{pad}{tag}"] + tree_lines(e[1], indent + 1)
    return ([f"{pad}{tag}"] + tree_lines(e[1], indent + 1)
            + tree_lines(e[2], indent + 1))


print("== 构造表达式树 ==")
x = var("x")
f = add(add(pow_(x, 2), mul(num(3), x)), num(2))       # x^2 + 3x + 2
print(f"  f = {to_string(f)}")
print("  树结构（缩进 = 子节点）:")
for line in tree_lines(f):
    print("   ", line)

print("\n== 求值 = 后序遍历 ==")
for xv in (-1.0, 0.0, 2.0, 5.0):
    got = evaluate(f, {"x": xv})
    want = xv * xv + 3 * xv + 2
    print(f"  f({xv:g}) = {got:g}   Python 直接算 = {want:g}")

print("\n== 多变量表达式与自由变量 ==")
y = var("y")
g = sub(mul(x, y), div(y, x))                          # x*y - y/x
print(f"  g = {to_string(g)}")
print(f"  自由变量 = {sorted(collect_vars(g))}")
print(f"  g(4, 6) = {evaluate(g, {'x': 4.0, 'y': 6.0}):g}   （24 - 1.5 = 22.5）")

print("\n== 错误都要在求值时清楚暴露 ==")
h = add(x, var("z"))
try:
    evaluate(h, {"x": 1.0})
except KeyError as exc:
    print(f"  缺变量     -> KeyError: {exc}")
try:
    evaluate(div(x, num(0)), {"x": 3.0})
except ZeroDivisionError as exc:
    print(f"  除零       -> {exc}")
try:
    evaluate(log_(num(-1)), {})
except ValueError as exc:
    print(f"  log 定义域 -> {exc}")

print("\n== 变量替换：f(x) -> f(x+1) ==")
inner = add(x, num(1))
f_shift = substitute(f, "x", inner)
print(f"  f(x+1) = {to_string(f_shift)}")
for xv in (0.0, 1.0, 2.0):
    got = evaluate(f_shift, {"x": xv})
    want = (xv + 1) ** 2 + 3 * (xv + 1) + 2
    print(f"  f({xv:g}+1) = {got:g}   应 = {want:g}")

print("\n== 结构指标 ==")
big = sin_(add(pow_(x, 2), num(1)))                    # sin(x^2 + 1)
for label, e in (("f", f), ("g", g), ("sin(x^2+1)", big)):
    print(f"  {label:<12} 节点数 = {node_count(e):>2}   深度 = {depth(e)}")

print("\n== 小结 ==")
for line in (
    "  表达式树把「数学」变成「数据」：可求值、可变换、可分析",
    "  求值是后序遍历；替换/微分/化简都是递归的树重写",
    "  元组节点不可变且可共享，天然适合写纯函数式的符号变换",
    "  后续：微分(844) -> AD(845/846/850) -> 解方程(847) -> 化简(848) -> 多项式(849)",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 to_python(e)：把表达式树编译成 Python 表达式字符串（如 "x**2 + 3*x + 2"），
#    用 eval 与 evaluate 对比验证一致。
# 2. 实现 expression_equal(a, b)：递归比较两棵树是否结构相等；验证
#    substitute(f, "x", var("x")) == f（替换回自身应得到相同的树）。
# 3. 实现 count_op(e, op)：统计某运算符在树中出现的次数；算一算 f 与 g 中各有多少。
# 4. 思考：为什么符号系统用「树」而不是「字符串」？两种表示各适合什么操作？
