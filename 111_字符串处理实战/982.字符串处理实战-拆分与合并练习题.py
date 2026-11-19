# ===== 第982课：字符串处理实战-拆分与合并 =====
# 知识点：
#   - split() 按分隔符拆成列表；不传参数按空白字符拆
#   - join() 把列表合并为字符串，格式为 分隔符.join(列表)
#   - splitlines() 按换行符拆分；partition() 只拆第一次
#   - 实际场景：解析 CSV 行、拆分命令、合并文件路径
#   - split 和 join 是一对逆操作

# 案例一：解析 CSV 数据行
csv_line = "张三,25,男,北京"
fields = csv_line.split(",")
print(f"CSV 行: {csv_line}")
print(f"拆分后: {fields}")
print(f"姓名: {fields[0]}, 年龄: {fields[1]}, 城市: {fields[3]}")

# 案例二：合并列表为字符串
tags = ["Python", "编程", "学习"]
print(f"\n标签列表: {tags}")
print(f"用逗号合并: {', '.join(tags)}")
print(f"用竖线合并: {' | '.join(tags)}")
print(f"无分隔符合并: {''.join(tags)}")

# 案例三：拆分多行文本
log_text = "2024-01-15 INFO 启动\n2024-01-15 ERROR 数据库断开\n2024-01-15 INFO 恢复"
lines = log_text.split("\n")
print(f"\n日志行数: {len(lines)}")
for line in lines:
    print(f"  {line}")

# 案例四：split 不传参数（按空白拆，自动去多余空格）
messy = "  hello    world   python  "
print(f"\n messy = {messy!r}")
print(f"split() 按空白拆: {messy.split()}")
print(f"split(' ') 按单个空格拆: {messy.split(' ')}")
print("  不传参数会自动合并连续空格 —— 通常这是你想要的效果")

# 案例五：partition 只拆第一次
email = "user@example.com"
username, sep, domain = email.partition("@")
print(f"\n邮箱: {email}")
print(f"用户名: {username}, 分隔符: {sep}, 域名: {domain}")

# 案例六：split 和 join 组合使用
path_parts = ["home", "user", "documents", "report.pdf"]
full_path = "/".join(path_parts)
print(f"\n路径片段: {path_parts}")
print(f"拼接路径: {full_path}")
back_to_parts = full_path.split("/")
print(f"再拆回来: {back_to_parts}")
print(f"拆分合并互逆: {back_to_parts == path_parts}")

# ===== 练习题 =====
# 1. 把 "apple,banana,cherry" 拆成列表，再把列表用 " + " 合并回来。
# 2. 有一个句子 "I love Python"，拆成单词列表，统计单词数。
# 3. 把 ["2024", "01", "15"] 用 "-" 合并成日期字符串。
# 4. 思考：split(",") 和 split(", ", 1) 有什么区别？（提示：第二个参数
#    是最大拆分次数）
