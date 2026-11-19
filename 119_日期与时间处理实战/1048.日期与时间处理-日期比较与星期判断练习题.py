# ===== 第1048课：日期与时间处理-日期比较与星期判断 =====
# 知识点：
#   - datetime/date 对象可直接用 > < == 比较，先后顺序一目了然
#   - weekday() 返回 0~6（周一到周日），isoweekday() 返回 1~7
#   - 周末判断：weekday() >= 5（周六 5、周日 6）
#   - 实际场景：判断是否工作日、活动是否过期、排班表

# 案例一：日期先后比较
from datetime import datetime, date, timedelta

d1 = date(2024, 1, 15)
d2 = date(2024, 2, 1)
print(f"1月15日 早于 2月1日：{d1 < d2}")
print(f"两个日期相等：{d1 == d2}")

# 带时刻的比较：先到先得
t_a = datetime(2024, 1, 15, 8, 30)
t_b = datetime(2024, 1, 15, 9, 0)
first = min(t_a, t_b)
print(f"先发生的：{first}")

# 案例二：星期几
# 场景：判断某天是星期几并输出中文
week_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
d = date(2024, 1, 15)
print(f"2024-01-15 是：{week_cn[d.weekday()]}")

# 案例三：周末判断
# 场景：周末不配送
def can_deliver(d):
    if d.weekday() >= 5:
        return f"{d} 是 {week_cn[d.weekday()]}，周末不配送"
    return f"{d} 是 {week_cn[d.weekday()]}，可以配送"

for day in [date(2024, 1, 15), date(2024, 1, 20), date(2024, 1, 21)]:
    print(can_deliver(day))

# 案例四：活动是否在有效期内
# 场景：优惠券 start <= 今天 <= end 才能用
start = date(2024, 1, 1)
end = date(2024, 1, 31)
today = date(2024, 1, 15)
if start <= today <= end:
    print("优惠券可用")
else:
    print("不在有效期内")

# 案例五：找出本月所有周日
# 场景：每周日大扫除提醒
sundays = []
d = date(2024, 1, 1)
while d.month == 1:
    if d.weekday() == 6:
        sundays.append(d.strftime("%m-%d"))
    d += timedelta(days=1)  # timedelta 表示"一天"，下一课详讲
print(f"2024 年 1 月的周日：{sundays}")

# ===== 练习题 =====
# 1. 判断今天是否周末（用 date.today()），输出"今天是周末"或"今天是工作日"。
# 2. 写函数 is_same_day(t1, t2)：两个 datetime 只比年月日不比时刻，8:30 和 9:00 同一天应返回 True。
# 3. 给定日期列表 [date(2024,1,15), date(2024,1,20), date(2024,1,21)]，用列表推导式筛选出所有周六周日并打印中文星期。
