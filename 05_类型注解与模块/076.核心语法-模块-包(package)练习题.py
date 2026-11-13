# ===== 第076课：核心语法-模块-包(package) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 包是存放多个模块的文件夹，目录中通常有 __init__.py
#   - __init__.py 在包被导入时执行，可用来初始化或导出常用成员
#   - from 包 import 模块 / from 包.模块 import 函数
#   - 包让代码按功能分目录管理，避免模块名冲突
#   - 包内模块可用相对导入：from .模块 import 成员
# 配套包：同目录下的 course076_tools/

import course076_tools
from course076_tools import math_tools
from course076_tools.text_tools import shout
from course076_tools import average

print("包名：", course076_tools.__name__)
print("包路径：", course076_tools.__file__)
print("两数之和：", course076_tools.add(10, 20))
print("平均数：", math_tools.average([80, 90, 100]))
print("平均分：", average([70, 85, 95]))
print("喊话：", shout("hello python"))
print("包导出的名字：", course076_tools.__all__)

# 也可以用 import 包.模块 as 别名
import course076_tools.math_tools as mt
print("和的平方：", mt.add(1, 2) ** 2)

# ===== 练习题 =====
# 1. 导入包中的 average，计算 [60, 75, 90] 的平均分。
# 2. 使用 from course076_tools import *，调用 shout("ok") 并说明 __all__。
# 3. 解释 __init__.py 的作用，并打印包和子模块的 __file__。
