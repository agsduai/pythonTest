# ===== 第046课：核心语法-数据容器-元组tuple-基本操作 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 元组用 () 定义，元素之间用英文逗号分隔
#   - 元组是有序的，可以通过下标和切片访问元素
#   - 元组是不可变的，定义后不能修改、添加或删除元素
#   - 只有一个元素的元组必须写成 (元素,)，逗号不能省略
#   - count() 统计元素次数，index() 查找元素下标
#   - len()、in、for 循环同样适用于元组

point = (3, 5)
print(point)
print(point[0], point[-1])
print(point[:1])
print(len(point))
print(3 in point)

# 单元素元组：必须保留逗号
single = (5,)
print(single, type(single))

# 不加逗号只是带括号的整数
not_tuple = (5)
print(not_tuple, type(not_tuple))

# 元组中可以有重复元素
colors = ("red", "green", "blue", "red")
print(colors.count("red"))
print(colors.index("green"))
print(colors[1:3])
print(colors[::-1])
print("blue" in colors)

# 元组不可变，下面这行会报错，所以注释掉
# colors[0] = "yellow"

# 嵌套元组
students = (("小明", 18), ("小红", 17))
print(students[0])
print(students[0][0])
print(students[1][1])

# 遍历元组
for color in colors:
    print(color)

# 空元组
empty = ()
print(empty, len(empty))

# ===== 练习题 =====
# 1. 定义元组 (10, 20, 30)，打印第一个和最后一个元素，再切片取出 (20, 30)。
# 2. 定义只有一个元素 100 的元组，打印它的内容和类型，并打印长度。
# 3. 定义 ("张三", 90, "李四", 85, 90)，统计 90 的次数和第一次出现的下标。
