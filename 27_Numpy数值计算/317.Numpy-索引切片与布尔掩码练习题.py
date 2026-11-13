# ===== 第317课：Numpy-索引切片与布尔掩码 =====
# 知识点：
#   - 多维索引 m[行, 列]；切片 m[1:, :2]
#   - 布尔掩码：m[条件] 条件过滤，m[条件]=值 条件赋值（数据分析最常用）
#   - 花式索引：按下标列表批量取值
#   - np.where(条件, a, b)：向量化 if/else
#   - 切片是“视图”：改切片会改原数组，要独立请 .copy()
# 依赖：pip install numpy

import numpy as np

# 多维索引与切片
m = np.arange(1, 13).reshape(3, 4)
print(m)
print("m[1, 2] =", m[1, 2])        # 第1行第2列（从0数）
print("第0行：", m[0])
print("第1列：", m[:, 1])
print("子矩阵（行1起，列0~1）：\n", m[1:, :2])

# 布尔掩码
scores = np.array([88, 45, 92, 67, 73, 59])
print("掩码：", scores >= 60)
print("及格的分数：", scores[scores >= 60])
scores[scores < 60] = 0             # 不及格清零
print("处理后：", scores)

# 花式索引与 where
print("取第 0/2/4 个：", scores[[0, 2, 4]])
print(np.where(scores >= 90, "优秀", "继续努力"))

# 视图陷阱
view = m[0]
view[0] = 999
print("改了视图，原数组也变：", m[0])
m2 = np.arange(1, 13).reshape(3, 4)
copy_row = m2[0].copy()
copy_row[0] = -1
print("copy 后原数组不变：", m2[0])

# ===== 练习题 =====
# 1. 从成绩数组中取出“偶数下标且及格”的分数（两个条件用 & 连接，别忘括号）。
# 2. 把 3×4 矩阵的对角线元素全部改为 0（提示：m[i, i] 花式索引 m[range(3), range(3)]）。
# 3. 用 np.where 把分数映射为 及格/不及格 两档。
# 4. 思考：视图设计的好处是什么？（提示：切片零拷贝）
