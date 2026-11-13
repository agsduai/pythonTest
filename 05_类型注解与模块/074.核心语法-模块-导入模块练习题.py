# ===== 第074课：核心语法-模块-导入模块 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - import 模块名：导入整个模块，用“模块名.成员”访问
#   - import 模块名 as 别名：给模块起短名字
#   - from 模块名 import 成员：只导入指定成员，可直接使用
#   - from 模块名 import 成员 as 别名：给成员起别名
#   - 不推荐 from 模块名 import *，容易造成名字冲突
#   - 导入模块时，Python 会先在当前目录、再在标准库路径中查找

import math
import random as rd
from datetime import date
from math import sqrt, pi

print("平方根：", math.sqrt(81))
print("随机骰子：", rd.randint(1, 6))
print("今天：", date.today())
print("直接使用 sqrt：", sqrt(25))
print("直接使用 pi：", pi)

# 同一个模块用不同方式导入，指向的是同一个模块对象
import math as m2
print("模块对象相同：", math is m2)

# 别名可以避免与变量同名
from random import choice as random_choice
print("随机选择：", random_choice(["石头", "剪刀", "布"]))

# 导入多个成员时用逗号分隔
from math import ceil, floor
print("取整：", ceil(2.1), floor(2.9))

# ===== 练习题 =====
# 1. 用 import statistics as st 的方式导入统计模块，求平均分。
# 2. 用 from math import ceil, floor 导入并比较 3.2 的上取整和下取整。
# 3. 用 from random import choice 随机抽取一个学生姓名并打印。
