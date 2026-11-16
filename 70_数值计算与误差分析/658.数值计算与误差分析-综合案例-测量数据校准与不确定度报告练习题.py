# ===== 第658课：数值计算与误差分析-综合案例-测量数据校准与不确定度报告 =====
# 知识点：
#   - 综合串起本章：浮点/Decimal、稳健统计、误差传播、插值校准、矩阵求解、报告输出
#   - 校准流程：原始读数 -> 异常剔除 -> 稳健中心 -> 线性标定 -> 合成不确定度 -> 报表
#   - 不确定度传播：y = a·x + b 时 u(y)² = (a·u(x))² + u(a)² + u(b)²（一阶近似）
#   - 系统误差（偏置）与随机误差（标准差）分开报告，不要混成一个数
#   - 金额/最终结果用 Decimal 与 HALF_EVEN 舍入，避免展示层二次失真
#   - 全部标准库、临时目录、纯函数分析层，离线可运行
# 依赖：无（标准库）
import json
import math
import statistics
import tempfile
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

REF_LOW, REF_HIGH = 0.0, 100.0
CAL_SLOPE, CAL_INTERCEPT = 1.02, -0.5        # 真实标定系数（用于生成数据）


def mad(xs):
    med = statistics.median(xs)
    return statistics.median([abs(x - med) for x in xs])


def reject_outliers(xs, threshold=3.5):
    """修正 z-score 剔除异常（第656课）。"""
    med, m = statistics.median(xs), mad(xs)
    if m == 0:
        return list(xs), []
    kept, dropped = [], []
    for x in xs:
        z = 0.6745 * (x - med) / m
        (dropped if abs(z) > threshold else kept).append(x)
    return kept, dropped


def welford(xs):
    n, mean, m2 = 0, 0.0, 0.0
    for x in xs:
        n += 1
        d = x - mean
        mean += d / n
        m2 += d * (x - mean)
    return mean, math.sqrt(m2 / n) if n > 1 else 0.0


def fit_linear(xs, ys):
    """最小二乘拟合 y = a·x + b，返回 (a, b, 残差标准差)。"""
    n = len(xs)
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = math.fsum((x - mx) ** 2 for x in xs)
    sxy = math.fsum((x - mx) * (y - my) for x, y in zip(xs, ys))
    a = sxy / sxx
    b = my - a * mx
    resid = [y - (a * x + b) for x, y in zip(xs, ys)]
    s = math.sqrt(math.fsum(r * r for r in resid) / (n - 2)) if n > 2 else 0.0
    return a, b, s


@dataclass
class Result:
    raw_count: int
    kept_count: int
    dropped: list
    mean: float
    std: float
    median: float
    mad: float
    a: float
    b: float
    resid_std: float
    calibrated: float
    u_random: float
    u_system: float
    u_combined: float
    rounded: Decimal


