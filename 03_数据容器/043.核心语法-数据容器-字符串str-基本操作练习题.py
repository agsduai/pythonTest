# ===== 第043课：核心语法-数据容器-字符串str-基本操作 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 字符串是用引号定义的字符序列，属于数据容器
#   - 字符串是有序、不可变的，可以下标访问和切片
#   - 下标从 0 开始，-1 表示最后一个字符
#   - len() 可以获取字符串长度
#   - in / not in 判断子串是否存在于字符串中
#   - 字符串可以用 for 循环逐个取出字符

text = "Python"

# 正数下标和负数下标
print(text[0], text[-1])

# 字符串切片：左闭右开
print(text[1:4])
print(text[:3])
print(text[3:])
print(text[::-1])

# 字符串长度
print(len(text))

# 判断子串是否存在，区分大小写
print("Py" in text)
print("py" in text)
print("Java" not in text)

# 遍历字符串中的每一个字符
for ch in text:
    print(ch)

# 字符串拼接和重复
new_text = text + "!"
print(new_text)
print("-" * 20)

# 字符串不可变，下面这行会报错，所以注释掉
# text[0] = "J"

# 用循环统计字符 o 出现的次数
count = 0
for ch in "hello world":
    if ch == "o":
        count += 1
print("o 的个数：", count)

# ===== 练习题 =====
# 1. 对字符串 "abcdefg" 打印第 1 个、第 3 个和最后一个字符，并打印长度。
# 2. 从 "abcdefg" 中切片取出 "cde"，再把整个字符串倒序打印。
# 3. 判断 "Python" 中是否包含 "th"，并用循环统计 "good morning" 中字母 o 的个数。
