# ===== 第1050课：日期与时间处理-replace与date常用方法 =====
# 知识点：
#   - replace(字段=值)：不改原对象，返回改了字段的新 datetime（不可变思想）
#   - date 对象常用：.replace()、.toordinal()、date.today()
#   - isoformat() 输出标准 "YYYY-MM-DD" 格式，接口传输首选
#   - 构造指定日期：datetime(2024, 1, 15, 8, 30)，不用非得是"今天"

# 案例一：replace 修正字段
from datetime import datetime, date

now = datetime(2024, 1, 15, 14, 30, 45)
at_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
print(f"原始：{now}")
print(f"当天零点：{at_midnight}")  # 用于"按天"统计

# 案例二：构造指定日期做测试
# 场景：单元测试要固定的"假今天"，不能依赖真实时间
pay_day = datetime(2024, 2, 10, 9, 0, 0)
print(f"固定测试日期：{pay_day.date()}")

# 案例三：isoformat 标准输出
# 场景：写入 JSON / 调接口，日期统一用 ISO 格式
d = date(2024, 1, 15)
print(f"isoformat：{d.isoformat()}")  # 2024-01-15
print(f"带时刻：{now.isoformat()}")   # 2024-01-15T14:30:45

# 案例四：日期归一化 —— 去掉时刻只留天
# 场景：订单列表按"天"分组
orders = [
    datetime(2024, 1, 15, 9, 0),
    datetime(2024, 1, 15, 18, 30),
    datetime(2024, 1, 16, 8, 0),
]
by_day = {}
for o in orders:
    key = o.replace(hour=0, minute=0, second=0, microsecond=0)
    by_day.setdefault(key, []).append(o.strftime("%H:%M"))
for day, times in sorted(by_day.items()):
    print(f"{day.date()}：{times}")

# 案例五：date.today 与字符串三兄弟对比
# date 对象也有 strftime / replace
today = date.today()
print(f"今天：{today}，月底：{today.replace(day=28)}")  # 简化版月底
print(f"今年第一天：{today.replace(month=1, day=1)}")

# ===== 练习题 =====
# 1. 用 replace 把 datetime(2024, 6, 15, 18, 45) 分别变成"当天 08:00:00"和"当月 1 号"，打印两个结果。
# 2. 写函数 month_start(dt)：返回传入时刻所在月 1 号零点，用 datetime(2024, 3, 5, 10, 0) 测试。
# 3. 把 [datetime(2024,1,15,8,0), datetime(2024,2,20,9,30)] 用 isoformat 转成标准字符串列表并打印。
