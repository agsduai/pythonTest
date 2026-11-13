# ===== 第073课：核心语法-模块-介绍 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 模块就是一个 .py 文件，里面可以放变量、函数和类
#   - 使用 import 模块名 导入模块，再用“模块名.成员”访问
#   - Python 自带很多标准库模块：math、random、datetime 等
#   - 模块第一次被导入时执行其顶层代码，之后重复导入不会重复执行
#   - __name__ 是模块的内置属性，直接运行文件时值为 "__main__"

import math
import random
import datetime

print("圆周率：", math.pi)
print("16 的平方根：", math.sqrt(16))
print("随机整数：", random.randint(1, 10))
print("今天的日期：", datetime.date.today())

# 模块名就是文件名（不含 .py）
print("math 模块名：", math.__name__)
print("当前模块名：", __name__)

# dir() 可以查看模块里有哪些名字
print("math 的部分成员：", dir(math)[:5])

# 用模块名调用函数，避免和内置函数重名
print("向上取整：", math.ceil(3.2))
print("向下取整：", math.floor(3.8))

# ===== 练习题 =====
# 1. 导入 math，计算半径为 3 的圆面积（π * r * r）。
# 2. 导入 random，随机生成 1~100 的整数并打印。
# 3. 导入 datetime，打印当前日期和年份，并解释 __name__ 的作用。
