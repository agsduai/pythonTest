# ===== 第847课：符号计算与自动微分-符号方程求解 =====
# 知识点：
#   - 解方程的三条路线：公式法（线性/二次）、符号变换、数值迭代
#   - 线性提取：把 f 递归重写成 a·x + b（系数收集），一次方程精确解
#   - 牛顿法 x_{n+1} = x_n - f/f'：导数由第844课的符号微分自动生成
#   - 符号导数 vs 数值差分：精确、无噪声、推导一次到处使用
#   - 收敛对比：牛顿二次收敛 vs 二分线性收敛
# 依赖：无（标准库）
import math

FUNCS = ("sin", "cos", "exp", "log")
UNARY = ("neg",) + FUNCS


# ---- 表达式树（同第843/844课）----
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


def collect_vars(e, acc=None):
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


def simplify(e):
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
            pass
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
    for _ in range(max_rounds):
        nxt = simplify(e)
        if nxt == e:
            return e
        e = nxt
    return e


def diff(e, x):
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


def is_free(e, x):
    """表达式是否不含变量 x。"""
    return x not in collect_vars(e)


def linear_coeffs(e, x):
    """把 e 写成 a·x + b，返回 (a, b)；若关于 x 非线性返回 None。
    系数 a、b 本身是表达式（可含其他变量）。"""
    tag = e[0]
    if tag == "num":
        return (num(0), e)
    if tag == "var":
        return (num(1), num(0)) if e[1] == x else (num(0), e)
    if tag == "neg":
        r = linear_coeffs(e[1], x)
        if r is None:
            return None
        return (neg(r[0]), neg(r[1]))
    if tag in ("+", "-"):
        r1 = linear_coeffs(e[1], x)
        r2 = linear_coeffs(e[2], x)
        if r1 is None or r2 is None:
            return None
        if tag == "+":
            return (add(r1[0], r2[0]), add(r1[1], r2[1]))
        return (sub(r1[0], r2[0]), sub(r1[1], r2[1]))
    if tag == "*":
        if is_free(e[1], x):
            r = linear_coeffs(e[2], x)
            if r is None:
                return None
            return (mul(e[1], r[0]), mul(e[1], r[1]))
        if is_free(e[2], x):
            r = linear_coeffs(e[1], x)
            if r is None:
                return None
            return (mul(e[2], r[0]), mul(e[2], r[1]))
        return None                       # x*x 型：非线性
    return None                           # /、^、函数：本课不处理


def solve_linear(e, x):
    """解方程 e = 0（e 关于 x 的一次式）。返回 (status, root_expr)。"""
    coeffs = linear_coeffs(simplify_deep(e), x)
    if coeffs is None:
        return "nonlinear", None
    a, b = simplify_deep(coeffs[0]), simplify_deep(coeffs[1])
    if a == num(0):
        return ("any" if b == num(0) else "none"), None
    root = num(0) if b == num(0) else div(neg(b), a)
    return "ok", simplify_deep(root)


def solve_quadratic(a, b, c):
    """数值系数的 a·x^2 + b·x + c = 0，返回 (实根列表, 判别式)。"""
    disc = b * b - 4 * a * c
    if disc < 0:
        return [], disc
    if disc == 0:
        return [-b / (2 * a)], disc
    r = math.sqrt(disc)
    return [(-b + r) / (2 * a), (-b - r) / (2 * a)], disc


def quad_str(a, b, c):
    """a·x^2 + b·x + c 的可读字符串（处理符号与省略系数 1）。"""
    terms = []
    for coef, sym in ((a, "x^2"), (b, "x"), (c, "")):
        if coef == 0:
            continue
        mag = abs(coef)
        body = ("" if mag == 1 and sym else f"{mag:g}") + sym
        if not terms:
            terms.append(("-" + body) if coef < 0 else body)
        else:
            terms.append(("- " if coef < 0 else "+ ") + body)
    return " ".join(terms) if terms else "0"


def eval_if_possible(e, env=None):
    """能求值就返回数值，否则返回 None。"""
    env = dict(env or {})
    try:
        missing = collect_vars(e) - set(env)
        if missing:
            return None
        return evaluate(e, env)
    except Exception:
        return None


def newton(f_expr, x0, x="x", tol=1e-12, max_iter=50):
    """牛顿迭代：f' 由符号微分自动生成。
    返回 (根, 迭代记录, 导数表达式, 迭代次数)。"""
    fp = simplify_deep(diff(f_expr, x))
    cur, steps, iters = x0, [], 0
    for _ in range(max_iter):
        fval = evaluate(f_expr, {x: cur})
        steps.append((cur, fval))
        if abs(fval) < tol:
            break
        dval = evaluate(fp, {x: cur})
        if dval == 0:
            raise ZeroDivisionError("牛顿法遇到零导数")
        cur -= fval / dval
        iters += 1
    return cur, steps, fp, iters


def bisection(fn, lo, hi, tol=1e-12, max_iter=200):
    flo, fhi = fn(lo), fn(hi)
    if flo * fhi > 0:
        raise ValueError("区间两端同号，无法二分")
    it = 0
    while (hi - lo) / 2 > tol and it < max_iter:
        mid = (lo + hi) / 2
        if fn(lo) * fn(mid) <= 0:
            hi = mid
        else:
            lo = mid
        it += 1
    return (lo + hi) / 2, it


