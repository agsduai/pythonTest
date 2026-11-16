# ===== 第659课：模板引擎与文本生成-string.Template与format =====
# 知识点：
#   - string.Template：$var / ${var} 占位，substitute 严格、safe_substitute 宽容
#   - $$ 表示字面美元符号；标识符规则是 [A-Za-z_][A-Za-z0-9_]*
#   - str.format：{name} / {0} / {x:>10.2f}，格式规范走 __format__ 协议
#   - f-string 是编译期把表达式求值再 FORMAT_VALUE，功能最强但不能存成模板
#   - 三者选型：用户可编辑模板用 Template（最安全），代码内拼接用 f-string
#   - 关键差异：Template 只做「取值替换」，不执行任何表达式，天然防注入
# 依赖：无（标准库）
import string
from datetime import date

print("== string.Template 基础 ==")
tpl = string.Template("你好，$name！今天是 $date，余额 $$USD $amount。")
data = {"name": "小明", "date": "2026-11-14", "amount": "128.50"}
print("  substitute      :", tpl.substitute(data))
print("  带 ${} 消歧义  :", string.Template("${name}的订单").substitute(name="小明"))

print("\n== substitute vs safe_substitute ==")
t2 = string.Template("$a / $b / $c")
partial = {"a": 1, "b": 2}
try:
    t2.substitute(partial)
except KeyError as e:
    print("  substitute 缺 key 抛 KeyError:", e)
print("  safe_substitute 保留未提供的占位符:", t2.safe_substitute(partial))

print("\n== 标识符规则与 $$ 转义 ==")
for text in ("$x", "${x}", "$$x", "$1", "$x_y", "$x-y"):
    try:
        print(f"  {text!r:<10} -> {string.Template(text).substitute(x='OK', x_y='OK2')!r}")
    except (ValueError, KeyError) as e:
        print(f"  {text!r:<10} -> {type(e).__name__}: {e}")

print("\n== 自定义分隔符（继承 Template）==")
class PercentTemplate(string.Template):
    delimiter = "%"          # 把 $ 换成 %

print("  ", PercentTemplate("Hello %name, code=%code").substitute(name="Ann", code="A1"))

print("\n== str.format 与格式规范 ==")
row = {"name": "Python", "score": 95.678, "n": 7}
print("  位置/命名 :", "{0} 考了 {score} 分".format("小明", score=95))
print("  对齐精度 :", "|{name:<10}|{score:>8.2f}|{n:04d}|".format(**row))
print("  千分位   :", "{:,}".format(12345678))
print("  百分比   :", "{:.1%}".format(0.8765))
print("  日期     :", "{:%Y-%m-%d}".format(date(2026, 11, 14)))
print("  进制     :", "{:#x} {:#b} {:#o}".format(255, 10, 8))
print("  解包字典 :", "{name} = {score}".format(**row))

print("\n== __format__ 协议 ==")
class Money:
    def __init__(self, cents):
        self.cents = cents
    def __format__(self, spec):
        if spec == "cn":
            return f"¥{self.cents / 100:,.2f}"
        return format(self.cents / 100, spec or ".2f")

m = Money(1234567)
print(f"  {{:cn}} -> {m:cn}")
print(f"  {{:.2f}} -> {m:.2f}")

print("\n== f-string 的特点 ==")
name, n = "小明", 3
print("  编译期求值:", f"{name} 有 {n * 2} 本书")
print("  调试语法  :", f"{n=}")
print("  多行/表达式:", f"{sum(range(5))=}")
print("  注意：f-string 不能存成字符串再延迟渲染，模板必须写在源码里")

print("\n== 三者对比 ==")
print(f"  {'方式':<16}{'可执行表达式':<14}{'可外部提供':<12}{'适用场景'}")
for r in (("string.Template", "否", "是", "用户可编辑模板/邮件"),
          ("str.format", "仅格式规范", "是", "代码内格式串"),
          ("f-string", "是", "否", "代码内拼接，最直观")):
    print(f"  {r[0]:<16}{r[1]:<14}{r[2]:<12}{r[3]}")

print("\n== 安全边界 ==")
evil = "${__import__('os').getcwd()}"
print("  恶意模板:", evil)
print("  Template 只按标识符查字典，不会执行：", end=" ")
try:
    print(string.Template(evil).safe_substitute({}))
except Exception as e:
    print(type(e).__name__, e)
print("  反例：eval/exec 拼模板字符串等于把执行权交出去")

# ===== 练习题 =====
# 1. 实现 Template 子类，支持 $var 缺失时自动填 "<未知>" 而不报错。
# 2. 用 format_map 配合 defaultdict 实现「缺值留空」的宽松格式化。
# 3. 写一个 render(template, ctx, strict) 统一封装 substitute/safe_substitute。
# 4. 思考：为什么用户可编辑的模板不该用 f-string 或 eval 实现？
