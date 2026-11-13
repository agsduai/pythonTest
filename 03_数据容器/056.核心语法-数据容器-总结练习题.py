# ===== 第056课：核心语法-数据容器-总结 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 列表、字符串、元组、集合、字典的对比
#   - 根据“是否可变、是否有序、能否去重、是否按键访问”选择容器
#   - 综合小自测：去重、统计、解包、字典计数

# ---------- 知识对比表 ----------
# 容器    定义方式          可变  有序  元素可重复  访问方式      典型用途
# list    [1, 2, 3]         是    是    是          下标          有序、可修改的一组数据
# tuple   (1, 2, 3)         否    是    是          下标          不希望被修改的固定数据
# str     "abc"             否    是    是          下标          文本处理
# set     {1, 2, 3} / set() 是    否    否          不能下标      去重、集合运算
# dict    {"a": 1}          是    是*   键不能重复  按键           键值映射、结构化数据
# 注：字典按插入顺序保存键值对（Python 3.7+），但访问元素主要靠键而不是下标。

# ---------- 小自测脚本 ----------
# 1. 列表：保存原始数据
words = ["apple", "banana", "apple", "orange", "banana", "apple"]

# 2. 集合：去重
unique_words = set(words)
print("不同单词：", unique_words, "个数：", len(unique_words))

# 3. 字典：统计每个单词出现的次数
counter = {}
for word in words:
    if word in counter:
        counter[word] += 1
    else:
        counter[word] = 1
print("单词计数：", counter)

# 4. 元组：保存固定数据并解包
student = ("小明", 95)
name, score = student
print("学生：", name, "成绩：", score)

# 5. 字符串：常用方法
text = "  Python is fun  "
print("去空格：", text.strip())
print("转大写：", text.strip().upper())

# 6. 列表推导式：筛选及格成绩
scores = [88, 95, 72, 60, 45]
passed = [s for s in scores if s >= 60]
print("及格成绩：", passed)

# 7. 综合：找出出现次数最多的单词
max_word = ""
max_count = 0
for word, count in counter.items():
    if count > max_count:
        max_word = word
        max_count = count
print("出现最多的单词：", max_word, max_count)

# ===== 练习题 =====
# 1. 用 print() 输出一句话，说明列表、元组、集合、字典最主要的区别。
# 2. 列表 data = [3, 1, 3, 2, 1, 4]，用集合去重并排序，打印结果。
# 3. 字符串 s = "a b a c b a"，用字典统计每个字符出现的次数，并打印出现次数最多的字符。
