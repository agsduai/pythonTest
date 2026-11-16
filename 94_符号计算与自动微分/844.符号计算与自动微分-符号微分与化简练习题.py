# ===== 第844课：符号计算与自动微分-符号微分与化简 =====
# 知识点：
#   - 符号微分：对表达式树递归应用求导法则，得到「导数的表达式」
#   - 乘积法则 / 商法则 / 幂法则 / 链式法则 —— 全部是树的重写规则
#   - 原始求导结果冗长（表达式膨胀），必须配化简：常数折叠 + 单位元消去
#   - 化简到不动点：反复应用直到树不再变化
#   - 验证手段：与解析导数、数值中心差分三方对比
# 依赖：无（标准库）
import math

FUNCS = ("sin", "cos", "exp", "log")
UNARY = ("neg",) + FUNCS


# ---- 表达式树（同第843课）----
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


_PREC = {"+": 1, "-": 1, "*": 2, "/": 2, "neg": 3, "^": 4}


def to_string(e, prec=0):
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
    if tag == "^":
        s = f"{to_string(e[1], p + 1)}^{to_string(e[2], p)}"
    else:
        s = f"{to_string(e[1], p)} {tag} {to_string(e[2], p + 1)}"
    return f"({s})" if prec > p else s


def evaluate(e, env):
    tag = e[0]
    if tag == "num":
        return e[1]
    if tag == "var":
        if e[1] not in env:
            raise KeyError(f"变量 {e[1]} 未提供")
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
            raise ZeroDivisionError("除零")
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
            raise ValueError("log 定义域为正数")
        return math.log(v)
    raise ValueError(f"未知节点 {tag}")


def node_count(e):
    if e[0] in ("num", "var"):
        return 1
    if e[0] in UNARY:
        return 1 + node_count(e[1])
    return 1 + node_count(e[1]) + node_count(e[2])


def simplify(e):
    """单层化简：常数折叠 + 单位元消去（自底向上）。"""
    tag = e[0]
    if tag in ("num", "var"):
        return e
    if tag in FUNCS:
        return (tag, simplify(e[1]))
    if tag == "neg":
        a = simplify(e[1])
        if a[0] == "num":
            return num(-a[1])
        return ("neg", a)
    a, b = simplify(e[1]), simplify(e[2])
    if a[0] == "num" and b[0] == "num":
        try:
            return num(evaluate((tag, a, b), {}))
        except Exception:
            pass                       # 除零等：保留原样
    if tag == "+":
        if a == num(0):
            return b
        if b == num(0):
            return a
    elif tag == "-":
        if b == num(0):
            return a
        if a == num(0):
            return neg(b)
    elif tag == "*":
        if a == num(0) or b == num(0):
            return num(0)
        if a == num(1):
            return b
        if b == num(1):
            return a
    elif tag == "/":
        if a == num(0):
            return num(0)
        if b == num(1):
            return a
    elif tag == "^":
        if b == num(1):
            return a
        if b == num(0):
            return num(1)
    return (tag, a, b)


def simplify_deep(e, max_rounds=20):
    """反复化简直到不动点。"""
    for _ in range(max_rounds):
        nxt = simplify(e)
        if nxt == e:
            return e
        e = nxt
    return e


def diff(e, x):
    """对变量 x 的符号导数（返回新表达式树）。"""
    tag = e[0]
    if tag == "num":
        return num(0)
    if tag == "var":
        return num(1) if e[1] == x else num(0)
    if tag == "+":
        return add(diff(e[1], x), diff(e[2], x))
    if tag == "-":
        return sub(diff(e[1], x), diff(e[2], x))
    if tag == "neg":
        return neg(diff(e[1], x))
    if tag == "*":
        u, v = e[1], e[2]
        return add(mul(diff(u, x), v), mul(u, diff(v, x)))
    if tag == "/":
        u, v = e[1], e[2]
        return div(sub(mul(diff(u, x), v), mul(u, diff(v, x))), pow_(v, 2))
    if tag == "^":
        n = e[2][1]
        return mul(mul(num(n), pow_(e[1], n - 1)), diff(e[1], x))
    if tag == "sin":
        return mul(cos_(e[1]), diff(e[1], x))
    if tag == "cos":
        return neg(mul(sin_(e[1]), diff(e[1], x)))
    if tag == "exp":
        return mul(exp_(e[1]), diff(e[1], x))
    if tag == "log":
        return div(diff(e[1], x), e[1])
    raise ValueError(f"无法对节点 {tag} 求导")


