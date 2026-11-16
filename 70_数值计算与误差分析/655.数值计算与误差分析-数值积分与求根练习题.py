# ===== 第655课：数值计算与误差分析-数值积分与求根 =====
# 知识点：
#   - 数值积分：矩形法 O(h) / 梯形法 O(h²) / 辛普森法 O(h⁴)
#   - 自适应细分：在曲率大的区间多分段，用误差估计决定是否继续细分
#   - 求根：二分法（稳但慢）、牛顿法（快但需导数且可能发散）、割线法（无需导数）
#   - 收敛判据要用「区间宽度 + 函数值」双条件，别只看迭代次数
#   - 病态情形：重根、导数接近 0、不连续函数，二分法最可靠
#   - 用已知解析解的函数（∫x²、sin 的零点）量化误差与收敛速度
# 依赖：无（标准库）
import math

print("== 数值积分：∫₀¹ x² dx = 1/3 ==")
def f(x):
    return x * x

EXACT = 1 / 3

def rectangle(f, a, b, n):
    h = (b - a) / n
    return h * sum(f(a + i * h) for i in range(n))

def trapezoid(f, a, b, n):
    h = (b - a) / n
    return h * (0.5 * f(a) + sum(f(a + i * h) for i in range(1, n)) + 0.5 * f(b))

def simpson(f, a, b, n):
    if n % 2:
        n += 1
    h = (b - a) / n
    s = f(a) + f(b)
    s += 4 * sum(f(a + i * h) for i in range(1, n, 2))
    s += 2 * sum(f(a + i * h) for i in range(2, n, 2))
    return h * s / 3

print(f"  精确值 = {EXACT:.12f}")
print(f"  {'n':<8}{'矩形误差':>14}{'梯形误差':>14}{'辛普森误差':>14}")
for n in (4, 8, 16, 64, 256):
    er = abs(rectangle(f, 0, 1, n) - EXACT)
    et = abs(trapezoid(f, 0, 1, n) - EXACT)
    es = abs(simpson(f, 0, 1, n) - EXACT)
    print(f"  {n:<8}{er:>14.3e}{et:>14.3e}{es:>14.3e}")
print("  辛普森对二次多项式应当精确（误差只来自舍入）")

print("\n== 自适应积分（按局部误差细分）==")
def adaptive_simpson(f, a, b, tol=1e-8, max_depth=20):
    def whole(a, b, fa, fb, fm):
        return (b - a) / 6 * (fa + 4 * fm + fb)

    def rec(a, b, fa, fb, fm, S, tol, depth):
        m = (a + b) / 2
        lm, rm = (a + m) / 2, (m + b) / 2
        flm, frm = f(lm), f(rm)
        SL = whole(a, m, fa, fm, flm)
        SR = whole(m, b, fm, fb, frm)
        if depth <= 0 or abs(SL + SR - S) <= 15 * tol:
            return SL + SR + (SL + SR - S) / 15
        return (rec(a, m, fa, fm, flm, SL, tol / 2, depth - 1) +
                rec(m, b, fm, fb, frm, SR, tol / 2, depth - 1))

    fa, fb, fm = f(a), f(b), f((a + b) / 2)
    S = whole(a, b, fa, fb, fm)
    return rec(a, b, fa, fb, fm, S, tol, max_depth)

def oscillatory(x):
    return math.sin(10 * x) / (1 + x)

for tol in (1e-4, 1e-8, 1e-12):
    val = adaptive_simpson(oscillatory, 0, 1, tol)
    ref = adaptive_simpson(oscillatory, 0, 1, 1e-14)
    print(f"  tol={tol:<7g} 结果={val:.12f} 与高精度参考差={abs(val - ref):.2e}")

print("\n== 求根：二分法 / 牛顿法 / 割线法 ==")
def g(x):
    return x * x - 2          # 根 = sqrt(2)

def dg(x):
    return 2 * x

ROOT = math.sqrt(2)

def bisect(f, a, b, tol=1e-12, max_iter=200):
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError("区间两端同号，无法保证有根")
    for i in range(1, max_iter + 1):
        m = (a + b) / 2
        fm = f(m)
        if abs(fm) < tol or (b - a) / 2 < tol:
            return m, i
        if fa * fm < 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    return (a + b) / 2, max_iter

def newton(f, df, x0, tol=1e-12, max_iter=50):
    x = x0
    for i in range(1, max_iter + 1):
        fx, dfx = f(x), df(x)
        if dfx == 0:
            return x, i, "导数为零"
        step = fx / dfx
        x -= step
        if abs(step) < tol:
            return x, i, "收敛"
    return x, max_iter, "未收敛"

def secant(f, x0, x1, tol=1e-12, max_iter=50):
    f0, f1 = f(x0), f(x1)
    for i in range(1, max_iter + 1):
        if f1 - f0 == 0:
            return x1, i, "分母为零"
        x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
        if abs(x2 - x1) < tol:
            return x2, i, "收敛"
        x0, f0, x1, f1 = x1, f1, x2, f(x2)
    return x1, max_iter, "未收敛"

b, it_b = bisect(g, 0, 2)
n, it_n, st_n = newton(g, dg, 1.0)
s, it_s, st_s = secant(g, 0.0, 2.0)
print(f"  真实根 sqrt(2) = {ROOT:.12f}")
print(f"  二分法  : {b:.12f}  迭代 {it_b:>3} 次  误差={abs(b-ROOT):.2e}")
print(f"  牛顿法  : {n:.12f}  迭代 {it_n:>3} 次  误差={abs(n-ROOT):.2e}  {st_n}")
print(f"  割线法  : {s:.12f}  迭代 {it_s:>3} 次  误差={abs(s-ROOT):.2e}  {st_s}")

print("\n== 牛顿法的发散风险 ==")
def h(x):
    return x ** (1 / 3) if x >= 0 else -((-x) ** (1 / 3))

def dh(x):
    return 1 / (3 * abs(x) ** (2 / 3)) if x != 0 else float("inf")

x = 1.0
seq = [x]
for _ in range(6):
    x = x - h(x) / dh(x)
    seq.append(x)
print("  f(x)=x^(1/3) 从 x=1 出发:", [round(v, 3) for v in seq])
print("  导数在根附近趋于 0，迭代步长反而放大 -> 发散；此时二分法更可靠")

print("\n== 收敛判据 ==")
for line in (
    "  双条件: |f(x)| < tol 且 |Δx| < tol，单看一个都可能误判",
    "  相对容差处理量级差异大的根：|Δx| <= rtol*|x| + atol",
    "  必设 max_iter 与区间有效性检查，防死循环",
    "  多根函数先扫描变号区间，再对每个区间单独求根",
):
    print(line)

# ===== 练习题 =====
# 1. 实现复合高斯-勒让德积分，与辛普森法在同等函数求值次数下比较精度。
# 2. 给牛顿法加步长阻尼（line search），修复上面发散的例子。
# 3. 实现 brent 风格混合法：二分保底 + 割线加速。
# 4. 思考：为什么自适应积分要按「局部曲率」而非全局均匀细分？
