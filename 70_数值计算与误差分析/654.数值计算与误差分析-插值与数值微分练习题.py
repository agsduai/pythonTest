# ===== 第654课：数值计算与误差分析-插值与数值微分 =====
# 知识点：
#   - 线性插值：两点间用直线近似；实现简单，导数不连续
#   - 拉格朗日插值：过 n 个点的 n-1 次多项式；节点等距时高次会龙格现象（边缘震荡）
#   - 数值微分：前向/后向/中心差分；中心差分误差 O(h²) 优于一阶 O(h)
#   - 步长 h 的权衡：太大截断误差大，太小舍入误差大，存在最优 h≈eps^(1/3)
#   - 用已知解析导数的函数做基准，量化不同 h 下的误差曲线
#   - 分段低次插值（样条思想）比全局高次更稳
# 依赖：无（标准库）
import math

print("== 线性插值 ==")
def lerp(x0, y0, x1, y1, x):
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)

knots = [(0, 0), (1, 1), (2, 4), (3, 9)]      # 采样自 x²
def linear_interp(pts, x):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return lerp(x0, y0, x1, y1, x)
    return pts[0][1] if x < pts[0][0] else pts[-1][1]

for x in (0.5, 1.5, 2.5):
    print(f"  x={x}: 线性={linear_interp(knots, x):.3f} 真实 x²={x*x:.3f} "
          f"误差={abs(linear_interp(knots, x) - x*x):.3f}")

print("\n== 拉格朗日插值 ==")
def lagrange(pts, x):
    total = 0.0
    for i, (xi, yi) in enumerate(pts):
        term = yi
        for j, (xj, _) in enumerate(pts):
            if i != j:
                term *= (x - xj) / (xi - xj)
        total += term
    return total

pts4 = [(0, 0), (1, 1), (2, 4), (3, 9)]
for x in (0.5, 1.5, 2.5):
    print(f"  x={x}: 拉格朗日={lagrange(pts4, x):.6f} 真实={x*x:.6f}")
print("  用 4 个点拟合 x²（二次），拉格朗日应当精确还原：",
      abs(lagrange(pts4, 1.7) - 1.7**2) < 1e-9)

print("\n== 龙格现象：等距高次插值会震荡 ==")
def runge(x):
    return 1 / (1 + 25 * x * x)

for n in (5, 9, 15):
    nodes = [(-1 + 2 * i / (n - 1)) for i in range(n)]
    pts = [(xi, runge(xi)) for xi in nodes]
    errs = [abs(lagrange(pts, -1 + 2 * k / 200) - runge(-1 + 2 * k / 200))
            for k in range(201)]
    print(f"  n={n:>2} 个等距节点: 最大误差={max(errs):.3f}  "
          f"边缘误差={errs[0]:.3f}/{errs[-1]:.3f}")
print("  节点越多边缘反而越差 -> 改用切比雪夫节点或分段样条")

print("\n== 数值微分：三种差分 ==")
def f(x):
    return math.sin(x)

def df_true(x):
    return math.cos(x)

def forward(f, x, h):
    return (f(x + h) - f(x)) / h

def backward(f, x, h):
    return (f(x) - f(x - h)) / h

def central(f, x, h):
    return (f(x + h) - f(x - h)) / (2 * h)

x = 1.0
print(f"  f=sin, x={x}, 真实导数 cos(x)={df_true(x):.12f}")
print(f"  {'h':<12}{'前向误差':>14}{'中心误差':>14}")
for h in (1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-7, 1e-10, 1e-14):
    ef = abs(forward(f, x, h) - df_true(x))
    ec = abs(central(f, x, h) - df_true(x))
    print(f"  {h:<12g}{ef:>14.3e}{ec:>14.3e}")

print("\n== 最优步长 ==")
hs = [10 ** (-k) for k in range(1, 16)]
best = min(hs, key=lambda h: abs(central(f, x, h) - df_true(x)))
print(f"  中心差分实测最优 h ≈ {best:g}（理论 eps^(1/3) ≈ {2.22e-16 ** (1/3):.2e}）")
print("  h 再小：浮点相减的舍入误差反超截断误差，误差回升")

print("\n== 二阶导数（三点格式）==")
def d2(f, x, h):
    return (f(x + h) - 2 * f(x) + f(x - h)) / (h * h)

for h in (1e-2, 1e-3, 1e-4, 1e-5):
    print(f"  h={h:<7g} f''(1) 估计={d2(f, x, h):.8f} 真实={-math.sin(x):.8f} "
          f"误差={abs(d2(f, x, h) + math.sin(x)):.2e}")

print("\n== 工程要点 ==")
for line in [
    "  插值点数少用线性/低次；点多用分段样条，别硬上高次多项式",
    "  微分优先中心差分；能用解析导数/自动微分就别数值差分",
    "  步长按量级取 h≈|x|·eps^(1/3)，不要无脑 1e-8",
    "  噪声数据先平滑再微分，差分会把噪声放大 1/h 倍",
]:
    print(line)

# ===== 练习题 =====
# 1. 用切比雪夫节点重做龙格函数插值，对比等距节点的最大误差。
# 2. 实现五点中心差分（O(h⁴)），画出误差-步长曲线找最优 h。
# 3. 给含噪声的采样值加简单移动平均，再比较微分误差。
# 4. 思考：为什么数值微分对噪声极其敏感，而数值积分相对稳健？