def analyze(raw_readings, cal_points, u_slope=0.005, u_intercept=0.02):
    kept, dropped = reject_outliers(raw_readings)
    mean, std = welford(kept)
    med, m = statistics.median(kept), mad(kept)

    xs, ys = zip(*cal_points)
    a, b, resid_std = fit_linear(list(xs), list(ys))

    calibrated = a * med + b
    u_random = std / math.sqrt(len(kept))          # 均值的标准不确定度
    u_system = math.sqrt((med * u_slope) ** 2 + u_intercept ** 2 + resid_std ** 2)
    u_combined = math.hypot(u_random, u_system)
    rounded = Decimal(str(round(calibrated, 2))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return Result(len(raw_readings), len(kept), dropped, mean, std, med, m,
                  a, b, resid_std, calibrated, u_random, u_system, u_combined, rounded)


def render(r: Result) -> str:
    return "\n".join([
        "=" * 58,
        "测量数据校准与不确定度报告",
        "-" * 58,
        f"原始读数 {r.raw_count} 个，剔除异常 {len(r.dropped)} 个 -> {r.kept_count} 个",
        f"异常值: {r.dropped}",
        f"均值 {r.mean:.4f}  标准差 {r.std:.4f}  中位数 {r.median:.4f}  MAD {r.mad:.4f}",
        "-" * 58,
        f"标定曲线 y = {r.a:.6f}·x + {r.b:.6f}   残差标准差 {r.resid_std:.4f}",
        f"校准后结果 = {r.calibrated:.6f}",
        "-" * 58,
        f"随机不确定度 u_A = {r.u_random:.6f} (A 类，重复测量)",
        f"系统不确定度 u_B = {r.u_system:.6f} (B 类，标定/仪器)",
        f"合成标准不确定度 u_c = {r.u_combined:.6f}",
        f"扩展不确定度 U(k=2) = {2 * r.u_combined:.6f}",
        f"报告值 = {r.calibrated:.2f} ± {2 * r.u_combined:.2f} (k=2)",
        f"Decimal(HALF_EVEN) 展示 = {r.rounded}",
        "=" * 58,
    ])


# ---- 构造含异常值、带漂移的读数 ----
readings = [50.12, 50.08, 49.97, 50.21, 49.88, 50.05,
            50.31, 49.93, 50.17, 50.02, 999.0, -800.0]
cal_points = [(x, CAL_SLOPE * x + CAL_INTERCEPT + 0.03 * (i % 3 - 1))
              for i, x in enumerate(range(0, 101, 10))]

r = analyze(readings, cal_points)
print(render(r))

print("\n== 分阶段中间结果（可逐段校验）==")
kept, dropped = reject_outliers(readings)
print(f"  稳健剔除: 保留 {len(kept)} 个，剔除 {dropped}")
print(f"  拟合系数 a={r.a:.6f} (真值 {CAL_SLOPE}), b={r.b:.6f} (真值 {CAL_INTERCEPT})")
print(f"  中位数 {r.median:.4f} -> 校准 {r.calibrated:.4f}")
print(f"  u_random={r.u_random:.6f} u_system={r.u_system:.6f} "
      f"u_combined={r.u_combined:.6f}")
print(f"  合成用 hypot 而非 a+b：{math.hypot(r.u_random, r.u_system):.6f}")

print("\n== 异常值污染对比（若不剔除）==")
polluted = statistics.mean(readings)
print(f"  含异常值均值={polluted:.3f}  稳健中位数={r.median:.3f}")
print(f"  两者相差 {abs(polluted - r.median):.2f}，说明稳健统计的必要性")

print("\n== 不确定度预算（各项占比）==")
parts = {"A 类(重复测量)": r.u_random ** 2,
         "标定斜率": (r.median * 0.005) ** 2,
         "标定截距": 0.02 ** 2,
         "拟合残差": r.resid_std ** 2}
total_var = sum(parts.values())
for name, v in parts.items():
    print(f"  {name:<16} 方差贡献 {v:.6f}  占比 {v / total_var:>6.1%}")
print("  占比最大的项就是最值得改进测量的环节")

print("\n== 报表落盘 ==")
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "report.json"
    doc = {"report_value": str(r.rounded), "U_k2": round(2 * r.u_combined, 4),
           "n_kept": r.kept_count, "dropped": r.dropped,
           "a": round(r.a, 6), "b": round(r.b, 6)}
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), "utf-8")
    print(f"  {p.name} {p.stat().st_size} 字节")
    print("  ", json.dumps(json.loads(p.read_text("utf-8")), ensure_ascii=False))

print("\n== 方法回顾 ==")
for line in [
    "  稳健统计: 中位数/MAD 抗异常，Welford 稳定算方差（第656课）",
    "  误差传播: 一阶近似 + 方和根合成，A/B 类分开（本章）",
    "  曲线拟合: 最小二乘，残差标准差进入 B 类预算（第655/657课）",
    "  展示层  : Decimal + HALF_EVEN，避免 float 二次舍入（第652课）",
    "  分析层纯函数: 同样输入必得同样报表，可缓存、可单测、可复现",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加重复测量的 t 分布因子，按置信水平动态算 k 而不是固定 k=2。
# 2. 把线性标定换成二次标定，观察残差与 u_system 的变化。
# 3. 实现蒙特卡洛法（GUM-S1）传播不确定度，与一阶近似结果对比。
# 4. 思考：为什么系统误差与随机误差必须分开报告，而不能直接相加？
