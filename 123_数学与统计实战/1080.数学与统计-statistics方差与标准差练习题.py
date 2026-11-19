# ===== 第1080课：数学与统计-statistics方差与标准差 =====
# 知识点：
#   - stdev 标准差：衡量数据"波动大小"，越大越分散
#   - variance 方差 = 标准差的平方；pstdev/pvariance 是"全体数据"版本
#   - 标准差与均值配合看：波动/均值 = 变异程度
#   - 实际场景：两班成绩谁更稳定、机器误差是否超标、投资波动

# 案例一：标准差直观理解
import statistics

stable = [88, 89, 90, 91, 92]      # 都在 90 附近
volatile = [60, 75, 90, 105, 120]  # 起伏大
for name, d in [("稳定组", stable), ("波动组", volatile)]:
    print(f"{name}：均值 {statistics.mean(d)}，标准差 {statistics.stdev(d):.2f}")
print("均值相同，标准差大的更分散")

# 案例二：两班成绩稳定性对比
# 场景：平均分接近，看谁的发挥更稳
class_a = [85, 87, 86, 88, 84]
class_b = [90, 70, 95, 65, 80]
for name, d in [("甲班", class_a), ("乙班", class_b)]:
    print(f"{name}：平均 {statistics.mean(d):.1f} 分，标准差 {statistics.stdev(d):.2f}")
print("甲班标准差小，成绩更稳定")

# 案例三：variance 与 stdev 的关系
d = [2, 4, 6, 8, 10]
v = statistics.variance(d)
s = statistics.stdev(d)
print(f"方差 {v:.2f}，标准差 {s:.2f}")
print(f"验证 sqrt(方差) == 标准差：{abs(v ** 0.5 - s) < 1e-9}")

# 案例四：样本与总体的区别
# stdev（样本，除以 n-1）比 pstdev（总体，除以 n）略大
print(f"样本标准差 stdev：{statistics.stdev(d):.4f}")
print(f"总体标准差 pstdev：{statistics.pstdev(d):.4f}")
print("全班成绩用 pstdev，抽样调查用 stdev")

# 案例五：质量抽检 —— 误差是否超标
# 场景：零件标准长度 50mm，抽检 5 件
target, limit = 50, 2.0
samples = [49.8, 50.2, 50.1, 49.9, 50.0]
std = statistics.stdev(samples)
mean = statistics.mean(samples)
print(f"均值 {mean:.2f}mm，标准差 {std:.3f}mm")
print(f"质量判定：{'合格' if std <= limit else '超标'}（阈值 {limit}mm）")

# ===== 练习题 =====
# 1. 计算 [10, 12, 14, 16, 18] 的方差和标准差，验证方差 == 标准差 ** 2。
# 2. 两位射手成绩：甲 [9, 9, 10, 8, 9]、乙 [10, 6, 10, 7, 9]，用 stdev 判断谁更稳定并打印结论。
# 3. 写函数 quality_check(samples, target, limit)：均值与目标偏差和标准差都达标返回 "合格"，否则 "不合格"，用两组数据测试。
