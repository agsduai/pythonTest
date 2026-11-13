# ===== 第068课：核心语法-函数进阶-匿名函数(lambda表达式) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - lambda 用于定义匿名函数，语法为 lambda 参数: 表达式
#   - 表达式的结果就是返回值，不需要写 return
#   - 适合逻辑简单、只用一次的小函数
#   - 常配合 sorted、filter 等函数使用

add = lambda a, b: a + b
print("两数之和：", add(3, 4))

square = lambda x: x ** 2
print("5 的平方：", square(5))

# 按元组的第二个元素排序
students = [("小明", 85), ("小红", 92), ("小刚", 78)]
students.sort(key=lambda item: item[1], reverse=True)
print("按成绩排序：", students)

# 过滤出偶数
numbers = [1, 2, 3, 4, 5, 6]
even_numbers = list(filter(lambda x: x % 2 == 0, numbers))
print("偶数：", even_numbers)

# lambda 也可以定义后立即调用
print("直接调用：", (lambda x, y: x * y)(3, 5))

# lambda 与普通函数对比：简单逻辑用 lambda 更简洁
def is_positive(x):
    return x > 0

positive_numbers = list(filter(lambda x: x > 0, [-2, 3, 0, 5]))
print("正数：", positive_numbers)

# ===== 练习题 =====
# 1. 用 lambda 定义求两个数较大值的函数，并调用输出 10 和 20 的结果。
# 2. 有一个字典列表，用 sorted 和 lambda 按年龄从小到大排序。
# 3. 用 filter 和 lambda 从列表中筛选出所有大于 60 的成绩。
