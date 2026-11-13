# ===== 第280课：实用脚本-定时执行 =====
# 知识点：
#   - 最简调度：while + sleep；按“下次执行时间”判断是否到点
#   - 每日任务防重复：记住“上次执行日期”
#   - 生产建议：系统级调度（Windows 任务计划 / cron）比脚本内循环更可靠

import time
from datetime import datetime, timedelta


def job(name):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 执行任务：{name}")


# ---- 方式一：固定间隔循环 ----
def run_every(func, interval, times):
    for _ in range(times):
        time.sleep(interval)
        func("每 0.3 秒一次的任务")


run_every(job, 0.3, 3)

# ---- 方式二：每日一次（防止同一天重复执行） ----
last_run_date = None
for _ in range(3):
    time.sleep(0.1)
    today = datetime.now().date()
    if last_run_date != today:            # 模拟“新的一天”
        job("每日早报")
        last_run_date = today
    else:
        print("  今天已执行过，跳过")

# ---- 方式三：下次执行时间点（到点才跑，不占空转） ----
next_time = datetime.now() + timedelta(seconds=0.5)
for _ in range(2):
    wait = (next_time - datetime.now()).total_seconds()
    if wait > 0:
        time.sleep(wait)
    job("到点触发的任务")
    next_time = datetime.now() + timedelta(seconds=0.5)

# ---- 生产环境怎么做 ----
#   Windows：任务计划程序（可以设“每天 9 点运行 python 脚本”）
#   Linux/Mac：cron（crontab -e 添加一行）
#   程序内的 while+sleep 适合轻量场景；系统重启、脚本崩溃它管不了

# ===== 练习题 =====
# 1. 写一个“每天 9 点提醒喝水”的程序：结合方式二，比较当前时间是否过 9 点。
# 2. 给 run_every 加最大执行时长参数，超时自动停止。
# 3. 思考：如果脚本在 23:59 启动，跨天逻辑要注意什么？
