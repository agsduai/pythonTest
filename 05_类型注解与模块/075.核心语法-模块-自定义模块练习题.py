# ===== 第075课：核心语法-模块-自定义模块 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 自己写的 .py 文件就是一个模块，放在同目录即可导入
#   - 模块中定义的函数、变量可以被其他文件复用
#   - __all__ 控制 from 模块 import * 时导出的名字
#   - if __name__ == "__main__": 中的代码只在直接运行时执行
#   - 模块的说明文档写在文件开头的三引号字符串中
# 配套模块：同目录下的 course075_myutils.py

import course075_myutils as tools
from course075_myutils import add, average, shout

print("模块说明：", tools.__doc__)
print("PI =", tools.PI)
print("add(3, 4) =", add(3, 4))
print("average([80, 90, 100]) =", average([80, 90, 100]))
print("shout('python') =", shout("python"))
print("模块文件：", tools.__file__)
print("模块名：", tools.__name__)
print("__all__ =", tools.__all__)

# 自定义模块和标准库模块的使用方式完全一样
import math
print("标准库平方根：", math.sqrt(49))

# ===== 练习题 =====
# 1. 从 course075_myutils 导入 square，计算 6 的平方并打印。
# 2. 用 from course075_myutils import * 导入后调用 shout("ok")，说明 __all__ 的作用。
# 3. 直接运行 course075_myutils.py，观察 __name__ == "__main__" 的自测输出。
