# ===== 第849课：符号计算与自动微分-多项式运算与插值 =====
# 知识点：
#   - 多项式的系数表示：[c0, c1, c2, ...] = c0 + c1·x + c2·x^2 + ...
#   - 加减法是系数对位相加，乘法是系数卷积；求值用 Horner/秦九韶法 O(n)
#   - 长除法与余式定理：P ÷ (x-a) 的余数 = P(a)
#   - 拉格朗日插值 / 牛顿均差：n+1 个点唯一确定 n 次多项式
#   - 插值的陷阱：只保证节点处精确，节点间有偏差、外推误差大、高次会振荡（Runge）
# 依赖：无（标准库）
import math


def p_trim(a):
    """去掉高位零系数（至少保留 [0.0]）。"""
    n = len(a)
    while n > 1 and a[n - 1] == 0:
        n -= 1
    return a[:n]


def p_add(a, b):
    n = max(len(a), len(b))
    return [((a[i] if i < len(a) else 0.0) + (b[i] if i < len(b) else 0.0))
            for i in range(n)]


def p_sub(a, b):
    n = max(len(a), len(b))
    return [((a[i] if i < len(a) else 0.0) - (b[i] if i < len(b) else 0.0))
            for i in range(n)]


def p_mul(a, b):
    out = [0.0] * (len(a) + len(b) - 1)
    for i, ca in enumerate(a):
        if ca == 0:
            continue
        for j, cb in enumerate(b):
            out[i + j] += ca * cb
    return out


def p_scale(a, s):
    return [c * s for c in a]


def p_eval(a, x):
    """Horner/秦九韶法：n 次乘法。"""
    acc = 0.0
    for c in reversed(a):
        acc = acc * x + c
    return acc


def p_eval_naive(a, x):
    """朴素幂求和：O(n^2)（教学对照）。"""
    return sum(c * x ** i for i, c in enumerate(a))


def p_deriv(a):
    if len(a) <= 1:
        return [0.0]
    return [i * a[i] for i in range(1, len(a))]


def p_str(a):
    parts = []
    for i in range(len(a) - 1, -1, -1):
        c = a[i]
        if c == 0:
            continue
        mag = abs(c)
        cs = str(int(mag)) if mag == int(mag) else f"{mag:g}"
        if i == 0:
            body = cs
        else:
            xp = "x" if i == 1 else f"x^{i}"
            body = xp if mag == 1 else f"{cs}{xp}"
        if not parts:
            parts.append(("-" + body) if c < 0 else body)
        else:
            parts.append(("- " if c < 0 else "+ ") + body)
    return " ".join(parts) if parts else "0"


def p_divmod(a, b):
    """多项式长除法：返回 (商, 余数)。"""
    a, b = p_trim(list(a)), p_trim(list(b))
    if b == [0.0]:
        raise ZeroDivisionError("多项式除零")
    q = [0.0] * max(len(a) - len(b) + 1, 1)
    r = list(a)
    lead = b[-1]
    guard = len(a) + 10
    while len(r) >= len(b) and r[-1] != 0 and guard > 0:
        guard -= 1
        shift = len(r) - len(b)
        factor = r[-1] / lead
        q[shift] += factor
        for i, cb in enumerate(b):
            r[shift + i] -= factor * cb
        r = p_trim(r)
    return p_trim(q), r


def lagrange_interpolate(points):
    """过给定点的拉格朗日插值多项式（系数列表）。"""
    n = len(points)
    result = [0.0] * n
    for i, (xi, yi) in enumerate(points):
        basis = [1.0]
        denom = 1.0
        for j, (xj, _) in enumerate(points):
            if j == i:
                continue
            if xi == xj:
                raise ValueError("插值节点 x 重复")
            basis = p_mul(basis, [-xj, 1.0])
            denom *= xi - xj
        result = p_add(result, p_scale(basis, yi / denom))
    return p_trim(result)


def newton_divided_diff(points):
    """牛顿均差系数：p(x) = c0 + c1(x-x0) + c2(x-x0)(x-x1) + ..."""
    xs = [p[0] for p in points]
    coef = [float(p[1]) for p in points]
    n = len(points)
    for j in range(1, n):
        for i in range(n - 1, j - 1, -1):
            coef[i] = (coef[i] - coef[i - 1]) / (xs[i] - xs[i - j])
    return coef


def newton_eval(coef, xs, x):
    """牛顿形式的嵌套（Horner 式）求值。"""
    acc = 0.0
    for k in reversed(range(len(coef))):
        acc = acc * (x - xs[k]) + coef[k]
    return acc


def newton_to_poly(coef, xs):
    """牛顿形式 -> 标准系数列表。"""
    poly = [coef[-1]]
    for k in range(len(coef) - 2, -1, -1):
        poly = p_add(p_mul(poly, [-xs[k], 1.0]), [coef[k]])
    return p_trim(poly)


print("== 多项式的系数表示与 Horner 求值 ==")
P = [1.0, -3.0, 2.0]                    # 1 - 3x + 2x^2
print(f"  P = {p_str(P)}")
for xv in (0.0, 1.0, 1.7):
    print(f"  P({xv}) = {p_eval(P, xv):.6f}   朴素法 = {p_eval_naive(P, xv):.6f}")
