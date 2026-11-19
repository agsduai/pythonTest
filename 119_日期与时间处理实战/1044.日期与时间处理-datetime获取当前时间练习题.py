# ===== 第1044课：日期与时间处理-datetime获取当前时间 =====
# 知识点：
#   - from datetime import datetime：datetime.now() 拿到"年月日时分秒微秒"
#   - 对象属性直接取字段：now.year、now.month、now.day、now.hour ...
#   - datetime.now().date() 只要日期，.time() 只要时刻
#   - 实际场景：记录订单时间、打日志、显示"现在几点"

# 案例一：获取当前完整时间
from datetime import datetime

now = datetime.now()
print(f"当前时间：{now}")  # 例如 2024-01-15 08:30:45.123456
print(f"年：{now.year}，月：{now.month}，日：{now.day}")
print(f"时：{now.hour}，分：{now.minute}，秒：{now.second}")

# 案例二：订单时间戳记录
# 场景：下单时记录"什么时候下的单"
def place_order(goods_name):
    order_time = datetime.now()
    print(f"[{order_time}] 下单成功：{goods_name}")
    return order_time

t1 = place_order("苹果")
t2 = place_order("牛奶")
print(f"两单间隔微秒数：{t2.microsecond - t1.microsecond}")  # 同秒内也能区分先后

# 案例三：date 与 time 拆开用
# 场景：报表只要日期，日志只要时刻
today = datetime.now().date()
clock = datetime.now().time()
print(f"今天是：{today}")   # 只有 2024-01-15
print(f"此刻是：{clock}")   # 只有 08:30:45.xxxxxx

# 案例四：判断现在是上午还是下午
# 场景：商城问候语
hour = datetime.now().hour
if hour < 6:
    greet = "凌晨好"
elif hour < 12:
    greet = "上午好"
elif hour < 18:
    greet = "下午好"
else:
    greet = "晚上好"
print(f"{greet}！欢迎光临")

# ===== 练习题 =====
# 1. 打印当前的年、月、日、时、分，格式为"2024年01月15日 08时30分"（用 :02d 补零）。
# 2. 写函数 log(msg)：打印 "[HH:MM:SS] 消息内容"，用 datetime.now() 生成前缀，调用两次验证时间在变。
# 3. 用 now.month 写程序：3~5 月输出"春天"，6~8 月"夏天"，9~11 月"秋天"，12/1/2 月"冬天"。
