# ===== 第652课：数值计算与误差分析-Decimal与精确计算 =====
# 知识点：
#   - Decimal 用十进制表示，0.1 就是精确的 0.1，适合金额/税率/计量
#   - 必须从 str 或 int 构造：Decimal(0.1) 会把 float 的误差一起带进来
#   - 上下文 context：prec（有效位）、rounding（舍入模式）、Emin/Emax
#   - ROUND_HALF_EVEN 是银行家舍入（默认）；ROUND_HALF_UP 是常见四舍五入
#   - quantize 按指定小数位舍入；getcontext() 是线程局部，localcontext() 可临时改
#   - Fraction 表示精确有理数；Decimal 适合十进制有限小数，Fraction 适合任意分数
# 依赖：无（标准库）
from decimal import (Decimal, ROUND_CEILING, ROUND_DOWN, ROUND_FLOOR,
                     ROUND_HALF_EVEN, ROUND_HALF_UP, getcontext, localcontext)
from fractions import Fraction

print("== float vs Decimal 构造 ==")
print(f"  0.1 + 0.2 = {0.1 + 0.2!r}")
print(f"  Decimal(0.1)      = {Decimal(0.1)!r}  ← 把 float 误差带进来了")
print(f"  Decimal('0.1')    = {Decimal('0.1')!r}  ← 精确")
print(f"  Decimal('0.1')+Decimal('0.2') = {Decimal('0.1') + Decimal('0.2')!r}")
print(f"  等于 Decimal('0.3'): {Decimal('0.1') + Decimal('0.2') == Decimal('0.3')}")

print("\n== 精度上下文 prec ==")
print(f"  默认 prec = {getcontext().prec}")
print(f"  Decimal(1)/Decimal(7) = {Decimal(1) / Decimal(7)}")
with localcontext() as ctx:
    ctx.prec = 6
    print(f"  prec=6 -> {Decimal(1) / Decimal(7)}")
with localcontext() as ctx:
    ctx.prec = 40
    print(f"  prec=40 -> {Decimal(1) / Decimal(7)}")
print(f"  localcontext 退出后恢复: prec={getcontext().prec}")

print("\n== 舍入模式 ==")
value = Decimal("2.5")
for mode in (ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_DOWN, ROUND_CEILING, ROUND_FLOOR):
    print(f"  {mode:<18} 2.5 -> {value.quantize(Decimal('1'), rounding=mode)}  "
          f"3.5 -> {Decimal('3.5').quantize(Decimal('1'), rounding=mode)}")
print("  ROUND_HALF_EVEN：2.5->2, 3.5->4（向偶数靠，累计偏差最小）")

print("\n== quantize 与金额 ==")
price = Decimal("19.995")
qty = Decimal("3")
total = price * qty
print(f"  单价={price} 数量={qty} 未舍入合计={total}")
print(f"  保留 2 位(HALF_UP)  = {total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}")
print(f"  保留 2 位(HALF_EVEN)= {total.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)}")
try:
    total.quantize(Decimal("0.001"))
except Exception as e:
    print("  精度不足时:", type(e).__name__)

print("\n== 税率累加（避免 float 分币误差）==")
items = ["0.10"] * 10
float_sum = sum(0.10 for _ in range(10))
dec_sum = sum((Decimal(x) for x in items), Decimal("0"))
print(f"  float  : {float_sum!r}  == 1.0 ? {float_sum == 1.0}")
print(f"  Decimal: {dec_sum!r}  == 1.00 ? {dec_sum == Decimal('1.00')}")

print("\n== Fraction：任意精确分数 ==")
f = Fraction(1, 3) + Fraction(1, 6)
print(f"  1/3 + 1/6 = {f}（精确等于 1/2: {f == Fraction(1, 2)}）")
print(f"  Fraction(Decimal('0.1')) = {Fraction(Decimal('0.1'))}")
print(f"  float(Fraction(1,3))     = {float(Fraction(1, 3))!r}")
print("  Fraction 不适合开方/三角（结果常无理），Decimal 也不擅长")

print("\n== 三者对比 ==")
print(f"  {'类型':<10}{'表示':<14}{'速度':<8}{'适用'}")
for row in (("float", "二进制近似", "最快", "科学计算、图形、ML"),
            ("Decimal", "十进制精确", "较慢", "金额、税率、报表"),
            ("Fraction", "有理数精确", "最慢", "比例、符号推导")):
    print(f"  {row[0]:<10}{row[1]:<14}{row[2]:<8}{row[3]}")

print("\n== 序列化与边界（对接第643课）==")
import json
amount = Decimal("19.99")
print("  json 直接编 Decimal 会 TypeError，需转字符串:", end=" ")
try:
    json.dumps({"amount": amount})
except TypeError as e:
    print(type(e).__name__)
print("  正确做法:", json.dumps({"amount": str(amount)}))
print("  大数不丢精度:", Decimal("12345678901234567890.123456789") + 1)

print("\n== 工程要点 ==")
for line in [
    "全链路统一：数据库 DECIMAL、接口字符串、计算 Decimal，别中途转 float",
    "只在最终展示层 round，中间步骤保留足够精度",
    "prec 要覆盖最大数的整数位 + 小数位，别只设 2",
    "Decimal 与 float 混算会抛 TypeError，这是好事（强制显式）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 money_add(a, b, currency)，全程 Decimal 并校验两位小数。
# 2. 对比「先舍入再累加」与「累加后一次舍入」在 100 笔账目上的差额。
# 3. 用 localcontext 给单个函数临时设 prec=28，验证退出后全局不变。
# 4. 思考：为什么金额在 JSON 里用字符串传输，而不是 number？
