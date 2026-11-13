# ===== 第322课：Numpy-综合案例-成绩矩阵统计 =====
# 知识点：
#   - 综合运用：随机数组（320）+ axis 统计（319）+ 布尔掩码（317）+ 广播（318）
#   - 场景：5 名学生 × 4 科目的成绩矩阵，产出一份完整分析
# 依赖：pip install numpy

import numpy as np

names = ["小明", "小红", "小刚", "小丽", "小强"]
subjects = ["语文", "数学", "英语", "物理"]

np.random.seed(7)
scores = np.random.randint(50, 101, size=(5, 4))     # 50~100 随机成绩
print("成绩矩阵（行=学生，列=科目）：\n", scores)

# ---- 分析1：各科平均分，哪科最难 ----
subject_avg = scores.mean(axis=0)
print("各科平均：", dict(zip(subjects, subject_avg.round(1))))
print("最难科目：", subjects[subject_avg.argmin()])

# ---- 分析2：总分排名 ----
totals = scores.sum(axis=1)
order = np.argsort(-totals)          # 降序：负号取反
print("总分排名：", [(names[i], int(totals[i])) for i in order])

# ---- 分析3：不及格清单 ----
bad = np.argwhere(scores < 60)       # 返回所有 (行, 列) 下标
print("不及格：", [(names[i], subjects[j], int(scores[i, j])) for i, j in bad])

# ---- 分析4：每人标准化后的“相对位置” ----
std_scores = (scores - scores.mean(axis=0)) / scores.std(axis=0)
for i, name in enumerate(names):
    best = subjects[std_scores[i].argmax()]
    print(f"  {name} 相对最强科目：{best}（z={std_scores[i].max():.2f}）")

# ===== 练习题 =====
# 1. 输出每名学生的“最高科目与分数”（axis=1 上 argmax）。
# 2. 给矩阵整体加“难度系数”向量（广播），重新排名。
# 3. 思考：如果学生数是 5 万，这份代码需要改动吗？
