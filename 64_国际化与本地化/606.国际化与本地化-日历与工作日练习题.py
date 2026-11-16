# ===== 第606课：国际化与本地化-日历与工作日 =====
# 知识点：
#   - calendar：monthrange（月首星期+天数）、weekday、isleap、leapdays
#   - TextCalendar / HTMLCalendar 生成文本或 HTML 月历；setfirstweekday 调整周首
#   - 不同区域周首不同：中国/ISO 周一，美国周日，中东部分国家周六
#   - 工作日计算要同时排除「周末」与「节假日」，并支持调休补班
#   - 自定义节假日用 set[date] 存储，O(1) 查询；用迭代逐日推进
#   - 日历规则（如复活节、农历春节）需专门算法或数据表，别硬编码
# 依赖：无（标准库）
import calendar
from datetime import date, timedelta

print("== 基础日历信息 ==")
print("  2026 是闰年:", calendar.isleap(2026), "| 2028 是闰年:", calendar.isleap(2028))
print("  2000~2026 闰年数:", calendar.leapdays(2000, 2027))
print("  2026-11 的 (月首星期, 天数):", calendar.monthrange(2026, 11))
print("  2026-11-14 是星期几 (0=周一):", calendar.weekday(2026, 11, 14))
print("  星期名称:", list(calendar.day_name))
print("  月份名称:", list(calendar.month_name)[1:])

print("\n== 周首设置 ==")
for first in (calendar.MONDAY, calendar.SUNDAY):
    cal = calendar.TextCalendar(firstweekday=first)
    print(f"  周首={calendar.day_name[first]} 时 2026-11 首周: "
          f"{list(cal.itermonthdays(2026, 11))[:7]}")

print("\n== 中文月历（周一为首）==")
zh = calendar.TextCalendar(calendar.MONDAY)
print(zh.formatmonth(2026, 11, w=3))

print("\n== HTML 月历（片段）==")
html = calendar.HTMLCalendar(calendar.MONDAY).formatmonth(2026, 11)
print("  长度:", len(html), "字符；含 <table>:", "<table" in html)


class WorkCalendar:
    """带节假日与调休补班的工作日历。"""

    def __init__(self, weekend=(5, 6), holidays=None, makeup_days=None):
        self.weekend = set(weekend)
        self.holidays = set(holidays or ())
        self.makeup = set(makeup_days or ())

    def is_workday(self, d: date) -> bool:
        if d in self.makeup:
            return True
        if d in self.holidays:
            return False
        return d.weekday() not in self.weekend

    def add_workdays(self, start: date, n: int) -> date:
        """从 start 之后（不含 start）数 n 个工作日。"""
        d, counted = start, 0
        while counted < n:
            d += timedelta(days=1)
            if self.is_workday(d):
                counted += 1
        return d

    def workdays_between(self, start: date, end: date) -> int:
        return sum(self.is_workday(start + timedelta(days=i))
                   for i in range((end - start).days + 1))


# 2026 年国庆示例：10/1~10/7 放假，9/27 与 10/10 补班
holidays = {date(2026, 10, d) for d in range(1, 8)}
makeup = {date(2026, 9, 27), date(2026, 10, 10)}
wc = WorkCalendar(weekend=(5, 6), holidays=holidays, makeup_days=makeup)

print("\n== 中国式工作日历（含调休）==")
for d in (date(2026, 9, 27), date(2026, 10, 1), date(2026, 10, 8), date(2026, 10, 10)):
    print(f"  {d} 周{d.weekday()}: {'上班' if wc.is_workday(d) else '休息'}")

start = date(2026, 9, 30)
print(f"\n  从 {start} 起 3 个工作日后: {wc.add_workdays(start, 3)}")
print(f"  2026-10 全月工作日: {wc.workdays_between(date(2026, 10, 1), date(2026, 10, 31))} 天")

print("\n== 不同区域的周末定义 ==")
for region, weekend, first in (
    ("中国 / ISO", (5, 6), calendar.MONDAY),
    ("美国", (6,), calendar.SUNDAY),
    ("以色列", (4, 5), calendar.SUNDAY),
):
    cal = WorkCalendar(weekend=weekend)
    days = [d for d in (date(2026, 11, 14) + timedelta(days=i) for i in range(7))
            if cal.is_workday(d)]
    print(f"  {region:<10} 周末={weekend} 周首={calendar.day_name[first]} 工作日数={len(days)}")

print("\n== 儒略/复活节等需专用算法 ==")
print("  calendar 不提供农历/复活节；用数据表或 computus 算法单独实现")

# ===== 练习题 =====
# 1. 输出 2026 全年 12 个月的月历，并统计全年工作日总数。
# 2. 实现 next_workday(d)，返回 d 之后最近的第一个工作日。
# 3. 增加「每周三下午也休息」的半日规则，改造 is_workday 的返回值。
# 4. 思考：为什么调休补班用集合单独存，而不是从 weekend 里临时排除？
