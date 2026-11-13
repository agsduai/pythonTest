# ===== 第010课：核心语法-数据存储与运算-变量 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 变量：给数据起个名字，方便保存和重复使用
#   - 定义格式：变量名 = 值（= 是赋值，不是数学里的等于）
#   - 变量可以重新赋值，新值会覆盖旧值
#   - 变量必须先赋值后使用，变量名区分大小写

# 定义一个整数变量，等号右边是值，左边是变量名
age = 18
print(age)

# 定义一个字符串变量
name = "小明"
print(name)

# 用变量参与运算，变量名就代表它保存的值
price = 9.9
count = 3
print(price * count)

# 变量重新赋值：后面的值会覆盖前面的值
score = 60
print("第一次成绩：", score)
score = 95
print("修改后成绩：", score)

# 变量名区分大小写，Name 和 name 是两个不同的变量
Name = "小红"
print(name)
print(Name)

# 把已有变量的值赋给另一个变量
a = 100
b = a
print("a =", a)
print("b =", b)

# 可以先分别定义多个变量，再一起使用
city = "北京"
weather = "晴"
temperature = 26
print(city, weather, temperature)

# 注意：变量必须先赋值再使用，下面这行会报错，仅作说明
# print(total)

# ===== 练习题 =====
# 1. 定义变量保存你的姓名、年龄、城市，并用 print() 分三行输出。
# 2. 定义商品单价 price 和数量 count，计算总价并输出。
# 3. 定义变量 score = 60，输出后再把 score 改成 95，再次输出，观察覆盖效果。
# 4. 定义 a = 1、b = 2，先让 b = a，再让 a = 100，输出 a 和 b，思考 b 为什么不是 100。
