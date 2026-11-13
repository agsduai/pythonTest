# ===== 第019课：核心语法-数据存储与运算-运算符-赋值运算符 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 赋值运算符：=、+=、-=、*=、/=、//=、%=、**=
#   - 复合赋值：先运算，再把结果赋回原变量
#   - Python 没有 ++ 和 --
#   - 多重赋值与同时赋值

# 基本赋值
num = 10
print(num)

# +=：累加，等价于 num = num + 5
num += 5
print(num)

# -=：累减
num -= 3
print(num)

# *=：累乘
num *= 2
print(num)

# /=：除法赋值，结果会变成浮点数
num /= 4
print(num)

# //=：整除赋值
num //= 2
print(num)

# %=：取余赋值
num %= 3
print(num)

# **=：幂赋值，等价于 num = num ** 2
num = 5
num **= 2
print(num)

# 字符串也可以使用 += 拼接
text = "Python"
text += " 学习"
print(text)

# 多重赋值：多个变量赋同一个值
x = y = z = 100
print(x, y, z)

# 同时赋值：一行给多个变量分别赋值
a, b = 1, 2
print(a, b)

# Python 没有 ++ 和 -- 运算符，下面写法是错误的
# num++
# num--

# ===== 练习题 =====
# 1. 定义 score = 80，依次执行 score += 10、score -= 5、score *= 2，输出每一步结果。
# 2. 定义 money = 1000，用 -= 扣掉 250，再输出剩余金额。
# 3. 定义 count = 7，用 //= 2、%= 2 依次运算并输出。
# 4. 用多重赋值让 a、b、c 都等于 0，再用同时赋值给它们分别赋 1、2、3。
