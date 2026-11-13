# ===== 第012课：核心语法-数据存储与运算-变量案例(变量交换) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 变量交换：把两个变量保存的值互换
#   - 借助第三方变量 temp 完成交换
#   - Python 特有写法：a, b = b, a
#   - 交换的关键：先把其中一个值保存起来，再覆盖

# 场景：两个杯子，一个装可乐，一个装雪碧，如何互换
cup_a = "可乐"
cup_b = "雪碧"
print("交换前：", cup_a, cup_b)

# 方法一：借助第三方变量
temp = cup_a    # 先把 cup_a 的值备份到 temp
cup_a = cup_b   # 把 cup_b 的值赋给 cup_a
cup_b = temp    # 再把备份的值赋给 cup_b
print("交换后：", cup_a, cup_b)

# 方法二：Python 特有的写法，一行完成交换
left = 10
right = 20
print("交换前：", left, right)
left, right = right, left
print("交换后：", left, right)

# 如果不借助 temp，直接写 cup_a = cup_b 再 cup_b = cup_a 会怎样？
# 第一句执行后 cup_a 的“可乐”已经被覆盖，两个变量都会变成“雪碧”
# 所以交换时一定要先保存其中一个值

# 交换三个变量（轮换）：a 的值给 b，b 的值给 c，c 的值给 a
a = 1
b = 2
c = 3
print("轮换前：", a, b, c)
a, b, c = c, a, b
print("轮换后：", a, b, c)

# ===== 练习题 =====
# 1. 定义 x = 100、y = 200，使用第三方变量 temp 交换它们的值并输出。
# 2. 定义 name1 = "张三"、name2 = "李四"，使用 Python 的一行写法交换并输出。
# 3. 定义三个变量保存三门课的成绩，用一行代码完成循环交换后输出。
# 4. 思考题：为什么交换两个变量时不能直接写 a = b; b = a？把答案写在注释里。
