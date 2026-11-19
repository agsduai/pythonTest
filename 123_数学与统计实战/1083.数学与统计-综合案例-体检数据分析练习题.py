# ===== 第1083课：数学与统计-综合案例-体检数据分析 =====
# 知识点：
#   - 综合运用：math（BMI 计算）、statistics（均值/中位数/标准差）
#   - BMI = 体重 / 身高²，用范围判断健康等级
#   - 统计报告套路：逐条计算 -> 汇总统计 -> 分级统计 -> 结论
#   - 输出对齐的报表让数据一目了然

# 案例一：BMI 计算与分级
import math
import statistics

def bmi(weight_kg, height_m):
    return weight_kg / height_m ** 2

def bmi_level(value):
    if value < 18.5:
        return "偏瘦"
    if value < 24:
        return "正常"
    if value < 28:
        return "偏胖"
    return "肥胖"

w, h = 70, 1.75
value = bmi(w, h)
print(f"BMI = {value:.1f}，等级：{bmi_level(value)}")

# 案例二：全员体检数据
records = [
    ("小张", 70, 1.75), ("小李", 55, 1.62), ("小王", 85, 1.80),
    ("小赵", 48, 1.58), ("小周", 66, 1.70), ("小吴", 92, 1.78),
]
results = []
for name, weight, height in records:
    v = bmi(weight, height)
    results.append((name, round(v, 1), bmi_level(v), weight, height))
    print(f"{name}：BMI {v:.1f}（{bmi_level(v)}）")

# 案例三：汇总统计
bmi_values = [r[1] for r in results]
print("--- 汇总 ---")
print(f"平均 BMI：{statistics.mean(bmi_values):.1f}")
print(f"中位数 BMI：{statistics.median(bmi_values)}")
print(f"标准差：{statistics.stdev(bmi_values):.2f}")
print(f"最高：{max(bmi_values)}（{max(results, key=lambda r: r[1])[0]}）")
print(f"最低：{min(bmi_values)}（{min(results, key=lambda r: r[1])[0]}）")

# 案例四：分级统计 —— Counter
from collections import Counter
level_counter = Counter(r[2] for r in results)
print("--- 等级分布 ---")
for level, cnt in level_counter.most_common():
    print(f"{level}：{cnt} 人（{cnt / len(results):.0%}）")

# 案例五：健康建议
print("--- 建议 ---")
for name, v, level, weight, height in results:
    if level == "偏瘦":
        print(f"{name}：建议增重，目标 BMI 18.5~24（约需增重 {(18.5 * height * height - weight):.1f} 公斤）")
    elif level == "正常":
        print(f"{name}：保持现状")
    else:
        target_w = 23.9 * height ** 2
        print(f"{name}：建议减重，目标 {target_w:.1f} 公斤（约减 {weight - target_w:.1f} 公斤）")

# ===== 练习题 =====
# 1. 写函数 ideal_weight(height_m)：按 BMI=22 反推理想体重，打印身高 1.75 的理想体重（约 67.4 公斤）。
# 2. 给 records 增加身高体重的"标准差判断"：身高标准差小于 0.1 打印"身高整齐"，否则"身高差异大"。
# 3. 综合挑战：把体检数据写入列表套字典（name/weight/height/bmi/level），按 BMI 从高到低排序打印带排名的报表。
