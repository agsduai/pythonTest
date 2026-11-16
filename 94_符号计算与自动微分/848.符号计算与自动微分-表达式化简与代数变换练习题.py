# ===== 第848课：符号计算与自动微分-表达式化简与代数变换 =====
# 知识点：
#   - 同一表达式有无穷多种写法 -> 化简与「规范型 canonical form」
#   - 常数折叠 + 单位元消去 + 规范排序 + 展开 + 合并同类项
#   - 展开：乘法分配到加法、整数次幂按二项式展开（笛卡尔积实现）
#   - 合并同类项：展开后按次数归并，得到唯一的多项式规范型
#   - 变换正确性用「随机取点采样」快速验证（不是数学证明）
# 依赖：无（标准库）
import math
import random

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


def node_count(e):
    if e[0] in ("num", "var"):
        return 1
    if e[0] in UNARY:
        return 1 + node_count(e[1])
    return 1 + node_count(e[1]) + node_count(e[2])


def simplify(e):
    """常数折叠 + 单位元消去（自底向上单层）。"""
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


def canon_key(e):
    """规范排序用的比较键。"""
    return to_string(e)


def sort_commute(e):
    """对 + 与 * 的操作数按规范顺序排序（交换律的规范型）。"""
    tag = e[0]
    if tag in ("num", "var"):
        return e
    if tag in UNARY:
        return (tag, sort_commute(e[1]))
    a, b = sort_commute(e[1]), sort_commute(e[2])
    if tag in ("+", "*") and canon_key(a) > canon_key(b):
        a, b = b, a
    return (tag, a, b)


def _sum_terms(e):
    """拆成 [(sign, factor_list)]：和的项、积的因子都摊平。"""
    tag = e[0]
    if tag in ("num", "var"):
        return [(1, [e])]
    if tag in FUNCS:
        return [(1, [(tag, e[1])])]          # 函数整体当一个因子
    if tag == "/":
        return [(1, [("/", e[1], e[2])])]
    if tag == "neg":
        return [(-s, f) for s, f in _sum_terms(e[1])]
    if tag == "+":
        return _sum_terms(e[1]) + _sum_terms(e[2])
    if tag == "-":
        return _sum_terms(e[1]) + [(-s, f) for s, f in _sum_terms(e[2])]
    if tag == "*":
        out = []
        for s1, f1 in _sum_terms(e[1]):
            for s2, f2 in _sum_terms(e[2]):
                out.append((s1 * s2, f1 + f2))
        return out
    if tag == "^":
        base, expo = e[1], e[2]
        if expo[0] == "num" and float(expo[1]).is_integer() and expo[1] >= 2:
            terms = _sum_terms(base)
            out = [(1, [])]
            for _ in range(int(expo[1])):
                nxt = []
                for s1, f1 in out:
                    for s2, f2 in terms:
                        nxt.append((s1 * s2, f1 + f2))
                out = nxt
            return out
        return [(1, [("^", base, expo)])]
    raise ValueError(tag)


def _rebuild(terms):
    """把 [(sign, factors)] 重建为表达式：系数合并、跳过零项。"""
    parts = []
    for sign, factors in terms:
        coeff = float(sign)
        rest = []
        for fac in factors:
            if fac[0] == "num":
                coeff *= fac[1]
            else:
                rest.append(fac)
        if coeff == 0:
            continue
        if not rest:
            parts.append(num(coeff))
            continue
        term = rest[0]
        for fac in rest[1:]:
            term = ("*", term, fac)
        if coeff != 1:
            term = ("*", num(coeff), term)
        parts.append(term)
    if not parts:
        return num(0)
    e = parts[0]
    for p in parts[1:]:
        e = ("+", e, p)
    return e


def expand(e):
    """展开：乘法分配到加法、整数次幂展开；函数体内部也递归展开。"""
    tag = e[0]
    if tag in ("num", "var"):
        return e
    if tag in FUNCS:
        return (tag, expand(e[1]))
    if tag == "neg":
        return ("neg", expand(e[1]))
    if tag == "/":
        return ("/", expand(e[1]), expand(e[2]))
    if tag == "^":
        base = expand(e[1])
        expo = e[2]
        if expo[0] == "num" and float(expo[1]).is_integer() and expo[1] >= 2:
            return _rebuild(_sum_terms(("^", base, expo)))
        return ("^", base, expand(expo))
    a, b = expand(e[1]), expand(e[2])
    if tag in ("+", "-"):
        return (tag, a, b)
    # tag == "*"：两边摊平做笛卡尔积
    out = []
    for s1, f1 in _sum_terms(a):
        for s2, f2 in _sum_terms(b):
            out.append((s1 * s2, f1 + f2))
    return _rebuild(out)


def collect(e, x):
    """合并关于 x 的同类项 -> 多项式规范型；非多项式返回 None。"""
    terms = _sum_terms(e)
    table = {}
    for sign, factors in terms:
        coeff = float(sign)
        degree = 0
        for fac in factors:
            if fac[0] == "num":
                coeff *= fac[1]
            elif fac[0] == "var" and fac[1] == x:
                degree += 1
            elif fac[0] == "^" and fac[1] == ("var", x) and fac[2][0] == "num":
                degree += int(fac[2][1])
            else:
                return None                  # 含其他因子：不是 x 的多项式
        if coeff != 0:
            table[degree] = table.get(degree, 0.0) + coeff
    parts = []
    for d in sorted(table, reverse=True):
        c = table[d]
        if c == 0:
            continue
        if d == 0:
            parts.append(num(c))
            continue
        xp = ("var", x) if d == 1 else ("^", ("var", x), num(d))
        if c != 1:
            xp = ("*", num(c), xp)
        parts.append(xp)
    if not parts:
        return num(0)
    e2 = parts[0]
    for p in parts[1:]:
        e2 = ("+", e2, p)
    return e2


