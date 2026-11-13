# ===== 第036课：核心语法-数据容器-概述 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 数据容器可以一次保存多个数据，用变量名统一管理
#   - Python 常见容器：列表 list、元组 tuple、字符串 str、集合 set、字典 dict
#   - 容器有有序/无序、可变/不可变的区别
#   - len() 获取元素个数，type() 查看容器类型
#   - 列表用 []、元组用 ()、集合和字典用 {}、字符串用引号定义

# 列表：有序、可变，元素之间用逗号分隔
scores = [90, 85, 78]
print(scores, type(scores), len(scores))

# 元组：有序、不可变
point = (3, 5)
print(point, type(point), len(point))

# 字符串：有序、不可变，每个字符都是一个元素
name = "Python"
print(name, type(name), len(name))

# 集合：无序、可变，会自动去掉重复元素
numbers = {1, 2, 2, 3}
print(numbers, type(numbers), len(numbers))

# 字典：保存键值对，通过键可以快速找到对应的值
student = {"name": "小明", "age": 18}
print(student, type(student), len(student))

# 同一个列表可以保存不同类型的数据
mixed = [1, "two", 3.0, True]
print(mixed, type(mixed), len(mixed))

# ===== 练习题 =====
# 1. 定义列表、元组、字符串各一个，分别打印内容、类型和长度。
# 2. 定义集合 {1, 2, 2, 3, 3, 3}，打印集合，观察重复元素是否保留，并打印长度。
# 3. 定义字典保存一本书的书名和价格，打印字典和长度，再分别取出书名和价格。
