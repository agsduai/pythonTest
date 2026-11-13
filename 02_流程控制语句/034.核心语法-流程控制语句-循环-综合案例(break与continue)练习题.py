# ===== 第034课：核心语法-流程控制语句-循环-综合案例(break与continue) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - break：立即结束整个循环
#   - continue：跳过本次循环剩余代码，直接进入下一次循环
#   - break/continue 通常与 if 搭配使用
#   - 在 while True 中常用 break 提供退出条件

# 示例一：break 提前结束 for 循环
for i in range(1, 11):
    if i == 5:
        break  # i 等于 5 时结束整个循环
    print(i)
print("示例一结束")

# 示例二：continue 跳过偶数
for i in range(1, 11):
    if i % 2 == 0:
        continue  # 偶数不打印，直接进入下一次循环
    print(i)
print("示例二结束")

# 示例三：找出 1 到 100 中第一个能被 7 整除的数
for i in range(1, 101):
    if i % 7 == 0:
        print(f"第一个能被 7 整除的数是：{i}")
        break  # 找到后立即结束循环

# 示例四：while 循环中用 break 结束
count = 1
while count <= 10:
    if count == 3:
        print("count 到 3 了，结束循环")
        break
    print(f"count = {count}")
    count += 1

# ===== 练习题 =====
# 1. 用 for 循环找出 1 到 100 中第一个能被 13 整除的数，找到后用 break 结束循环。
# 2. 用 for 循环和 continue 输出 1 到 20 中所有不能被 3 整除的数。
# 3. 用 while 循环模拟密码输入，最多尝试 3 次，输入正确密码 "8888" 时用 break 结束（运行后按提示输入）。
