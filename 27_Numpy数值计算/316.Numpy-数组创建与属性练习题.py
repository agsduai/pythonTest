# ===== 第316课：Numpy-数组创建与属性 =====
# 知识点：
#   - ndarray：同构多维数组，数值计算的标准载体
#   - 创建：np.array / zeros / ones / full / arange / linspace
#   - 三大属性：shape 形状、dtype 元素类型、ndim 维度
#   - “同构”：混进字符串会全体转型 —— 这是与 list 的本质差异
# 依赖：pip install numpy

import numpy as np

# 从 list 创建
a = np.array([1, 2, 3, 4])
print(a, "| shape:", a.shape, "| dtype:", a.dtype, "| ndim:", a.ndim)

# 二维数组：1~12 摆成 3 行 4 列
m = np.arange(1, 13).reshape(3, 4)
print(m)
print("形状：", m.shape, "| 维度：", m.ndim, "| 元素总数：", m.size)

# 快捷创建
print(np.zeros((2, 3)))          # 全 0
print(np.ones(4, dtype=int))     # 全 1
print(np.full((2, 2), 7))        # 全 7
print(np.arange(0, 10, 3))       # 等差序列，类似 range
print(np.linspace(0, 1, 5))      # 等分 5 个点，含两端

# dtype 决定精度与内存
f = np.array([1, 2, 3], dtype=np.float64)
print(f, f.dtype, "每元素", f.itemsize, "字节")

# 同构的代价与好处：混型会转型，但换来紧凑内存和高速运算
print(np.array([1, 2, "3"]))     # 全变字符串

# ===== 练习题 =====
# 1. 创建 5×5 的“单位矩阵”（对角线为1）：提示 np.eye(5)。
# 2. 用 linspace 生成 0~100 的 11 个等分点。
# 3. 打印一个 (4, 3, 2) 全零数组的 shape 和 size，理解三维数组。
# 4. 思考：为什么 ndarray 要求“同构”？
