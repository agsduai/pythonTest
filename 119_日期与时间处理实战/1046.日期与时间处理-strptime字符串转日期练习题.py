# ===== 第1046课：日期与时间处理-strptime字符串转日期 =====
# 知识点：
#   - strptime(字符串, 格式)：把字符串解析成 datetime 对象，格式必须严格匹配
#   - 与 strftime 方向相反：strftime 是"对象->字符串"，strptime 是"字符串->对象"
#   - 解析失败会抛 ValueError，用户输入/文件数据必须用 try 包住
#   - 转成对象后才能做加减、比较等日期运算

# 案例一：解析标准日期字符串
from datetime import datetime

text = "2024-01-15"
d = datetime.strptime(text, "%Y-%m-%d")
print(f"解析结果：{d}")
print(f"取字段：{d.year} 年 {d.month} 月 {d.day} 日")

# 案例二：解析带时刻的字符串
# 场景：日志行里有 "2024-01-15 08:30:45"
log_time = datetime.strptime("2024-01-15 08:30:45", "%Y-%m-%d %H:%M:%S")
print(f"日志时刻：{log_time}")
slash_time = datetime.strptime("2024/01/15 8:30", "%Y/%m/%d %H:%M")  # 分隔符要一致
print(f"斜杠样式：{slash_time}")

# 案例三：解析失败的兜底
# 场景：用户手输生日，可能输错格式
for raw in ["2000-05-20", "2000年5月20日"]:
    try:
        birthday = datetime.strptime(raw, "%Y-%m-%d")
        print(f"'{raw}' 解析成功：{birthday.date()}")
    except ValueError as e:
        print(f"'{raw}' 解析失败：{e}")  # 格式不匹配直接报错

# 案例四：解析后做运算 —— 算年龄
# 场景：根据生日算周岁
def calc_age(birthday_text, today):
    birth = datetime.strptime(birthday_text, "%Y-%m-%d")
    age = today.year - birth.year
    # 今年生日还没过，减 1 岁
    if (today.month, today.day) < (birth.month, birth.day):
        age -= 1
    return age

today = datetime(2024, 1, 15)
print(f"2000-05-20 出生的年龄：{calc_age('2000-05-20', today)}")  # 23，生日没到
print(f"1999-01-01 出生的年龄：{calc_age('1999-01-01', today)}")  # 25，生日已过

# ===== 练习题 =====
# 1. 把 "2024-06-01"、"2024/06/01"、"20240601" 三种字符串分别用 strptime 解析成功并打印。
# 2. 写函数 parse_safe(text)：能解析 "%Y-%m-%d" 返回 datetime，失败返回 None 并打印原因，用 "2024-02-30" 测试（2 月没有 30 号）。
# 3. 解析两个时刻 "2024-01-15 08:00" 和 "2024-01-15 10:30"，打印它们相差多少分钟（配合 timedelta，下一课详讲，先试着输出 150）。
