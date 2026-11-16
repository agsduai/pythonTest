# ===== 第845课：符号计算与自动微分-前向模式自动微分 =====
# 知识点：
#   - 对偶数（dual number）：a + bε，规定 ε² = 0 —— 代数系统里「藏」着导数
#   - (a+bε)·(c+dε) = ac + (ad+bc)ε —— ε 系数恰好自动实现乘积法则
#   - 前向模式：从输入向输出同时传播「值 + 导数」，一次得到一个方向的方向导数
#   - 与第844课符号微分的区别：不生成表达式，导数直接随计算传播数字
#   - 截断泰勒数 T2：把 ε² 保留下来，一次前向同时得到 f、f'、f''
# 依赖：无（标准库）
import math


class Dual:
    """对偶数：value = a，deriv = b（表示 a + bε，ε² = 0）。"""
    __slots__ = ("value", "deriv")

    def __init__(self, value, deriv=0.0):
        self.value = value
        self.deriv = deriv

    def __add__(self, other):
        o = _wrap(other)
        return Dual(self.value + o.value, self.deriv + o.deriv)

    __radd__ = __add__                       # 加法可交换

    def __sub__(self, other):
        o = _wrap(other)
        return Dual(self.value - o.value, self.deriv - o.deriv)

    def __rsub__(self, other):
        return _wrap(other) - self

    def __mul__(self, other):
        o = _wrap(other)
        return Dual(self.value * o.value,
                    self.deriv * o.value + self.value * o.deriv)

    __rmul__ = __mul__                       # 乘法可交换

    def __truediv__(self, other):
        o = _wrap(other)
        if o.value == 0:
            raise ZeroDivisionError("对偶数除零")
        return Dual(self.value / o.value,
                    (self.deriv * o.value - self.value * o.deriv) / o.value ** 2)

    def __rtruediv__(self, other):
        return _wrap(other) / self

    def __pow__(self, p):
        return Dual(self.value ** p,
                    p * self.value ** (p - 1) * self.deriv)

    def __neg__(self):
        return Dual(-self.value, -self.deriv)

    def __repr__(self):
        return f"Dual({self.value:.6f}, ε:{self.deriv:.6f})"


def _wrap(x):
    return x if isinstance(x, Dual) else Dual(x)


def d_exp(u):
    e = math.exp(u.value)
    return Dual(e, e * u.deriv)


def d_sin(u):
    return Dual(math.sin(u.value), math.cos(u.value) * u.deriv)


def d_cos(u):
    return Dual(math.cos(u.value), -math.sin(u.value) * u.deriv)


def d_log(u):
    if u.value <= 0:
        raise ValueError("log 定义域为正数")
    return Dual(math.log(u.value), u.deriv / u.value)


def forward(f, x, seed=1.0):
    """一次前向：返回 (f(x), f'(x))。seed 是输入扰动方向。"""
    r = f(Dual(x, seed))
    return r.value, r.deriv


print("== 对偶数的代数 ==")
a = Dual(3.0, 1.0)
b = Dual(2.0, 1.0)
print(f"  a = 3 + 1ε, b = 2 + 1ε")
print(f"  a + b = {a + b}    （5 + 2ε）")
print(f"  a * b = {a * b}    （6 + 5ε：ε 系数 = 3·1 + 1·2 —— 乘积法则！）")
print(f"  a / b = {a / b}    （(a'b - ab')/b^2 = (2 - 3)/4 = -0.25）")
print(f"  a^2   = {a ** 2}    （9 + 6ε）")

print("\n== 前向模式：求值与求导同步完成 ==")
cases = [
    ("x^2 + 3*x + 2", lambda t: t * t + 3 * t + 2,
     lambda v: 2 * v + 3),
    ("sin(x) * x",    lambda t: d_sin(t) * t,
     lambda v: math.sin(v) + v * math.cos(v)),
    ("exp(0.5 * x)",  lambda t: d_exp(0.5 * t),
     lambda v: 0.5 * math.exp(0.5 * v)),
    ("log(x^2 + 1)",  lambda t: d_log(t * t + 1),
     lambda v: 2 * v / (v * v + 1)),
    ("x^3 - 2*x",     lambda t: t ** 3 - 2 * t,
     lambda v: 3 * v * v - 2),
]
for label, f, fprime in cases:
    row = f"  {label:<15}"
    for xv in (0.5, 1.3, 2.7):
        val, der = forward(f, xv)
        err = abs(der - fprime(xv))
        row += f"  f({xv})={val:.4f} f'={der:.6f} 误差{err:.0e}"
    print(row)

print("\n== 链式法则：导数沿着计算一步步「流」出来 ==")
t = Dual(1.0, 1.0)
u = t * t + 1                       # 内层 u = x^2 + 1，u' = 2x = 2
r = d_exp(u)                        # 外层 exp(u)，r' = exp(u)·u'
print(f"  内层 u = x^2 + 1 -> {u}")
print(f"  外层 exp(u)      -> {r}")
print(f"  f'(1) = {r.deriv:.6f}   解析 2x·exp(x^2+1) = {2 * math.exp(2):.6f}")

print("\n== 多变量梯度：n 个输入需要 n 次前向 ==")


