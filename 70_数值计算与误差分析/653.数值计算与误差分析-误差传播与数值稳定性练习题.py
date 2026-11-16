# ===== 第653课：数值计算与误差分析-误差传播与数值稳定性 =====
# 知识点：
#   - 绝对误差 |x̂-x| 与相对误差 |x̂-x|/|x|；相对误差在接近 0 时会爆炸
#   - 灾难性抵消 catastrophic cancellation：两个相近大数相减，有效位大量丢失
#   - 稳定的改写法：有理化、用 math.log1p/expm1、math.hypot、math.fsum
#   - 条件数：输入相对误差被放大的倍数；问题本身病态时换算法也救不了
#   - 累加误差随 n 增长：普通 sum 是 O(n·eps)，math.fsum 带补偿几乎精确
#   - 前向误差 vs 后向误差：算法「几乎精确解了一个略微扰动的问题」即稳定
# 依赖：无（标准库）
import math

print("== 绝对误差 / 相对误差 ==")
for true, approx in ((100.0, 100.1), (1.0, 1.0001), (1e-12, 1.1e-12), (0.0, 1e-16)):
    abs_err = abs(approx - true)
    rel_err = abs_err / abs(true) if true != 0 else float("inf")
    print(f"  true={true:<8g} approx={approx:<10g} 绝对={abs_err:<10.3g} 相对={rel_err:.3g}")

print("\n== 灾难性抵消：求 sqrt(x+1) - sqrt(x) ==")
def naive(x):
    return math.sqrt(x + 1) - math.sqrt(x)

def stable(x):
    return 1 / (math.sqrt(x + 1) + math.sqrt(x))   # 有理化

for x in (1.0, 1e6, 1e12, 1e15):
    n, s = naive(x), stable(x)
    print(f"  x={x:<8g} naive={n:.12g} stable={s:.12g} "
          f"相对差={abs(n - s) / s if s else 0:.2e}")
print("  x 很大时 naive 先做两个相近大数相减，有效位被吃光")

print("\n== log1p / expm1 保住小量 ==")
for x in (1e-8, 1e-12, 1e-16):
    print(f"  x={x:<7g} log(1+x)={math.log(1 + x):.17g}  "
          f"log1p(x)={math.log1p(x):.17g}")
    print(f"          exp(x)-1 ={math.exp(x) - 1:.17g}  "
          f"expm1(x)={math.expm1(x):.17g}")

print("\n== math.fsum：补偿求和 ==")
values = [1e16, 1.0, -1e16, 1.0]      # 精确答案应为 2.0
print(f"  数据: {values}")
print(f"  sum()     = {sum(values)!r}")
print(f"  math.fsum = {math.fsum(values)!r}")
print(f"  精确值     = 2.0")

large = [1e16] + [1.0] * 10000 + [-1e16]
print(f"\n  1e16 + 10000 个 1.0 - 1e16:")
print(f"  sum()     = {sum(large)!r}  （1.0 被大数吞掉）")
print(f"  math.fsum = {math.fsum(large)!r}  （精确保留）")

print("\n== hypot 避免溢出/下溢 ==")
for a, b in ((3e308, 4e308), (1e-300, 1e-300)):
    try:
        naive_h = math.sqrt(a * a + b * b)
    except OverflowError:
        naive_h = float("inf")
    print(f"  a={a:<8g} b={b:<8g} sqrt(a²+b²)={naive_h!r}  "
          f"hypot={math.hypot(a, b)!r}")

print("\n== 条件数：问题本身是否病态 ==")
# f(x) = 1/(x-1)，x 越接近 1 条件数越大
def cond(x):
    return abs(x / (x - 1)) if x != 1 else float("inf")

for x in (2.0, 1.1, 1.01, 1.001):
    print(f"  x={x:<7g} 条件数≈{cond(x):>10.1f}  "
          f"输入扰动 1e-12 -> 输出变化≈{cond(x) * 1e-12:.2e}")
print("  条件数大时，无论算法多好，输入的一点点误差都会被放大")

print("\n== 二次方程求根的稳定写法 ==")
# ax²+bx+c=0，b 很大时 (-b+sqrt(disc)) 会抵消
def roots_naive(a, b, c):
    d = math.sqrt(b * b - 4 * a * c)
    return (-b + d) / (2 * a), (-b - d) / (2 * a)

def roots_stable(a, b, c):
    d = math.sqrt(b * b - 4 * a * c)
    q = -0.5 * (b + math.copysign(d, b))
    return q / a, c / q        # 用 Vieta 关系 c/(a*x1)

a, b, c = 1.0, 1e8, 1.0
print(f"  a={a} b={b:g} c={c}")
print(f"  naive : {roots_naive(a, b, c)}")
print(f"  stable: {roots_stable(a, b, c)}")
print("  Vieta 校验 x1*x2 == c/a:")
for name, rs in (("naive", roots_naive(a, b, c)), ("stable", roots_stable(a, b, c))):
    print(f"    {name:<7}: {rs[0] * rs[1]:.6g} (期望 {c/a:g})")

print("\n== 误差分析清单 ==")
for line in [
    "  先判断是「算法不稳定」还是「问题病态」：前者换公式，后者改模型",
    "  避免相近大数相减、避免小量加到大数上",
    "  优先用 math 模块里专门的函数（fsum/log1p/expm1/hypot）",
    "  关键结果用高精度 Decimal/mpmath 做一次交叉验证",
]:
    print(line)

# ===== 练习题 =====
# 1. 用 math.fsum 重写方差公式，对比「两遍法」与「朴素累加法」的稳定性。
# 2. 推导 1-cos(x) 的稳定写法（提示：2*sin²(x/2)），在 x→0 时验证。
# 3. 计算 f(x)=1/(x-1) 在 x=1.0001 处的条件数，并实测输入扰动的输出变化。
# 4. 思考：为什么「后向稳定」的算法即使前向误差大，仍被认为可靠？
