# ===== 第051课：核心语法-数据容器-集合set-案例 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 列表去重：list(set(列表))
#   - 交集：共同好友 / 共同选修课
#   - 差集：只在一个集合中出现的元素
#   - 并集：把两组数据合并去重
#   - 集合元素无序，需要顺序时转成列表再排序

# ---------- 示例代码：社团选课统计 ----------
# 1. 列表去重
nums = [1, 2, 2, 3, 3, 3, 4]
unique_nums = list(set(nums))      # 先转集合去重，再转回列表
unique_nums.sort()                 # 排序，让结果有顺序
print("去重后：", unique_nums)

# 2. 两个社团的成员名单
python_club = {"小明", "小红", "小刚", "小美"}
ai_club = {"小红", "小刚", "小强"}

# 3. 交集：两个社团都参加的人
both = python_club & ai_club
print("两个社团都参加：", both)

# 4. 差集：只参加 Python 社团的人
only_python = python_club - ai_club
print("只参加Python社团：", only_python)

# 5. 并集：所有参加过社团的人（自动去重）
all_members = python_club | ai_club
print("所有社团成员：", all_members)

# 6. 对称差集：只参加了一个社团的人
only_one = python_club ^ ai_club
print("只参加一个社团：", only_one)

# 7. 统计字符串中出现了哪些不同的字符
text = "hello world"
letters = set(text.replace(" ", ""))   # 去掉空格后转集合
print("不同字符：", letters)
print("不同字符个数：", len(letters))

# ===== 练习题 =====
# 1. 列表 words = ["a", "b", "a", "c", "b", "a"]，用集合去重并打印去重后的列表（按字母顺序）。
# 2. 集合 A = {1, 2, 3, 4, 5}、B = {4, 5, 6, 7}，求两个集合的交集、只在 A 中出现的元素、所有元素。
# 3. 字符串 s = "banana"，统计其中出现了哪些不同的字符，并打印不同字符的个数。
