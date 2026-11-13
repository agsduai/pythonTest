# ===== 第060课：核心语法-函数基础-函数说明文档 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 文档字符串（docstring）写在函数体第一行，用三引号包裹
#   - 文档字符串用于说明函数的功能、参数和返回值
#   - 通过 函数名.__doc__ 或 help(函数名) 查看说明文档
#   - 良好的文档能让别人（也包括未来的自己）更快看懂函数

def circle_area(radius):
    """计算圆的面积。

    :param radius: 圆的半径
    :return: 圆的面积，保留两位小数
    """
    return round(3.14159 * radius ** 2, 2)

print("半径 2 的圆面积：", circle_area(2))
print("查看文档：")
print(circle_area.__doc__)

def print_student(name, age):
    """打印学生信息。

    :param name: 学生姓名
    :param age: 学生年龄
    :return: 无
    """
    print(f"姓名：{name}，年龄：{age}")

print_student("小明", 18)
print(print_student.__doc__)

# help(circle_area)  # 取消注释后运行，可以查看更完整的帮助信息

# ===== 练习题 =====
# 1. 为函数 rectangle_area(length, width) 编写说明文档，写明功能、参数和返回值。
# 2. 定义函数 bmi(weight, height) 计算 BMI，并用文档字符串说明参数含义。
# 3. 分别用 __doc__ 和 help() 查看上面两个函数的说明文档。
