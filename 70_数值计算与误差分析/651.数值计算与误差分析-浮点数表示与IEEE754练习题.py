# ===== 第651课：数值计算与误差分析-浮点数表示与IEEE754 =====
# 知识点：
#   - IEEE 754 双精度：1 符号位 + 11 指数位 + 52 尾数位，共 64 bit
#   - 0.1 + 0.2 != 0.3：十进制有限小数在二进制里可能是无限循环
#   - 机器精度 eps：1.0 与「下一个可表示数」的间隔，约 2.22e-16
#   - 特殊值：inf / -inf / nan；nan != nan，要用 math.isnan 判断
#   - struct.pack/unpack 与 float.hex() 可查看精确位模式
#   - 次正规数（subnormal）填补 0 与最小正规数之间的空隙
# 依赖：无（标准库）
import math
import struct
import sys

print("== 经典反直觉 ==")
a = 0.1 + 0.2
print(f"  0.1 + 0.2 = {a!r}")
print(f"  0.3       = {0.3!r}")
print(f"  相等吗    : {a == 0.3}   差值 = {a - 0.3:.17g}")
print("  0.1 的精确十进制:", f"{0.1:.20f}")
print("  0.1 的十六进制:  ", (0.1).hex())

print("\n== 位模式（IEEE 754 binary64）==")
def bits(x: float) -> str:
    return format(struct.unpack(">Q", struct.pack(">d", x))[0], "064b")

def parts(x: float):
    u = struct.unpack(">Q", struct.pack(">d", x))[0]
    sign = (u >> 63) & 1
    exp = (u >> 52) & 0x7FF
    frac = u & ((1 << 52) - 1)
    return sign, exp, frac

for x in (0.0, -0.0, 1.0, 0.1, 2.0, float("inf"), float("nan")):
    s, e, f = parts(x)
    print(f"  {str(x):<8} sign={s} exp={e:>4} (biased) frac高位={f >> 48:>4}  "
          f"bits={bits(x)[:16]}...")

print("\n== 机器精度 eps ==")
eps = sys.float_info.epsilon
print(f"  sys.float_info.epsilon = {eps:.17g} (= 2^-52)")
print(f"  nextafter(1.0, 2)      = {math.nextafter(1.0, 2.0)!r}")
print(f"  1.0 + eps == 1.0       : {1.0 + eps == 1.0}")
print(f"  1.0 + eps/2 == 1.0     : {1.0 + eps / 2 == 1.0}")
print(f"  大数处间隔更大: nextafter(1e16, inf) - 1e16 = "
      f"{math.nextafter(1e16, math.inf) - 1e16:.1f}")

print("\n== 特殊值 ==")
values = (float("inf"), float("-inf"), float("nan"))
for v in values:
    print(f"  {v!r:<8} isinf={math.isinf(v)} isnan={math.isnan(v)} isfinite={math.isfinite(v)}")
print(f"  nan == nan       : {float('nan') == float('nan')}")
print(f"  math.isnan(nan)  : {math.isnan(float('nan'))}")
print(f"  1/0 不返回 inf 而是抛异常：", end=" ")
try:
    _ = 1 / 0
except ZeroDivisionError as e:
    print(type(e).__name__, e)
print(f"  1e308 * 1e10 = {1e308 * 1e10!r}（溢出为 inf）")

print("\n== 有符号零 ==")
print(f"  -0.0 == 0.0 : {-0.0 == 0.0}")
print("  两者数值相等，但符号位不同，用 copysign 区分:")
print(f"  copysign(1, 0.0)  = {math.copysign(1, 0.0):.1f}")
print(f"  copysign(1, -0.0) = {math.copysign(1, -0.0):.1f}")

print("\n== 次正规数 ==")
tiny = 5e-324
print(f"  最小次正规数 = {tiny!r}  isfinite={math.isfinite(tiny)}")
print(f"  最小正规数   = {sys.float_info.min!r}")
print(f"  tiny / 2     = {tiny / 2!r}（下溢为 0）")

print("\n== 精度随量级变化 ==")
for x in (1e-10, 1.0, 1e10, 1e16):
    step = math.nextafter(x, math.inf) - x
    print(f"  x={x:<8g} 相邻可表示间隔≈{step:.3g}")

print("\n== 实用结论 ==")
for line in [
    "金额/计数绝不用 float，用 Decimal 或整数分（第652课）",
    "比较用 math.isclose 或容差，不用 ==",
    "求和用 math.fsum 避免累积误差（第653课）",
    "先缩小量级再运算，避免大数吃小数（catastrophic cancellation）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 用 struct 手工解析 float，写出 sign/exp/frac -> value 的还原公式。
# 2. 统计 0.0~1.0 之间可表示的双精度浮点数个数的量级。
# 3. 验证 float.hex()/fromhex() 往返对任意浮点都精确无损。
# 4. 思考：为什么「相邻间隔随量级增大」意味着绝对容差不能通用于所有量级？