print("== 微分规则（对照手算）==")
for line in (
    "  d(c) = 0            d(x) = 1",
    "  (f+g)' = f' + g'    (f-g)' = f' - g'",
    "  (f·g)' = f'g + fg'                （乘积法则）",
    "  (f/g)' = (f'g - fg') / g^2",
    "  (f^n)' = n·f^(n-1)·f'             （幂 + 链式）",
    "  (sin f)' = cos(f)·f'   (cos f)' = -sin(f)·f'",
    "  (exp f)' = exp(f)·f'   (log f)' = f'/f",
):
    print(" ", line)

x = var("x")
f = add(add(pow_(x, 2), mul(num(3), x)), num(2))

print("\n== 符号微分 + 化简：从原始输出到可读结果 ==")
raw = diff(f, "x")
simp = simplify_deep(raw)
print(f"  f      = {to_string(f)}")
print(f"  f'原始 = {to_string(raw)}   （{node_count(raw)} 个节点）")
print(f"  f'化简 = {to_string(simp)}   （{node_count(simp)} 个节点）")

print("\n== 常用函数的符号导数 ==")
table = [
    ("x^3",      pow_(x, 3)),
    ("sin(x)",   sin_(x)),
    ("cos(x)",   cos_(x)),
    ("exp(x)",   exp_(x)),
    ("log(x)",   log_(x)),
    ("x*sin(x)", mul(x, sin_(x))),
]
for label, e in table:
    d = simplify_deep(diff(e, "x"))
    print(f"  d/dx {label:<10} = {to_string(d)}")

print("\n== 链式法则：内层导数 × 外层导数 ==")
e_chain = sin_(pow_(x, 2))
raw_c = diff(e_chain, "x")
print(f"  d/dx sin(x^2) 原始  = {to_string(raw_c)}")
print(f"  化简后              = {to_string(simplify_deep(raw_c))}")

print("\n== 数值验证：符号导数 vs 解析导数 vs 中心差分 ==")


def numeric_diff(fn, v, h=1e-6):
    return (fn(v + h) - fn(v - h)) / (2 * h)


cases = [
    ("x^2 + 3*x + 2", f,
     lambda t: t * t + 3 * t + 2, lambda t: 2 * t + 3),
    ("x^3 - 2*x", sub(pow_(x, 3), mul(num(2), x)),
     lambda t: t ** 3 - 2 * t, lambda t: 3 * t * t - 2),
    ("sin(x) * x", mul(sin_(x), x),
     lambda t: math.sin(t) * t, lambda t: math.sin(t) + t * math.cos(t)),
    ("exp(0.5 * x)", exp_(mul(num(0.5), x)),
     lambda t: math.exp(0.5 * t), lambda t: 0.5 * math.exp(0.5 * t)),
    ("log(x^2 + 1)", log_(add(pow_(x, 2), num(1))),
     lambda t: math.log(t * t + 1), lambda t: 2 * t / (t * t + 1)),
]
for label, e, fn, fprime in cases:
    d = simplify_deep(diff(e, "x"))
    worst_sym = worst_num = 0.0
    for xv in (0.5, 1.3, 2.7):
        sym = evaluate(d, {"x": xv})
        worst_sym = max(worst_sym, abs(sym - fprime(xv)))
        worst_num = max(worst_num, abs(numeric_diff(fn, xv) - fprime(xv)))
    print(f"  {label:<16} 符号最大误差 {worst_sym:.1e}   中心差分最大误差 {worst_num:.1e}")

print("\n== 二阶导数：微分两次 ==")
for label, e in (("x^3", pow_(x, 3)), ("sin(x)", sin_(x)), ("x^2+3x+2", f)):
    d2 = simplify_deep(diff(simplify_deep(diff(e, "x")), "x"))
    print(f"  d²/dx² {label:<10} = {to_string(d2)}")

print("\n== 小结 ==")
for line in (
    "  符号微分 = 求导法则的递归应用，输出仍是表达式",
    "  原始输出冗长且难读，化简（常数折叠 + 单位元）必不可少",
    "  符号导数精确无噪声；数值差分有 O(h) 截断误差",
    "  845/846 课：不做表达式，让导数直接随计算传播（自动微分）",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 增加 tan 节点：tan(f) = sin(f)/cos(f)，实现其求导规则（1 + tan^2），并对 tan(x) 验证。
# 2. 实现偏导：diff 已按变量名区分，请验证 ∂(x^2*y + sin(x))/∂y = x^2、∂/∂x = 2xy + cos(x)。
# 3. 增强 simplify：加入 x*x -> x^2 与 x/x -> 1 规则，并讨论哪些化简会悄悄改变定义域。
# 4. 思考：符号微分的「表达式膨胀」来自哪里？为什么乘积法则、链式法则叠加时膨胀最快？
