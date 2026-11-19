# ===== 第1001课：文件操作基础-综合案例-日志文件处理 =====
# 知识点：
#   - 写入日志文件：每条记录一行，用固定格式方便解析
#   - 读取日志：逐行解析、按级别过滤、统计
#   - 追加模式：多次运行程序时日志不丢失
#   - 实际场景：程序运行记录、错误追踪
# 依赖：无（标准库）
from datetime import datetime
import random

LOG_FILE = "app.log"


def write_log(level, message):
    """写入一条日志：时间 [级别] 消息"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{now} [{level}] {message}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


# 模拟程序运行产生日志
rng = random.Random(170)
print("== 模拟程序运行 ==")
operations = [
    ("INFO", "服务启动"),
    ("INFO", "数据库连接成功"),
    ("WARNING", "内存使用率较高"),
    ("INFO", "收到用户请求"),
    ("ERROR", "数据库查询失败"),
    ("INFO", "重试连接"),
    ("INFO", "数据库恢复"),
    ("WARNING", "磁盘空间不足"),
    ("INFO", "服务正常"),
]
for level, msg in operations:
    write_log(level, msg)
    print(f"  [{level}] {msg}")

print(f"\n日志已写入 {LOG_FILE}")

# 读取并分析日志
print("\n== 读取日志 ==")
with open(LOG_FILE, "r", encoding="utf-8") as f:
    all_lines = f.readlines()
print(f"  共 {len(all_lines)} 条日志")

# 按级别统计
print("\n== 级别统计 ==")
levels = {"INFO": 0, "WARNING": 0, "ERROR": 0}
for line in all_lines:
    for level in levels:
        if f"[{level}]" in line:
            levels[level] += 1
for level, count in levels.items():
    print(f"  {level}: {count} 条")

# 只显示 ERROR 和 WARNING
print("\n== 异常日志（ERROR + WARNING）==")
for line in all_lines:
    if "ERROR" in line or "WARNING" in line:
        print(f"  {line.strip()}")

# 按时间排序（日志本身就是按时间写入的，这里验证）
print("\n== 最新 3 条日志 ==")
for line in all_lines[-3:]:
    print(f"  {line.strip()}")

# ===== 练习题 =====
# 1. 写一个函数 log_info(message)，自动加时间戳写入日志文件。
# 2. 统计日志文件中 ERROR 出现的次数。
# 3. 只读取日志的最后 5 行（提示：readlines() 后取最后 5 个）。
# 4. 思考：为什么用 "a" 追加模式而不是 "w" 模式写日志？
