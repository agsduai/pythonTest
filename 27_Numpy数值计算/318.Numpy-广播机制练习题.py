# ===== 第318课：Numpy-广播机制 =====
# 知识点：
#   - 广播：形状不同的数组运算时自动“扩展对齐”，不用复制数据
#   - 规则：从右往左逐维对齐，两维相等、或有一方为 1（或缺失）即可
#   - 收益：少写循环、少占内存、代码更接近数学表达
# 依赖：pip install numpy

import numpy as np

# 标量广播
a = np.array([1, 2, 3])
print(a + 10)                        # 每个元素都加 10
print(a * np.array([10, 100, 1000]))

# (2,3) + (3,) → 行向量广播到每一行
m = np.arange(1, 7).reshape(2, 3)
print(m + np.array([100, 200, 300]))

# (2,1) + (2,3) → 列向量广播到每一列
print(m + np.array([[10], [20]]))

# 实战：按列标准化（减均值除标准差）—— 广播的经典应用
data = np.array([[90, 60], [80, 70], [70, 80]])
col_mean = data.mean(axis=0)
col_std = data.std(axis=0)
print("列均值：", col_mean)
print("标准化结果：\n", ((data - col_mean) / col_std).round(2))

# 形状不兼容：最后一维 3 vs 4 对不上 → 报错
try:
    m + np.arange(4)
except ValueError as exc:
    print("广播失败：", exc)

# ===== 练习题 =====
# 1. 用广播给矩阵每一行减去“该行的最大值”。
# 2. (3,1) + (1,4) 会得到什么形状？动手验证。
# 3. 思考：广播没有真的复制数据，那“看起来扩到每行”是怎么实现的？
