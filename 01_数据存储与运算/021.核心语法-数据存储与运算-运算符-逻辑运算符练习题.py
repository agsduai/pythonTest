# ===== 第021课：核心语法-数据存储与运算-运算符-逻辑运算符 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 逻辑运算符：and、or、not
#   - and：两边都为 True 结果才是 True
#   - or：只要一边为 True 结果就是 True
#   - not：取反
#   - 短路运算与优先级：not > and > or

print(True and True)
print(True and False)
print(False and False)

print(True or False)
print(False or False)

print(not True)
print(not False)

# 用比较表达式组合条件
age = 25
print(age > 18 and age < 35)
print(age < 18 or age > 60)
print(not (age == 25))

# 短路运算：and 左边为 False 时，右边不再计算
print(False and 1 / 0)    # 输出 False，不会报错
# 短路运算：or 左边为 True 时，右边不再计算
print(True or 1 / 0)      # 输出 True，不会报错

# 逻辑运算符返回的不一定是布尔值
# and：左边为假就返回左边，否则返回右边
print(0 and 100)
print(5 and 100)
# or：左边为真就返回左边，否则返回右边
print("" or "默认值")
print("已填写" or "默认值")

# 非零数字、非空字符串都会被当作 True
print(not 0)
print(not 1)
print(not "")

# 优先级：not > and > or
print(True or False and False)    # 先算 and，结果为 True
print(not True and False)         # 先算 not，结果为 False

# ===== 练习题 =====
# 1. 定义 a = True、b = False，分别输出 a and b、a or b、not a、not b。
# 2. 定义年龄 age = 20，输出 age >= 18 and age <= 30 的结果。
# 3. 定义 username = ""，用 username or "游客" 输出默认用户名。
# 4. 判断表达式 True or False and False 的结果，并用括号改写验证。
