# ===== 第680课：随机模拟与蒙特卡洛-自助法与置信区间 =====
# 知识点：
#   - Bootstrap：从原样本有放回重抽 n 个，重复 B 次，用经验分布近似抽样分布
#   - 不需要知道总体分布，对中位数、分位数、相关系数等统计量尤其有用
#   - 百分位法置信区间：取 bootstrap 统计量的 2.5% / 97.5% 分位
#   - 标准误 SE = bootstrap 统计量的标准差；偏差 = mean(boot) - 原统计量
#   - 与解析法对比：均值可用 CLT 解析区间，中位数没有简单公式
#   - 注意：bootstrap 不能修复「样本本身有偏」或「样本量太小」的问题
# 依赖：无（标准库）
import math
import random
import statistics

DATA = [12.1, 11.8, 12.3, 12.0, 11.9, 12.2, 12.4, 11.7, 12.1, 11.95,
        12.6, 11.6, 12.05, 12.35, 11.85, 13.9]      # 含一个偏大的点

print("== 原始样本 ==")
print(f"  n={len(DATA)} 均值={statistics.fmean(DATA):.4f} "
      f"中位数={statistics.median(DATA):.4f} 标准差={statistics.stdev(DATA):.4f}")


def bootstrap(data, stat, B=5000, seed=0):
    r = random.Random(seed)
    n = len(data)
    vals = []
    for _ in range(B):
        sample = [data[r.randrange(n)] for _ in range(n)]   # 有放回
        vals.append(stat(sample))
    vals.sort()
    return vals


def ci_percentile(vals, alpha=0.05):
    lo = vals[int(len(vals) * alpha / 2)]
    hi = vals[int(len(vals) * (1 - alpha / 2))]
    return lo, hi


def summarize(name, stat, analytic=None):
    obs = stat(DATA)
    vals = bootstrap(DATA, stat, B=4000, seed=42)
    lo, hi = ci_percentile(vals)
    se = statistics.pstdev(vals)
    bias = statistics.fmean(vals) - obs
    print(f"  {name}")
    print(f"    观测值={obs:.4f}  bootstrap SE={se:.4f}  偏差={bias:+.4f}")
    print(f"    95% 百分位 CI = [{lo:.4f}, {hi:.4f}]  区间宽={hi-lo:.4f}")
    if analytic:
        print(f"    解析法 95% CI = [{analytic[0]:.4f}, {analytic[1]:.4f}]")


se_mean = statistics.stdev(DATA) / math.sqrt(len(DATA))
m = statistics.fmean(DATA)
print("\n== 均值的 bootstrap vs 解析（CLT） ==")
summarize("均值", statistics.fmean, (m - 1.96 * se_mean, m + 1.96 * se_mean))

print("\n== 中位数（没有简单解析式，bootstrap 正合适） ==")
summarize("中位数", statistics.median)

print("\n== 标准差 ==")
summarize("标准差", statistics.stdev)

print("\n== 90% 分位数 ==")
def q90(xs):
    s = sorted(xs)
    pos = (len(s) - 1) * 0.9
    lo, hi = int(pos), min(int(pos) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)
summarize("P90", q90)

print("\n== B 大小对区间稳定性的影响 ==")
for B in (200, 1000, 4000, 10000):
    vals = bootstrap(DATA, statistics.median, B=B, seed=7)
    lo, hi = ci_percentile(vals)
    print(f"  B={B:<6} CI=[{lo:.4f}, {hi:.4f}] 宽={hi-lo:.4f}")
print("  B 太小分位数抖动大；一般 2000~10000 够用")

print("\n== 有放回 vs 无放回 ==")
r = random.Random(1)
drawn = [DATA[r.randrange(len(DATA))] for _ in range(len(DATA))]
print("  一次重抽:", [round(x, 2) for x in drawn])
print("  重复值出现次数 > 0:", len(set(drawn)) < len(drawn))
print("  无放回抽 n 个就是原样本本身，无法产生新分布")

print("\n== 适用场景与限制 ==")
for line in [
    "  适合: 中位数/分位数/相关系数/复杂统计量，分布未知",
    "  不适合: 样本量极小（n<10）、强相关时间序列、极端分位数",
    "  时间序列要用 block bootstrap，保持局部相关性",
    "  CI 只是「抽样不确定性」，不含测量偏差与模型误差",
]:
    print("  -", line)

print("\n== 与参数法对比 ==")
print(f"  {'方法':<14}{'假设':<24}{'中位数 CI'}")
print(f"  {'bootstrap':<14}{'无需分布假设':<24}{'可直接给出'}")
print(f"  {'CLT':<14}{'需正态/大样本':<24}{'中位数无闭式解'}")

# ===== 练习题 =====
# 1. 实现 BCa 区间（偏差校正 + 加速），对比百分位法的覆盖度。
# 2. 用 bootstrap 估计两样本均值差的 CI，判断差异是否显著。
# 3. 对含强相关的数据做 block bootstrap，验证普通 bootstrap 低估 SE。
# 4. 思考：为什么 bootstrap 的 SE 会低估时间序列数据的真实不确定性？
