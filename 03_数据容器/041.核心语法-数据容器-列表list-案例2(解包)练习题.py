# ===== 第041课：核心语法-数据容器-列表list-案例2(解包) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 解包：把容器中的元素依次赋值给多个变量
#   - 变量个数必须与元素个数一致，否则会报错
#   - 在变量名前加 * 可以收集剩余元素，结果是一个列表
#   - 列表、元组、字符串都支持解包
#   - 解包可以方便地交换两个变量的值

# 基本解包：三个元素对应三个变量
numbers = [10, 20, 30]
a, b, c = numbers
print(a, b, c)

# 星号解包：first 取第一个元素，rest 收集剩下的元素
first, *rest = [1, 2, 3, 4, 5]
print(first)
print(rest)

# 星号也可以放在前面，收集前面的元素
*others, last = [1, 2, 3, 4]
print(others)
print(last)

# 交换两个变量的值，不需要临时变量
x = 1
y = 2
x, y = y, x
print(x, y)

# 字符串也可以解包，每个字符对应一个变量
name = "Tom"
m, o, n = name
print(m, o, n)

# 嵌套解包：外层和内层同时解包
student = ["小明", [90, 85]]
student_name, (chinese, math_score) = student
print(student_name, chinese, math_score)

# 切分列表：把第一个元素和其余元素分开处理
data = [100, 200, 300, 400]
head, *body = data
print("第一个：", head)
print("其余：", body)

# ===== 练习题 =====
# 1. 把 [100, 200, 300] 解包到三个变量，并打印它们的和。
# 2. 把 [1, 2, 3, 4, 5, 6] 解包成 first、middle、last 三部分，打印三部分。
# 3. 定义两个变量 m=10、n=20，用解包交换它们的值后打印。
