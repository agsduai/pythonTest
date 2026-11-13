# ===== 第045课：核心语法-数据容器-字符串str-案例 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 综合使用字符串的大小写转换、查找、统计和拆分方法
#   - 使用 split() 把句子拆分成单词列表
#   - 使用循环遍历单词，求最长单词
#   - 使用切片 [::-1] 判断回文
#   - 使用 replace() 和 join() 完成字符串改写

sentence = "Python is easy and Python is powerful"
lower_sentence = sentence.lower()

print("原句：", sentence)
print("小写：", lower_sentence)
print("字符数：", len(sentence))
print("单词数：", len(sentence.split(" ")))
print("Python 出现次数：", lower_sentence.count("python"))

# 拆分出所有单词
words = sentence.split(" ")

# 找出最长的单词
longest = words[0]
for word in words:
    if len(word) > len(longest):
        longest = word
print("最长单词：", longest)

# 统计元音字母 a、e、i、o、u 的总个数
vowels = "aeiou"
vowel_count = 0
for ch in lower_sentence:
    if ch in vowels:
        vowel_count += 1
print("元音字母个数：", vowel_count)

# 判断回文：正着读和倒着读相同
line = "上海自来水来自海上"
if line == line[::-1]:
    print(line, "是回文")
else:
    print(line, "不是回文")

# 替换单词后重新输出
new_sentence = sentence.replace("Python", "Java")
print("替换后：", new_sentence)

# 用竖线连接所有单词
print("连接后：", "|".join(words))

# ===== 练习题 =====
# 1. 统计句子 "To be or not to be" 的单词数，以及单词 to 出现的次数（不区分大小写）。
# 2. 找出句子 "I love programming and learning" 中最长的单词。
# 3. 判断 "level" 和 "python" 是否为回文，并统计 "education" 中元音字母的个数。
