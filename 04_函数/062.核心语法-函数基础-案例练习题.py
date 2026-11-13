# ===== 第062课：核心语法-函数基础-案例 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 把案例拆成多个函数，一个函数只做一件事
#   - 函数之间通过参数传入数据、通过返回值传出结果
#   - 用 if/elif 根据运算符选择不同的计算函数
#   - 主流程函数负责组织调用，让代码结构更清晰

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return "除数不能为 0"
    return a / b

def calculator(a, operator, b):
    """简易计算器：根据运算符调用对应的函数。"""
    if operator == "+":
        return add(a, b)          # 函数内部嵌套调用
    elif operator == "-":
        return subtract(a, b)
    elif operator == "*":
        return multiply(a, b)
    elif operator == "/":
        return divide(a, b)
    return "不支持的运算符"

print("10 + 5 =", calculator(10, "+", 5))
print("10 - 5 =", calculator(10, "-", 5))
print("10 * 5 =", calculator(10, "*", 5))
print("10 / 5 =", calculator(10, "/", 5))
print("10 / 0 =", calculator(10, "/", 0))
print("10 % 5 =", calculator(10, "%", 5))

# ===== 练习题 =====
# 1. 定义 is_leap(year) 判断闰年，再定义 count_leap(years) 统计列表中闰年的个数。
# 2. 定义 bmi(weight, height) 计算 BMI，再定义 bmi_level(bmi_value) 返回胖瘦等级。
# 3. 定义 score_level(score) 返回“优秀/良好/及格/不及格”，并批量输出多个学生的等级。
