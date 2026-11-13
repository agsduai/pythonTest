# ===== 第319课：Numpy-常用统计函数 =====
# 知识点：
#   - 聚合：sum / mean / std / median / max / min / percentile
#   - axis 参数：axis=0 沿列压缩（每列得一个数），axis=1 沿行压缩
#   - argmax/argmin：最大/最小值的下标
#   - 布尔数组可求和：True 就是 1 —— 条件计数的惯用法
# 依赖：pip install numpy

import numpy as np

# 3 名学生 × 3 科目
scores = np.array([
    [92, 88, 95],      # 学生0
    [75, 95, 85],      # 学生1
    [58, 70, 64],      # 学生2
])
print(scores)

# 聚合与 axis
print("全体总分：", scores.sum())
print("每人总分（axis=1）：", scores.sum(axis=1))
print("每科平均（axis=0）：", scores.mean(axis=0).round(1))
print("每人最高分：", scores.max(axis=1))

# 位置信息
flat_max_idx = scores.argmax()
print("最高分：", scores.max(), "在第", flat_max_idx // 3, "行第", flat_max_idx % 3, "列")
print("每人最强科目编号：", scores.argmax(axis=1))

# 离散程度与分位数
print("标准差：", scores.std().round(2), "| 中位数：", np.median(scores))
print("75 分位数：", np.percentile(scores, 75))

# 条件计数：布尔求和
print("90+ 的科目数：", (scores > 90).sum())
print("每人 90+ 科目数：", (scores > 90).sum(axis=1))

# ===== 练习题 =====
# 1. 求每科“及格率”：(scores >= 60).mean(axis=0)。
# 2. 找出总分最高的学生编号（argsort 下一课细讲，先试 np.argmax(totals)）。
# 3. 思考：axis=0 是“跨行”还是“沿行方向压缩”？用自己的话描述一遍。