print("  Horner：n 次乘法；朴素：O(n^2) 次乘法 —— 高次时差距巨大")

print("\n== 加减乘 ==")
Q = [1.0, 1.0]                          # 1 + x
print(f"  P + Q = {p_str(p_trim(p_add(P, Q)))}")
print(f"  P - Q = {p_str(p_trim(p_sub(P, Q)))}")
PQ = p_mul(P, Q)
print(f"  P * Q = {p_str(p_trim(PQ))}")
xv = 1.7
print(f"  验证: P*Q 在 {xv} = {p_eval(PQ, xv):.6f},  P(x)·Q(x) = {p_eval(P, xv) * p_eval(Q, xv):.6f}")

print("\n== 导数 ==")
dP = p_deriv(P)
print(f"  P' = {p_str(dP)}")
h = 1e-6
print(f"  P'(1.7) = {p_eval(dP, 1.7):.6f}   中心差分 = "
      f"{(p_eval(P, 1.7 + h) - p_eval(P, 1.7 - h)) / (2 * h):.6f}")

print("\n== 长除法与余式定理 ==")
q1, r1 = p_divmod(P, [-1.0, 1.0])       # ÷ (x - 1)
print(f"  P ÷ (x-1) = 商 {p_str(q1)}，余 {p_str(r1)}")
P2 = [1.0, -1.0, 1.0, 2.0]              # 1 - x + x^2 + 2x^3
q2, r2 = p_divmod(P2, [2.0, 1.0])       # ÷ (x + 2)
print(f"  (2x^3 + x^2 - x + 1) ÷ (x+2) = 商 {p_str(q2)}，余 {p_str(r2)}")
for a_ in (0.7, -1.3):
    _, rem = p_divmod(P, [-a_, 1.0])
    sign = "-" if a_ >= 0 else "+"
    print(f"  余式定理: P ÷ (x {sign} {abs(a_):g}) 的余数 = {rem[0]:.6f}"
          f"  vs  P({a_}) = {p_eval(P, a_):.6f}（差 {abs(rem[0] - p_eval(P, a_)):.1e}）")

print("\n== 拉格朗日插值：3 点唯一确定 2 次多项式 ==")
pts = [(0.0, 1.0), (1.0, 0.0), (3.0, 10.0)]     # 取自 P = 2x^2 - 3x + 1
rec = lagrange_interpolate(pts)
print(f"  节点 {pts}")
print(f"  插值结果 = {p_str(rec)}")
same = len(rec) == len(P) and all(abs(rec[i] - P[i]) < 1e-9 for i in range(len(P)))
print(f"  原多项式 = {p_str(P)}   系数一致: {same}")
ok = all(abs(p_eval(rec, t) - p_eval(P, t)) < 1e-9 for t in (0.3, 1.7, 2.5, 4.2))
print(f"  随机点验证插值 ≡ 原多项式: {ok}")

print("\n== 牛顿均差形式 ==")
coef = newton_divided_diff(pts)
xs = [p[0] for p in pts]
print(f"  均差系数 = {coef}")
for t in (0.3, 1.7, 2.5):
    print(f"  x={t}: 牛顿形式 = {newton_eval(coef, xs, t):.6f}   P({t}) = {p_eval(P, t):.6f}")
print(f"  转标准系数 = {newton_to_poly(coef, xs)}")

print("\n== 插值的陷阱：节点精确 ≠ 处处精确 ==")
pts_sin = [(0.0, 0.0), (math.pi / 4, math.sin(math.pi / 4)), (math.pi / 2, 1.0)]
psin = lagrange_interpolate(pts_sin)
print(f"  用 3 个点插值 sin(x): {p_str(psin)}")
for t in (math.pi / 3, math.pi):
    iv = p_eval(psin, t)
    print(f"  x={t:.4f}: 插值 = {iv:.6f}   sin = {math.sin(t):.6f}   误差 = {abs(iv - math.sin(t)):.4f}")
print("  节点内(π/3)误差小，外推(π)误差大；等距高次插值会振荡（Runge 现象）")

print("\n== 表示法对比 ==")
print(f"  {'表示':<12}{'优点':<28}{'缺点'}")
for row in (("系数列表", "加减乘/求值都简单", "只适合多项式"),
            ("表达式树", "通用、可微分", "求值/化更复杂"),
            ("牛顿形式", "加点方便、数值稳", "需转系数才能乘除")):
    print(f"  {row[0]:<12}{row[1]:<28}{row[2]}")

print("\n== 小结 ==")
for line in (
    "  系数列表 + Horner 是多项式的标准工作表示",
    "  长除法/余式定理把「求值」与「除法」联系起来",
    "  n+1 点唯一确定 n 次多项式：插值 = 从数据恢复模型",
    "  插值只在节点处精确：区间内近似、区间外外推风险大",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 p_compose(a, b)：多项式复合 P(Q(x)) 的系数（提示：反复 p_mul 与 p_add）。
# 2. 实现 p_gcd：用欧几里得算法 + p_divmod 求 x^2-1 与 x^2-2x+1 的最大公因式（应为 x-1）。
# 3. 用 4 个点做三次插值并验证；再统计拉格朗日与牛顿形式各需要多少次乘除。
# 4. 思考：为什么等距节点的「高次」插值会振荡（Runge 现象）？切比雪夫节点为什么能缓解？
