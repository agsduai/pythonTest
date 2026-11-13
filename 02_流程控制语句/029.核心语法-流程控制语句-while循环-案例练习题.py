# ===== 第029课：核心语法-流程控制语句-while循环-案例 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 用 while 解决“次数未知、条件满足就继续”的问题
#   - 循环变量既可以是整数，也可以是金额、高度等数据
#   - 在循环体内累计结果、统计次数
#   - 注意浮点数计算与格式化输出

# 案例一：存款翻倍
money = 10000
years = 0
while money < 20000:
    money = money * 1.05  # 每年增长 5%
    years += 1
print(f"{years} 年后存款达到 {money:.2f} 元")

# 案例二：折纸超过珠穆朗玛峰
thickness = 0.1
count = 0
while thickness < 8848:
    thickness *= 2  # 每对折一次厚度翻倍
    count += 1
print(f"对折 {count} 次后高度为 {thickness:.2f} 米")

# 案例三：统计整数位数
number = 12345
digits = 0
while number > 0:
    number //= 10  # 去掉最低位
    digits += 1
print(f"原数字共有 {digits} 位")

# 案例四：计算 1 到 10 中所有奇数的和
total = 0
n = 1
while n <= 10:
    if n % 2 == 1:
        total += n
    n += 1
print(f"1 到 10 的奇数和为：{total}")

# ===== 练习题 =====
# 1. 本金 5000 元，年利率 3%，用 while 计算多少年后本金超过 8000 元（不考虑取整）。
# 2. 一张纸厚 0.1 毫米，每对折一次厚度翻倍，用 while 求对折多少次后超过 10 米。
# 3. 用 while 循环求 123456 的各位数字之和（提示：% 10 取个位，// 10 去掉个位）。
