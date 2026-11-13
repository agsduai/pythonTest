# ===== 第044课：核心语法-数据容器-字符串str-常用方法 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - strip() 去掉字符串两端的空白字符
#   - lower() 转小写、upper() 转大写
#   - find() 查找子串下标，找不到返回 -1
#   - replace() 替换子串，count() 统计子串出现次数
#   - split() 按分隔符拆分字符串，join() 把多个字符串连接起来
#   - startswith()、endswith()、isdigit() 用于判断

text = "  Hello Python World  "

# 去掉两端空格
print(text.strip())

# 大小写转换
print(text.lower())
print(text.upper())

# 查找子串，找不到时返回 -1
print(text.find("Python"))
print(text.find("Java"))

# 统计和替换
print(text.count("o"))
print(text.replace("Python", "AI"))

# 判断开头和结尾
print(text.startswith("  He"))
print(text.endswith("  "))

# split：按逗号拆分成列表
fruits = "apple,banana,orange".split(",")
print(fruits)
print(len(fruits))

# join：用短横线把列表中的字符串连接起来
result = "-".join(fruits)
print(result)

# 判断字符串是否全部由数字组成
print("12345".isdigit())
print("12a45".isdigit())

# 综合：清理用户输入并统一大小写
raw = "  PyThOn  "
clean = raw.strip().lower()
print(clean)

# ===== 练习题 =====
# 1. 对 "  Data Science  " 去掉两端空格，再转换为大写并打印。
# 2. 把 "red,green,blue" 按逗号拆分成列表，再用 "/" 连接成一个新字符串。
# 3. 判断 "2026" 是否全部为数字，并统计 "banana" 中 "na" 出现的次数。
