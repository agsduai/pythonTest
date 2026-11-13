# ===== 第032课：核心语法-流程控制语句-嵌套循环 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 嵌套循环：一个循环体内再写一个循环
#   - 外层循环执行一次，内层循环完整执行一遍
#   - 外层变量控制行，内层变量控制列
#   - 内层循环结束后通常用 print() 换行

# 示例一：打印 4 行 5 列星号
for row in range(4):
    for col in range(5):
        print("*", end="")
    print()  # 一行打印完，换行

# 示例二：直角三角形
for row in range(1, 6):
    for col in range(row):  # 第 row 行打印 row 个星号
        print("*", end="")
    print()

# 示例三：数字方阵
for row in range(1, 4):
    for col in range(1, 4):
        print(row * 10 + col, end=" ")
    print()

# 示例四：每行输出 1 到 3
for row in range(3):
    for col in range(1, 4):
        print(col, end=" ")
    print()

# ===== 练习题 =====
# 1. 用嵌套循环打印 5 行 5 列星号组成的正方形。
# 2. 用嵌套循环打印 5 行星号组成的直角三角形（第 1 行 1 个，第 5 行 5 个）。
# 3. 用嵌套循环打印 4 行，每行输出 1 2 3 4。
