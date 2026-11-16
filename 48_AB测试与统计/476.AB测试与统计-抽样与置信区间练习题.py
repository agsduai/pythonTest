# ===== 第476课：AB测试与统计-抽样与置信区间 =====
# 知识点：
#   - 总体 vs 样本：我们只能看到样本，用样本推断总体
#   - 抽样误差：不同样本算出的均值会波动；样本越大波动越小
#   - 标准误 SE = 标准差 / √n
#   - 95% 置信区间 ≈ 均值 ± 1.96 × SE（大样本）；小样本用 t 分布
#   - Bootstrap：不依赖分布假设，重采样估计区间（A/B 分析常用）
#   - 置信区间的正确解读：重复抽样时，约 95% 的区间会包含真值
# 依赖：无（random / statistics / math）

import random
import statistics
from math import sqrt

random.seed(7)

# ---------------- 1. 模拟总体：10000 个用户的消费 ----------------
POPULATION = [random.gauss(200, 60) for _ in range(10_000)]
TRUE_MEAN = statistics.mean(POPULATION)
print(f"总体真值（均值）：{TRUE_MEAN:.2f} 元（现实中我们不知道它）")

# ---------------- 2. 抽样与标准误 ----------------
print("\n== 不同样本量的估计波动 ==")
for n in (30, 100, 500):
    means = []
    for _ in range(200):
        sample = random.sample(POPULATION, n)
        means.append(statistics.mean(sample))
    print(f"  n={n:3d}: 200 次抽样的均值范围 "
          f"[{min(means):.1f}, {max(means):.1f}]，标准差 {statistics.stdev(means):.2f}")

# ---------------- 3. 单次抽样的 95% 置信区间 ----------------
sample = random.sample(POPULATION, 100)
n = len(sample)
mean = statistics.mean(sample)
se = statistics.stdev(sample) / sqrt(n)
ci_low, ci_high = mean - 1.96 * se, mean + 1.96 * se
print(f"\n== 一次抽样（n={n}）==")
print(f"  样本均值：{mean:.2f} | 标准误：{se:.2f}")
print(f"  95% CI：[{ci_low:.2f}, {ci_high:.2f}]")
print(f"  真值是否落在区间内：{ci_low <= TRUE_MEAN <= ci_high}")

# ---------------- 4. Bootstrap 置信区间 ----------------
def bootstrap_ci(values, n_boot=2000, confidence=0.95):
    means = []
    n = len(values)
    for _ in range(n_boot):
        resample = [values[random.randrange(n)] for _ in range(n)]
        means.append(statistics.mean(resample))
    means.sort()
    alpha = (1 - confidence) / 2
    low = means[int(len(means) * alpha)]
    high = means[int(len(means) * (1 - alpha)) - 1]
    return low, high


low, high = bootstrap_ci(sample)
print("\n== Bootstrap 95% CI ==")
print(f"  [{low:.2f}, {high:.2f}]（不依赖正态假设）")

# ---------------- 5. 区间宽度与样本量 ----------------
print("\n== 样本量越大，区间越窄 ==")
for n in (30, 100, 400, 1600):
    sample = random.sample(POPULATION, n)
    m = statistics.mean(sample)
    se = statistics.stdev(sample) / sqrt(n)
    width = 2 * 1.96 * se
    print(f"  n={n:4d}: 均值 {m:6.2f}，95% CI 宽度 {width:5.2f}")

print("  经验：样本量翻 4 倍，区间宽度减半（√n 效应）")

# ---------------- 6. 覆盖率模拟：验证“95%”的含义 ----------------
print("\n== 覆盖率模拟（1000 次抽样）==")
covered = 0
for _ in range(1000):
    s = random.sample(POPULATION, 100)
    m = statistics.mean(s)
    se = statistics.stdev(s) / sqrt(len(s))
    if m - 1.96 * se <= TRUE_MEAN <= m + 1.96 * se:
        covered += 1
print(f"  区间包含真值的比例：{covered / 1000:.1%}（应接近 95%）")

# ---- 常见误区 ----
print("\n== 常见误区 ==")
for item in [
    "“真值有 95% 概率在区间内” —— 错，真值固定，区间随机",
    "“置信区间不重叠就一定显著” —— 不严谨，要做正式检验（第478课）",
    "小样本用 1.96 会低估不确定性 → 用 t 分布或 Bootstrap",
    "样本有偏（比如只统计活跃用户）时，再大的 n 也救不了",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把置信度改成 90%/99%，观察区间宽度变化。
# 2. 用 t 分布临界值（第478课实现）替代 1.96，对比小样本差异。
# 3. 模拟“有偏抽样”：只取总体中前 50% 的用户，看区间是否还覆盖真值。
# 4. 思考：A/B 实验为什么强调“随机分流”而不是“随便找人”？