def equivalent_by_sampling(e1, e2, trials=30, lo=-5.0, hi=5.0, seed=0):
    """随机取点检验两个表达式是否等价（教学版：非严格证明）。"""
    vars_ = sorted(collect_vars(e1) | collect_vars(e2))
    rng = random.Random(seed)
    for _ in range(trials):
        env = {v: rng.uniform(lo, hi) for v in vars_}
        try:
            v1 = evaluate(e1, env)
            v2 = evaluate(e2, env)
        except Exception:
            continue                          # 该点不在定义域，跳过
        if abs(v1 - v2) > 1e-6 * max(1.0, abs(v1), abs(v2)):
            return False
    return True


print("== 为什么需要化简与规范型 ==")
x_ = var("x")
messy = add(add(mul(num(1), x_), num(0)), mul(num(2), num(3)))
print(f"  冗长式: {to_string(messy)}")
print(f"  化简后: {to_string(simplify_deep(messy))}")
print("  同一个式子有无穷多种写法 -> 需要「规范型 canonical form」")

print("\n== 规范排序：交换律下固定顺序 ==")
e_sort = add(mul(var("y"), var("x")), add(var("b"), var("a")))
print(f"  排序前: {to_string(e_sort)}")
print(f"  排序后: {to_string(sort_commute(e_sort))}")

print("\n== 展开：乘法分配律 + 整数次幂 ==")
e1 = mul(add(x_, num(1)), add(x_, num(3)))
print(f"  (x+1)*(x+3) 展开   = {to_string(expand(e1))}")
e2 = pow_(add(x_, num(1)), 3)
print(f"  (x+1)^3 展开       = {to_string(expand(e2))}")
e3 = mul(sin_(x_), add(x_, num(1)))
print(f"  sin(x)*(x+1) 展开  = {to_string(expand(e3))}")
e_body = sin_(mul(add(x_, num(1)), add(x_, num(2))))
print(f"  函数体也展开        = {to_string(expand(e_body))}")
e_div = div(x_, add(var("y"), num(1)))
print(f"  除法不展开（保守）  = {to_string(expand(e_div))}")

print("\n== 合并同类项：得到唯一的多项式规范型 ==")
quad_cases = [
    ("(x+1)*(x+3)", e1),
    ("(x+1)^3", e2),
    ("(x+1)^2 - x^2", sub(pow_(add(x_, num(1)), 2), pow_(x_, 2))),
    ("3(x+2) + 2(x+1)", add(mul(num(3), add(x_, num(2))),
                            mul(num(2), add(x_, num(1))))),
]
for label, e in quad_cases:
    canon = collect(expand(e), "x")
    print(f"  {label:<16} -> {to_string(canon)}")

print("\n== 表达式膨胀 vs 规范型 ==")
big = pow_(add(x_, num(1)), 8)
exp_big = expand(big)
col_big = collect(exp_big, "x")
print(f"  (x+1)^8: 原式 {node_count(big)} 节点 -> 展开 {node_count(exp_big)} 节点"
      f" -> 合并 {node_count(col_big)} 节点")
print(f"  合并结果 = {to_string(col_big)}")

print("\n== 等价性验证：随机取点采样 ==")
checks = [
    ("展开 ≡ 原式", e1, expand(e1)),
    ("合并 ≡ 原式", e1, collect(expand(e1), "x")),
    ("(x+1)^8 合并 ≡ 原式", big, col_big),
    ("sin(x)*(x+1) 展开 ≡ 原式", e3, expand(e3)),
]
for label, a_, b_ in checks:
    print(f"  {label:<24}: {equivalent_by_sampling(a_, b_)}")
print("  注意：采样通过 ≠ 数学证明（但能高效抓住变换 bug）")

print("\n== 变换流水线 ==")
print("  原始式 -> simplify(常数折叠/单位元) -> sort_commute(排序)")
print("        -> expand(展开) -> collect(合并同类项) -> 规范型")
print("  规范型用途：判断两式相等、缓存命中、编译器公共子表达式消除")

print("\n== 小结 ==")
for line in (
    "  化简 = 树重写；规范型 = 树重写的不动点",
    "  展开可能指数膨胀，合并同类项把它压回线性",
    "  保守原则：不能确定语义的变换（如除法）不轻易做",
    "  下一课：多项式运算与插值（849）",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现提取公因式：x*3 + x*2 -> 5*x（对「含 x 因子的项」做简单合并）。
# 2. 用 expand + collect 验证恒等式 (x^2 - 1) == (x-1)*(x+1)（构造两式后采样对比）。
# 3. 让 sort_commute 支持嵌套：先把 a+(b+c) 扁平化成三项，再排序重建（提示：递归 flatten）。
# 4. 思考：为什么「随机取点相等」不能证明两式恒等？查一查 Schwartz-Zippel 引理给出的概率保证。
