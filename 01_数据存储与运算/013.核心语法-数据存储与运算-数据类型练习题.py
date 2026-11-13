# ===== 第013课：核心语法-数据存储与运算-数据类型 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 常用数据类型：int、float、str、bool、NoneType
#   - type() 查看数据的类型
#   - 类型转换：int()、float()、str()、bool()
#   - 不同类型不能直接运算，需要先转换

# 用 type() 查看数据的类型
print(type(100))        # <class 'int'> 整数
print(type(3.14))       # <class 'float'> 浮点数
print(type("hello"))    # <class 'str'> 字符串
print(type(True))       # <class 'bool'> 布尔值
print(type(None))       # <class 'NoneType'> 空值

# 整数和浮点数可以直接运算，结果是浮点数
print(10 + 3.5)
print(type(10 + 3.5))

# 浮点数转整数：int() 直接截断小数部分，不做四舍五入
print(int(3.9))
print(int(-3.9))

# 字符串转数字：字符串内容必须是合法的数字
print(int("123"))
print(float("3.14"))
# print(int("abc"))     # 会报错，字符串不是数字

# 数字转字符串
print(str(100))
print(type(str(100)))

# 转布尔值：0、0.0、""、None 转成 False，其余大多转成 True
print(bool(0))
print(bool(0.0))
print(bool(""))
print(bool("abc"))
print(bool(1))

# 类型不同不能直接运算，例如 "18" + 1 会报错，需要先转换
age_text = "18"
print(int(age_text) + 1)
print(age_text + "1")   # 字符串拼接

# ===== 练习题 =====
# 1. 分别定义整数、浮点数、字符串、布尔值、None 各一个，用 type() 输出它们的类型。
# 2. 把字符串 "3.14" 转成浮点数，再转成整数，输出两次结果并观察区别。
# 3. 把 100 转成字符串后用 + 拼接成 "100分" 并输出。
# 4. 用 bool() 测试 0、1、""、"0"、None，把结果写在注释里。
