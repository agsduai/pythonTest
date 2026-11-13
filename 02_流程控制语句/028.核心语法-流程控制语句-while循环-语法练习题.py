# ===== 第028课：核心语法-流程控制语句-while循环-语法 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - while 循环的格式：while 条件:
#   - 条件为 True 时重复执行缩进代码块
#   - 循环体内要更新循环变量，否则可能死循环
#   - 循环条件最终要能变为 False，循环才会结束

# 示例一：输出 1 到 5
i = 1
while i <= 5:
    print(f"第 {i} 次循环")
    i += 1  # 循环变量递增，执行 5 次后条件为 False
print("循环结束")

# 示例二：求 1 到 100 的和
total = 0
num = 1
while num <= 100:
    total += num  # 累加
    num += 1
print(f"1 到 100 的和为：{total}")

# 示例三：倒计时
countdown = 3
while countdown > 0:
    print(f"倒计时：{countdown}")
    countdown -= 1
print("发射！")

# 示例四：循环条件一开始就不成立
n = 10
while n < 5:
    print("这一行不会执行")
    n += 1
print("while 循环结束")

# ===== 练习题 =====
# 1. 用 while 循环输出 1 到 10 的整数。
# 2. 用 while 循环求 1 到 100 之间所有偶数的和。
# 3. 用 while 循环求 5 的阶乘（1×2×3×4×5），并输出结果。
