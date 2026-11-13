# ===== 第227课：正则表达式-章综合案例-日志分析 =====
# 知识点：
#   - 综合运用：compile + 命名分组 + finditer + Counter 统计
#   - 场景：解析应用日志，统计各级别数量、找出耗时过高的请求
#   - 正则 + collections 是文本处理的黄金搭档

import re
from collections import Counter

LOG_TEXT = """2026-11-12 09:00:01 [INFO] 服务启动完成
2026-11-12 09:00:05 [INFO] GET /index 12ms
2026-11-12 09:00:09 [WARNING] GET /slow 890ms
2026-11-12 09:01:12 [ERROR] GET /api/pay 失败：超时 1500ms
2026-11-12 09:02:40 [INFO] GET /index 9ms
2026-11-12 09:03:15 [ERROR] GET /api/user 失败：数据库错误 200ms
"""

# 一行日志的解析模板：时间 + [级别] + 消息
LINE = re.compile(r"(?P<time>\S+ \S+) \[(?P<level>\w+)\] (?P<msg>.+)")

# 逐行解析并统计
level_counter = Counter()
slow_requests = []

for m in LINE.finditer(LOG_TEXT):
    level = m.group("level")
    level_counter[level] += 1

    # 从消息里抽取毫秒耗时
    cost = re.search(r"(\d+)ms", m.group("msg"))
    if level in ("WARNING", "ERROR") and cost and int(cost.group(1)) >= 500:
        slow_requests.append((m.group("msg"), int(cost.group(1))))

print("各级别日志数：", dict(level_counter))
print("慢请求（WARNING/ERROR 且 >=500ms）：")
for msg, ms in slow_requests:
    print(f"  {ms}ms ← {msg}")

# 提取访问过的接口路径并去重
paths = set(re.findall(r"GET (/[\w/]+)", LOG_TEXT))
print("访问过的接口：", sorted(paths))

# 把时间字段抽出来按行打印（练习 finditer + 命名分组）
for m in LINE.finditer(LOG_TEXT):
    print(m.group("time"), m.group("level"))

# ===== 练习题 =====
# 1. 统计每个接口被访问的次数（Counter + 提取路径）。
# 2. 把 ERROR 级别的日志单独整理成一份“错误报告”字符串。
# 3. 增加规则：同一分钟内出现 2 次以上 ERROR 则输出告警（提示：按分钟分组）。
# 4. 思考：如果日志是几 GB 的文件，这份代码怎么改成流式处理？（第191课）
