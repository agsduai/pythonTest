# ===== 第1045课：日期与时间处理-strftime格式化输出 =====
# 知识点：
#   - strftime(格式)：把 datetime 对象变成指定样式的字符串
#   - 常用代码：%Y 四位年、%m 月、%d 日、%H 时、%M 分、%S 秒
#   - %m 自动补零：1 月输出 "01"；不补零可用 %-m（Linux）/ %#m（Windows）
#   - 实际场景：文件名带日期（备份_20240115.log）、报表标题

# 案例一：常用格式一览
from datetime import datetime

now = datetime.now()
print(f"标准日期：{now.strftime('%Y-%m-%d')}")
print(f"完整时刻：{now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"中文样式：{now.strftime('%Y年%m月%d日 %H时%M分')}")

# 案例二：生成带日期的文件名
# 场景：每天备份都要一个不重名的文件
backup_name = f"backup_{now.strftime('%Y%m%d')}.sql"
log_name = f"app_{now.strftime('%Y%m%d_%H%M')}.log"
print(f"备份文件：{backup_name}")
print(f"日志文件：{log_name}")

# 案例三：报表标题与月份标签
# 场景：月度账单标题
title = f"== {now.strftime('%Y 年 %m 月')} 账单 =="
print(title)
month_tags = [f"{2024}-{m:02d}" for m in range(1, 4)]  # 月份标签用 :02d 自己补零更稳
print(f"近三月标签：{month_tags}")

# 案例四：只显示时刻与星期
# 场景：网页顶栏的时间显示
print(f"短时刻：{now.strftime('%H:%M')}")
print(f"带秒：{now.strftime('%H:%M:%S')}")
print(f"星期几（英文）：{now.strftime('%A')}")
print(f"上/下午：{now.strftime('%p')}")

# ===== 练习题 =====
# 1. 把当前时间格式化为 "2024/01/15 08:30:45"（斜杠分隔）和 "20240115"（紧凑日期）两种。
# 2. 写函数 make_logname(prefix)：返回 f"{prefix}_YYYYMMDD_HHMMSS.log" 样式的文件名，调用一次打印结果。
# 3. 用 strftime 打印 "今天是星期X"（中文），weekday 映射用列表 ["一","二","三","四","五","六","日"] 自己完成。
