# ===== 第986课：字符串处理实战-综合案例-文本分析 =====
# 知识点：
#   - split + len 统计单词数
#   - count 统计关键词出现次数
#   - startswith 过滤特定开头的行
#   - 组合使用：多个方法串联分析一段文本
#   - 实际场景：日志分析、文章统计

# 模拟一段服务器日志
log_text = """2024-01-15 08:00:01 INFO 服务启动成功
2024-01-15 08:00:05 INFO 数据库连接成功
2024-01-15 08:05:12 WARNING 内存使用率 85%
2024-01-15 08:10:00 INFO 收到请求 GET /api/users
2024-01-15 08:10:02 ERROR 数据库查询超时
2024-01-15 08:10:03 WARNING 重试连接
2024-01-15 08:15:00 INFO 收到请求 GET /api/orders
2024-01-15 08:20:01 ERROR 数据库连接失败
2024-01-15 08:20:05 INFO 服务关闭"""

print("== 原始日志 ==")
lines = log_text.split("\n")
for line in lines:
    print(f"  {line}")

# 统计各级别日志数量
print(f"\n== 日志级别统计 ==")
info_count = sum(1 for line in lines if " INFO " in line)
warn_count = sum(1 for line in lines if " WARNING " in line)
error_count = sum(1 for line in lines if " ERROR " in line)
print(f"  INFO: {info_count}, WARNING: {warn_count}, ERROR: {error_count}")

# 提取所有 ERROR 行
print(f"\n== ERROR 详情 ==")
for line in lines:
    if " ERROR " in line:
        print(f"  {line}")

# 提取时间戳
print(f"\n== 时间戳提取 ==")
for line in lines[:3]:
    timestamp = line.split(" ")[0] + " " + line.split(" ")[1]
    print(f"  {timestamp}")

# 统计每种事件类型的出现次数
print(f"\n== 事件关键词统计 ==")
keywords = ["启动", "数据库", "请求", "重试"]
for keyword in keywords:
    count = log_text.count(keyword)
    print(f"  {keyword}: 出现 {count} 次")

# 提取包含"数据库"的行
print(f"\n== 包含'数据库'的行 ==")
for line in lines:
    if "数据库" in line:
        print(f"  {line}")

# ===== 练习题 =====
# 1. 统计日志中包含 "GET" 的行数。
# 2. 提取所有 WARNING 行的时间戳（只输出时间部分）。
# 3. 统计所有行中最长的行有几个字符。
# 4. 思考：如果日志文件有 100 万行，上面的方法还有什么需要注意的？
