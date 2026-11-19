# ===== 第1051课：日期与时间处理-综合案例-生日与倒计时工具 =====
# 知识点：
#   - 综合运用：now / strptime / timedelta / weekday / strftime
#   - 生日倒计时：算"今年生日还差几天"，过了就顺延到明年
#   - 年龄周岁：生日没过要减一岁（这是最常见的算错点）
#   - 工具函数化：每个功能一个小函数，主函数串起来

# 案例一：距离今年生日还有几天
from datetime import datetime, date, timedelta

def days_to_birthday(birth_md, today):
    """birth_md 形如 (5, 20)，返回今年生日还差几天（负数表示已过）。"""
    this_year = date(today.year, birth_md[0], birth_md[1])
    return (this_year - today).days

today = date(2024, 1, 15)
print(f"5月20日生日还差：{days_to_birthday((5, 20), today)} 天")
print(f"1月1日生日还差：{days_to_birthday((1, 1), today)} 天")  # 已过为负

# 案例二：生日倒计时（过了就顺延到明年）
def next_birthday_countdown(birth_md, today):
    """下一个生日还有几天，今年过了就算明年的。"""
    this_year = date(today.year, birth_md[0], birth_md[1])
    if this_year < today:
        this_year = date(today.year + 1, birth_md[0], birth_md[1])
    return (this_year - today).days, this_year

n, when = next_birthday_countdown((1, 1), today)
print(f"下一个生日：{when}（还有 {n} 天）")

# 案例三：精确周岁
def calc_age(birth_ymd, today):
    """严格周岁：生日没过要减 1。"""
    birth = date(*birth_ymd)
    age = today.year - birth.year
    if (today.month, today.day) < (birth.month, birth.day):
        age -= 1
    return age

print(f"2000-05-20 出生，2024-01-15 时 {calc_age((2000, 5, 20), today)} 岁")  # 23
print(f"1999-01-10 出生，2024-01-15 时 {calc_age((1999, 1, 10), today)} 岁")  # 25

# 案例四：会议提醒 —— 指定日期的星期与剩余天数
def meeting_reminder(meeting_str):
    """meeting_str 形如 '2024-02-01 14:00'。"""
    when = datetime.strptime(meeting_str, "%Y-%m-%d %H:%M")
    week_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    left = (when.date() - date.today()).days
    return f"会议 {when.strftime('%m月%d日 %H:%M')}（{week_cn[when.weekday()]}），还剩 {max(left, 0)} 天"

print(meeting_reminder("2024-02-01 14:00"))
print(meeting_reminder("2023-12-01 09:00"))  # 过去的会议显示 0 天

# 案例五：年底倒计时
new_year = date(today.year + 1, 1, 1)
left_days = (new_year - today).days
print(f"距离 {new_year.year} 年新年还有 {left_days} 天")

# ===== 练习题 =====
# 1. 写函数 countdown(target_str)：解析 "2024-12-31" 并打印"距离目标还有 N 天"，目标在过去则打印"目标已过期"。
# 2. 用 strptime + timedelta 实现"获取 30 天前那天的日期字符串（YYYY-MM-DD）"。
# 3. 综合小工具 birthday_card(name, birth_str)：解析生日 -> 算周岁 -> 算下一个生日倒计时 -> 打印一张"生日卡"文本，包含姓名、年龄、倒计时天数。