def f2(u, v):
    return u * u * v + d_sin(u)


def gradient_forward(fn, point):
    grads = []
    for i in range(len(point)):
        args = tuple(Dual(p, 1.0 if i == j else 0.0)
                     for j, p in enumerate(point))
        grads.append(fn(*args).deriv)
    return grads


point = (2.0, 3.0)
grad = gradient_forward(f2, point)
print(f"  f(x,y) = x^2*y + sin(x)   ∇f(2,3) = [{grad[0]:.6f}, {grad[1]:.6f}]")
print(f"  解析                      = [{2 * 2 * 3 + math.cos(2):.6f}, {4.0:.6f}]")

print("\n== 方向导数（JVP）：一次前向直接算 ∇f·v ==")
d = f2(Dual(2.0, 1.0), Dual(3.0, 2.0))
gx, gy = 2 * 2 * 3 + math.cos(2), 4.0
print(f"  方向 v = (1, 2) -> 方向导数 = {d.deriv:.6f}")
print(f"  ∇f·v                       = {gx * 1 + gy * 2:.6f}")


print("\n== 截断泰勒数 T2：保留到 ε²，一次前向得 f、f'、f'' ==")


class T2:
    """a + bε + cε²（ε³ 舍弃）。乘法的 ε² 系数 = a1·c2 + b1·b2 + c1·a2。"""
    __slots__ = ("a", "b", "c")

    def __init__(self, a, b=0.0, c=0.0):
        self.a, self.b, self.c = a, b, c

    def __add__(self, other):
        o = _w(other)
        return T2(self.a + o.a, self.b + o.b, self.c + o.c)

    def __sub__(self, other):
        o = _w(other)
        return T2(self.a - o.a, self.b - o.b, self.c - o.c)

    def __mul__(self, other):
        o = _w(other)
        return T2(self.a * o.a,
                  self.b * o.a + self.a * o.b,
                  self.c * o.a + self.b * o.b + self.a * o.c)

    def __pow__(self, p):
        aa, bb, cc = self.a, self.b, self.c
        return T2(aa ** p,
                  p * aa ** (p - 1) * bb,
                  p * aa ** (p - 1) * cc + p * (p - 1) / 2 * aa ** (p - 2) * bb * bb)


def _w(x):
    return x if isinstance(x, T2) else T2(x)


def t2_exp(u):
    e = math.exp(u.a)
    return T2(e, e * u.b, e * (u.c + u.b * u.b / 2))


def t2_sin(u):
    s, c = math.sin(u.a), math.cos(u.a)
    return T2(s, c * u.b, c * u.c - s * u.b * u.b / 2)


def taylor2(f, x):
    """返回 (f(x), f'(x), f''(x))：ε² 系数是 f''/2。"""
    r = f(T2(x, 1.0, 0.0))
    return r.a, r.b, 2.0 * r.c


for label, fn, f2nd in (
    ("x^3",      lambda t: t ** 3,        lambda v: 6 * v),
    ("exp(x^2)", lambda t: t2_exp(t * t), lambda v: (2 + 4 * v * v) * math.exp(v * v)),
    ("x*sin(x)", lambda t: t2_sin(t) * t, lambda v: 2 * math.cos(v) - v * math.sin(v)),
):
    for xv in (0.7, 1.3):
        _, _, d2 = taylor2(fn, xv)
        ok = abs(d2 - f2nd(xv)) < 1e-9
        print(f"  {label:<9} x={xv:<4} f''(T2) = {d2:.9f}  解析 = {f2nd(xv):.9f}  一致 = {ok}")

print("\n== AD 精确 vs 数值差分近似 ==")
h = 1e-6
for label, fd, fn, xv in (
    ("sin(x) * x", lambda t: d_sin(t) * t,     lambda v: math.sin(v) * v,     1.3),
    ("exp(0.5*x)", lambda t: d_exp(0.5 * t),   lambda v: math.exp(0.5 * v),   1.3),
    ("log(x^2+1)", lambda t: d_log(t * t + 1), lambda v: math.log(v * v + 1), 2.0),
):
    _, der = forward(fd, xv)
    nd = (fn(xv + h) - fn(xv - h)) / (2 * h)
    print(f"  {label:<12} AD = {der:.12f}   中心差分 = {nd:.12f}   差 = {abs(der - nd):.1e}")

print("\n== 前向模式的适用边界 ==")
for line in (
    "  一次前向 = 一个方向的方向导数（JVP）",
    "  n 个输入要 n 次前向才有完整梯度",
    "  适合：输入少、输出多 —— 灵敏度分析、单方向导数",
    "  不适合：输入多、输出少（如 ML 训练）-> 反向模式（第846课）",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 验证 __pow__ 的推广：f(x) = x^(-1) 在 x=2 的导数应为 -0.25，f(x) = x^0.5 在 x=4 应为 0.25。
# 2. 用前向模式计算 logistic σ(x) = 1/(1+exp(-x)) 在 x=0 的 σ 与 σ'（0.5 与 0.25）。
# 3. 实现 jvp(f, point, direction)：一次前向返回方向导数，并用中心差分验证。
# 4. 思考：为什么 ε² = 0 这一条代数规定恰好实现了乘积法则？
