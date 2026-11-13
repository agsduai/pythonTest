# ===== 第042课：核心语法-数据容器-列表list-案例3(推导式) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 列表推导式可以用一行代码快速生成列表
#   - 基本语法：[表达式 for 变量 in 可迭代对象]
#   - 带条件的推导式：[表达式 for 变量 in 可迭代对象 if 条件]
#   - 支持嵌套循环，按顺序生成所有组合
#   - 推导式会生成一个新列表，不会修改原列表

numbers = [1, 2, 3, 4, 5]

# 每个元素求平方，生成新列表
squares = [n * n for n in numbers]
print(squares)

# 只保留偶数，再求平方
even_squares = [n * n for n in numbers if n % 2 == 0]
print(even_squares)

# 用 range 生成 1 到 5 的立方
cubes = [n ** 3 for n in range(1, 6)]
print(cubes)

# 对字符串列表中的每个元素追加感叹号
words = ["apple", "banana", "pear"]
decorated = [word + "!" for word in words]
print(decorated)

# 统计每个单词的长度
lengths = [len(word) for word in words]
print(lengths)

# 只保留长度大于 5 的单词
long_words = [word for word in words if len(word) > 5]
print(long_words)

# 嵌套循环生成所有组合
pairs = [(x, y) for x in [1, 2] for y in [3, 4]]
print(pairs)

# 对价格列表打折，只处理 200 元以上的商品
prices = [99, 199, 299, 399]
discounted = [price * 0.8 for price in prices if price >= 200]
print(discounted)

# 只处理正数，并把它们翻倍
values = [3, -1, 0, -5, 8]
doubled = [value * 2 for value in values if value > 0]
print(doubled)

# ===== 练习题 =====
# 1. 用推导式生成 1 到 10 中所有奇数的平方。
# 2. 用推导式从 ["Python", "java", "C", "go"] 中筛选出长度大于 2 的单词。
# 3. 用推导式把 [12, 5, 8, 20, 3] 中的每个数乘以 10，并只保留结果大于 100 的项。
