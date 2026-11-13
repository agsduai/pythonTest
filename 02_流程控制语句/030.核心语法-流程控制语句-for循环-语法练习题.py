# ===== 第030课：核心语法-流程控制语句-for循环-语法 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - for 循环的格式：for 变量 in 可迭代对象:
#   - for 循环会自动把每个元素依次赋给变量
#   - range() 用来生成整数序列
#   - 循环体通过缩进表示，循环次数由序列长度决定

# 示例一：循环 5 次
for i in range(5):
    print(f"第 {i + 1} 次循环，i = {i}")

# 示例二：遍历字符串中的每个字符
for char in "Python":
    print(char)

# 示例三：求 1 到 100 的和
total = 0
for num in range(1, 101):
    total += num
print(f"1 到 100 的和为：{total}")

# 示例四：循环输出 5 个星号
for i in range(5):
    print("*", end="")
print()  # 换行

# 示例五：for 循环结束后，循环变量保留最后一次的值
for i in range(3):
    print(f"循环中：{i}")
print(f"循环结束后 i = {i}")

# ===== 练习题 =====
# 1. 用 for 循环输出 1 到 10 的整数。
# 2. 用 for 循环遍历字符串 "hello"，每行输出一个字符。
# 3. 用 for 循环求 1 到 50 所有整数的和并输出。