print("== 一次方程：把 f 重写成 a·x + b ==")
x_ = var("x")
STATUS_ZH = {"ok": "唯一解", "none": "无解", "any": "恒等式（x 任意）",
             "nonlinear": "非线性，本课方法不适用"}
cases = [
    ("3x + 6 = 0",     add(mul(num(3), x_), num(6))),
    ("2(x+3) - 8 = 0", sub(mul(num(2), add(x_, num(3))), num(8))),
    ("a*x - 4 = 0",    add(mul(var("a"), x_), num(-4))),
    ("5 = 0",          num(5)),
    ("2x - 2x = 0",    sub(mul(num(2), x_), mul(num(2), x_))),
    ("x^2 = 0",        mul(x_, x_)),
    ("sin(x) = 0",     sin_(x_)),
]
for label, e in cases:
    status, root = solve_linear(e, "x")
    line = f"  {label:<15} -> {STATUS_ZH[status]}"
    if status == "ok":
        val = eval_if_possible(root)
        if val is None:
            line += f"：x = {to_string(root)}（含参数）"
            line += f"；代 a=2 得 x = {eval_if_possible(root, {'a': 2.0}):g}"
        else:
            resid = eval_if_possible(e, {"x": val})
            line += f"：x = {val:g}，代入验证 |左边| = {abs(resid):.1e}"
    print(line)

print("\n== 二次方程：求根公式 ==")
quad_cases = [(1, -5, 6), (1, 1, 1), (1, -1, -1)]
for a, b, c in quad_cases:
    e = add(add(mul(num(a), pow_(x_, 2)), mul(num(b), x_)), num(c))
    roots, disc = solve_quadratic(a, b, c)
    line = f"  {quad_str(a, b, c)} = 0   判别式 = {disc:g}"
    if not roots:
        print(line + "   无实根")
    else:
        print(line)
        for r in roots:
            resid = abs(evaluate(e, {"x": r}))
            print(f"      x = {r:.9f}   代入 |P(x)| = {resid:.1e}")
phi = (1 + 5 ** 0.5) / 2
print(f"  黄金比例：x^2 - x - 1 = 0 的正根 = {phi:.9f}（这就是 φ）")

print("\n== 牛顿法：符号导数驱动的迭代 ==")
f_expr = sub(sub(pow_(x_, 3), mul(num(2), x_)), num(5))       # x^3 - 2x - 5
root, steps, fp, iters = newton(f_expr, 2.0)
print(f"  f  = {to_string(f_expr)}")
print(f"  f' = {to_string(fp)}（符号微分自动得到）")
print("  迭代过程（二次收敛：正确数字位数每步约翻倍）:")
for i, (xc, fv) in enumerate(steps):
    print(f"    第{i}步: x = {xc:.12f}   |f| = {abs(fv):.2e}")
print(f"  根 ≈ {root:.12f}，共 {iters} 次迭代")

bis_root, bis_iters = bisection(lambda v: v ** 3 - 2 * v - 5, 2.0, 3.0)
print(f"\n  对比二分法: {bis_iters} 次迭代 -> {bis_root:.12f}（线性收敛）")
print(f"  牛顿法只需 {iters} 次迭代 -> {root:.12f}（二次收敛，但需要能求导）")

print("\n== 超越方程：cos(x) = x ==")
g_expr = sub(cos_(x_), x_)                                    # cos(x) - x
root2, steps2, gp, iters2 = newton(g_expr, 1.0)
print(f"  g  = {to_string(g_expr)}")
print(f"  g' = {to_string(gp)}")
print(f"  不动点 ≈ {root2:.12f}（Dottie number），{iters2} 次迭代")
print(f"  验证: cos(root) - root = {math.cos(root2) - root2:.1e}")

print("\n== 方法选择 ==")
print(f"  {'方法':<10}{'适用':<26}{'收敛速度'}")
for row in (("线性提取", "一次方程，精确解", "一步"),
            ("求根公式", "二次方程", "常数次运算"),
            ("牛顿法", "可导 + 初值敏感", "二次收敛"),
            ("二分法", "连续 + 区间两端异号", "线性收敛（稳）")):
    print(f"  {row[0]:<10}{row[1]:<26}{row[2]}")

print("\n== 小结 ==")
for line in (
    "  线性提取把「解方程」变成「读系数」，一次方程一步出精确解",
    "  牛顿法的导数来自符号微分：精确、零噪声、推导一次到处使用",
    "  无实根、恒等式、非线性都要显式区分，不能静默给出错误答案",
    "  下一课：表达式化简与规范型（848）",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 solve_2x2：克莱姆法则解二元一次方程组，并用代入验证。
# 2. 牛顿法初值敏感：f = x^3 - 2x + 2 从 x0 = 0 出发在 0 与 1 之间循环；
#    从 x0 = 0.5 出发最终收敛到实根 ≈ -1.7693。请演示这两种行为。
# 3. 把二次求解扩展到「含参数系数」：根用参数表达式表示（如 (-b ± √(b^2-4ac)) / 2a）。
# 4. 思考：牛顿法为什么需要「好的初值」？二分法慢但稳，工程上如何结合两者？
