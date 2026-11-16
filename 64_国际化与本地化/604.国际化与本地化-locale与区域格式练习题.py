# ===== 第604课：国际化与本地化-locale与区域格式 =====
# 知识点：
#   - locale 决定数字、货币、日期、排序的默认呈现（LC_NUMERIC / LC_TIME / LC_MONETARY）
#   - setlocale() 是进程级全局状态：多线程里不安全，且各系统地区名不统一
#   - Windows 名称如 "Chinese_China.936"，Linux 如 "zh_CN.UTF-8"，容易踩坑
#   - localeconv() 只读当前配置，不改全局状态，可安全观察
#   - 服务端更稳妥的做法：显式传入 region 规则表，而不是依赖进程 locale
#   - 本课用「规则表 + 显式格式化」实现可预测、可测试的区域格式
# 依赖：无（标准库）
import locale
from datetime import date

REGIONS = {
    "zh_CN": {"group": ",", "decimal": ".", "currency": "¥", "prefix": True,
              "date": "%Y年%m月%d日", "thousands": 3},
    "en_US": {"group": ",", "decimal": ".", "currency": "$", "prefix": True,
              "date": "%m/%d/%Y", "thousands": 3},
    "de_DE": {"group": ".", "decimal": ",", "currency": "€", "prefix": False,
              "date": "%d.%m.%Y", "thousands": 3},
    "fr_FR": {"group": " ", "decimal": ",", "currency": "€", "prefix": False,
              "date": "%d/%m/%Y", "thousands": 3},
    "en_IN": {"group": ",", "decimal": ".", "currency": "₹", "prefix": True,
              "date": "%d/%m/%Y", "thousands": 3},
}


def group_digits(int_part: str, sep: str, size: int = 3) -> str:
    """按区域规则插入千分位（每 size 位一组）。"""
    groups = []
    while len(int_part) > size:
        groups.append(int_part[-size:])
        int_part = int_part[:-size]
    groups.append(int_part)
    return sep.join(reversed(groups))


def format_number(value, region: str, digits: int = 2) -> str:
    rule = REGIONS[region]
    sign = "-" if value < 0 else ""
    text = f"{abs(value):.{digits}f}"
    int_part, frac = text.split(".")
    out = sign + group_digits(int_part, rule["group"]) + rule["decimal"] + frac
    return out


def format_currency(value, region: str) -> str:
    rule = REGIONS[region]
    num = format_number(abs(value), region)
    sign = "-" if value < 0 else ""
    body = (rule["currency"] + num) if rule["prefix"] else (num + " " + rule["currency"])
    return sign + body


def format_date(d: date, region: str) -> str:
    return d.strftime(REGIONS[region]["date"])


amount = 1234567.5
today = date(2026, 11, 14)
print("== 数字 / 货币 / 日期的区域差异 ==")
print(f"  {'region':<8}{'number':>18}{'currency':>20}  date")
for region in REGIONS:
    print(f"  {region:<8}{format_number(amount, region):>18}"
          f"{format_currency(amount, region):>20}  {format_date(today, region)}")

print("\n== 负数与印度分组（3-2-2）==")
def format_in_indian(value) -> str:
    """印度数字分组：最后 3 位一组，其余每 2 位一组。"""
    text = f"{abs(value):.2f}"
    int_part, frac = text.split(".")
    if len(int_part) > 3:
        head, tail = int_part[:-3], int_part[-3:]
        parts = []
        while len(head) > 2:
            parts.append(head[-2:])
            head = head[:-2]
        parts.append(head)
        int_part = ",".join(reversed(parts)) + "," + tail
    return ("-" if value < 0 else "") + int_part + "." + frac

print(f"  en_IN 普通 3 位分组 : {format_number(12345678.25, 'en_IN')}")
print(f"  en_IN 传统 3-2-2    : {format_in_indian(12345678.25)}")

print("\n== locale.localeconv()（只读当前环境）==")
conv = locale.localeconv()
for key in ("decimal_point", "thousands_sep", "currency_symbol", "frac_digits", "int_curr_symbol"):
    print(f"  {key:<18}: {conv.get(key)!r}")
print("  注意：这里没有调用 setlocale，因此显示的是进程默认值。")

print("\n== locale 辅助函数 ==")
print("  locale.atof('1,234.5') 需先 setlocale 才按区域解析；默认按 C：")
try:
    print("  ", locale.atof("1234.5"))
except ValueError as e:
    print("  解析失败:", e)

print("\n== 为什么服务端倾向显式 region ==")
for line in [
    "setlocale 是全局状态，多线程/协程间会互相干扰",
    "不同 OS 的地区名与可用 locale 不一致，CI 与生产可能不同",
    "Web 应用应按「每个请求的用户区域」格式化，而非按进程区域",
    "把 region 当参数传入，函数纯、可单测、可缓存",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 为 ja_JP 添加规则（无小数、日期 %Y/%m/%d、货币 ¥ 后置），并验证输出。
# 2. 实现 parse_number(text, region)，把 "1.234.567,89" 还原成 1234567.89。
# 3. 给 format_currency 增加「负数用括号」的会计格式选项（如 ($1,234.50)）。
# 4. 思考：为什么把 locale 作为函数参数比调用 setlocale 更适合 Web 服务？
