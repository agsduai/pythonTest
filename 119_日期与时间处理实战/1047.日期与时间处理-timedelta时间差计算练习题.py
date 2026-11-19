# ===== 第1047课：日期与时间处理-timedelta时间差计算 =====
# 知识点：
#   - timedelta(days=, hours=, minutes=)：表示"一段时间"，可与 datetime 加减
#   - 两个 datetime 相减直接得到 timedelta，用 .days / .total_seconds() 取值
#   - 实际场景：会员到期提醒、活动倒计时、订单超时判断
#   - timedelta 不支持"月"——月份长短不一，需要用 dateutil 或手动算

# 案例一：日期加减 —— 三天后到期
from datetime import datetime, timedelta

now = datetime(2024, 1, 15, 10, 0, 0)
deadline = now + timedelta(days=3)
print(f"现在：{now}")
print(f"三天后：{deadline}")  # 2024-01-18 10:00:00

# 案例二：算两个日期相差几天
# 场景：快递下单到签收用了几天
ordered = datetime(2024, 1, 10, 9, 30, 0)
received = datetime(2024, 1, 15, 14, 0, 0)
diff = received - ordered
print(f"运输时长：{diff.days} 天 {diff.seconds // 3600} 小时")
print(f"总秒数：{diff.total_seconds():.0f}")

# 案例三：倒计时
# 场景：秒杀活动 12 小时后开始
start = datetime(2024, 1, 15, 20, 0, 0)
remain = start - now
hours, mins = remain.seconds // 3600, remain.seconds % 3600 // 60
print(f"距离开始还有 {remain.days * 24 + hours} 小时 {mins} 分钟")

# 案例四：订单超时判断
# 场景：下单 30 分钟未支付自动取消
order_time = datetime(2024, 1, 15, 9, 0, 0)
pay_deadline = order_time + timedelta(minutes=30)
is_timeout = now > pay_deadline
print(f"支付截止：{pay_deadline}，当前已超时：{is_timeout}")

# 案例五：批量生成近 7 天日期
# 场景：统计最近一周每天销量
days = [(now - timedelta(days=i)).strftime("%m-%d") for i in range(7)]
print(f"近 7 天标签：{days}")  # 从今天往回排

# ===== 练习题 =====
# 1. 计算 2024-01-01 到 2024-03-01 相差多少天，打印结果 60。
# 2. 写函数 add_business_days(dt, n)：跳过周六周日往后推 n 个工作日（用 weekday() 判断），从周三推 3 个工作日应到下周一。
# 3. 会员到期日为 2024-02-01，用 now 与 timedelta 输出"还剩 X 天到期"（不足一天按小时算，输出保留 1 位小数的天数）。
