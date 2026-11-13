# ===== 第031课：核心语法-流程控制语句-for循环-案例(range) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - range(stop)：从 0 开始，到 stop 结束，不含 stop
#   - range(start, stop)：从 start 到 stop，不含 stop
#   - range(start, stop, step)：按步长生成整数
#   - 步长为负数时可以倒序生成

# 示例一：range(5)
for i in range(5):
    print(i, end=" ")
print()  # 输出：0 1 2 3 4

# 示例二：range(2, 7)
for i in range(2, 7):
    print(i, end=" ")
print()  # 输出：2 3 4 5 6

# 示例三：range(1, 10, 2)
for i in range(1, 10, 2):
    print(i, end=" ")
print()  # 输出：1 3 5 7 9

# 示例四：range(5, 0, -1)
for i in range(5, 0, -1):
    print(i, end=" ")
print()  # 输出：5 4 3 2 1

# 应用：求 1 到 100 的偶数和
total = 0
for i in range(2, 101, 2):
    total += i
print(f"1 到 100 的偶数和为：{total}")

# ===== 练习题 =====
# 1. 用 range 求 1 到 100 的奇数和。
# 2. 用 range 输出 1 到 100 中所有 7 的倍数，每行输出一个。
# 3. 用 range 倒序输出 10 到 1，再输出 1 到 10 的乘积。
