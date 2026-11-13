# ===== 第015课：核心语法-数据存储与运算-字符串拼接 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 使用 + 拼接字符串
#   - 使用 * 重复字符串
#   - 字符串只能和字符串拼接，和数字拼接要先 str() 转换
#   - 相邻字符串字面量会自动拼接
#   - += 可以在原字符串后面追加内容

# 用 + 拼接两个字符串
first_name = "张"
last_name = "三"
full_name = first_name + last_name
print(full_name)

# 拼接多个字符串，可以连写多个 +
greeting = "你好，" + full_name + "！"
print(greeting)

# 字符串 * 整数：把字符串重复指定次数
print("=" * 30)
print("哈" * 3)
line = "-" * 10
print(line)

# 字符串和数字不能直接用 + 拼接，会报错
# print("我今年" + 18 + "岁")    # TypeError
# 正确做法：先用 str() 把数字转成字符串
age = 18
print("我今年" + str(age) + "岁")

# 相邻的两个字符串字面量会自动拼接成一个字符串
print("Hello" "World")

# += 拼接：把右边的字符串追加到左边变量后面
message = "Python"
message += " 很有趣"
message += "，我要坚持学习"
print(message)

# 拼接时注意空格，字符串里写什么就输出什么
print("Python" + "AI")
print("Python " + "AI")

# ===== 练习题 =====
# 1. 定义姓和名两个变量，用 + 拼接成完整姓名并输出。
# 2. 用 * 输出一条由 20 个 "*" 组成的分隔线。
# 3. 定义年龄变量 age = 18，用 + 和 str() 输出 "我今年18岁"。
# 4. 定义变量 s = "Py"，用 += 依次追加 "th"、"on"，最后输出 s。
