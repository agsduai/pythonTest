# ===== 第230课：常用标准库-datetime与time =====
# 知识点：
#   - datetime.now() 取当前时间；strftime 格式化输出；strptime 解析字符串
#   - timedelta：时间加减（天/周/时/分/秒）
#   - date 只管日期；weekday() 返回 0=周一
#   - time.perf_counter 高精度计时；time.sleep 暂停

from datetime import datetime, date, timedelta
import time

# 当前时间与格式化
now = datetime.now()
print(now.strftime("%Y-%m-%d %H:%M:%S"))
print(now.year, now.month, now.day, now.hour)

# 常用格式符号：%Y 年 %m 月 %d 日 %H 时 %M 分 %S 秒
print(now.strftime("%Y年%m月%d日 %H点%M分"))

# 字符串 → 时间对象
d = datetime.strptime("2026-11-12", "%Y-%m-%d")
print(d, type(d).__name__)

# 构造指定时间
meeting = datetime(2026, 11, 20, 9, 30)
print("距离目标还有", meeting - now)

# timedelta：时间运算
print("明天：", (now + timedelta(days=1)).strftime("%m-%d"))
print("一周前：", (now - timedelta(weeks=1)).strftime("%m-%d"))
print((timedelta(days=2) - timedelta(days=1)).seconds, "秒")

# 只处理日期
today = date.today()
print(today, "星期", today.weekday() + 1)      # 0=周一，+1 更符合习惯

# time 模块：计时与暂停
start = time.perf_counter()
time.sleep(0.2)
print(f"耗时 {time.perf_counter() - start:.3f} 秒")
print("当前时刻：", time.strftime("%H:%M:%S"))

# ===== 练习题 =====
# 1. 输出“今天是一年中的第几天”（提示：%j）。
# 2. 编写函数 days_until(target)：计算距离某个日期还有几天。
# 3. 把 "2026/11/12 08:30" 用 strptime 解析成 datetime。
# 4. 思考：strftime 和 strptime 的方向怎么记？
