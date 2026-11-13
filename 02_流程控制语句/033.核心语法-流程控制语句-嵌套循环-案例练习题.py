# ===== 第033课：核心语法-流程控制语句-嵌套循环-案例 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 用嵌套循环解决图形与表格类问题
#   - 内层循环的范围可以依赖外层循环变量
#   - 外层控制行数，内层控制每行的内容
#   - f-string 与 end="\t" 可以对齐输出

# 案例一：九九乘法表
for i in range(1, 10):
    for j in range(1, i + 1):
        print(f"{j}*{i}={i * j}", end="\t")
    print()  # 每行结束换行

# 案例二：倒直角三角形
for i in range(5, 0, -1):
    for j in range(i):
        print("*", end="")
    print()

# 案例三：金字塔
rows = 5
for i in range(1, rows + 1):
    for space in range(rows - i):  # 先打印空格
        print(" ", end="")
    for star in range(2 * i - 1):  # 再打印星号
        print("*", end="")
    print()

# 案例四：输出 3 行乘法口诀的前两列
for i in range(1, 4):
    for j in range(1, 3):
        print(f"{j}*{i}={i * j}", end=" ")
    print()

# ===== 练习题 =====
# 1. 打印完整的九九乘法表（下三角）。
# 2. 打印 5 行倒直角三角形（第 1 行 5 个星号，最后一行 1 个）。
# 3. 打印 4 行数字金字塔：第 1 行 1，第 2 行 12，第 3 行 123，第 4 行 1234（每行前面补空格）。
