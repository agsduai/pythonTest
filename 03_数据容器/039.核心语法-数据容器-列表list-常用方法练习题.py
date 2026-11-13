# ===== 第039课：核心语法-数据容器-列表list-常用方法 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - append() 在列表末尾追加一个元素
#   - extend() 把另一个列表中的元素依次追加到末尾
#   - insert() 在指定下标位置插入元素
#   - remove() 删除指定的元素，pop() 删除并返回指定下标的元素
#   - sort() 排序、reverse() 反转、clear() 清空列表
#   - index() 查找下标、count() 统计出现次数

numbers = [3, 1, 2]

# append：在末尾追加一个元素
numbers.append(4)
print(numbers)

# extend：把另一个列表的元素逐个追加进来
numbers.extend([5, 6])
print(numbers)

# insert：在下标 1 的位置插入 100
numbers.insert(1, 100)
print(numbers)

# remove：删除指定的元素 100
numbers.remove(100)
print(numbers)

# pop：删除末尾元素，并把被删除的元素返回
last = numbers.pop()
print(last, numbers)

# sort：把列表从小到大排序
numbers.sort()
print(numbers)

# reverse：把列表反转
numbers.reverse()
print(numbers)

# index：查找元素第一次出现的下标
print(numbers.index(3))

# count：统计元素出现的次数
print(numbers.count(2))

# clear：清空列表
numbers.clear()
print(numbers)

# 再练习 count 和 index：统计名字出现次数并查找下标
names = ["小明", "小红", "小明"]
print(names.count("小明"))
print(names.index("小红"))

# ===== 练习题 =====
# 1. 创建购物车 ["苹果", "香蕉"]，追加 "橙子"，再在开头插入 "牛奶"，最后打印购物车。
# 2. 对成绩列表 [78, 92, 65, 92, 88] 统计 92 出现的次数和第一次出现的下标。
# 3. 对成绩列表排序后反转，打印结果；再删除 65，最后打印列表长度。
