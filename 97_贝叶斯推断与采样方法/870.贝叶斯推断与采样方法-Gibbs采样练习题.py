# ===== 第870课：贝叶斯推断与采样方法-Gibbs采样 =====
# 知识点：
#   - Gibbs：每个坐标按「其他坐标固定时的条件分布」轮流采样
#   - 只要条件分布能直接采样，就无需任何接受/拒绝 —— 每步必接受
#   - 条件分布 p(x|y) 对二元正态是解析的：N(ρy, 1-ρ²)
#   - 与 MH 对比：无调参、无拒绝，但要求每个条件分布可采样
#   - 用样本矩逼近联合分布：验证相关系数的恢复
# 依赖：无（标准库）
import math
import random


def gibbs_bivariate(n, rho, rng, x0=0.0, y0=0.0, burn=1000):
    """二元标准正态 N(0, Σ), Σ=[[1,ρ],[ρ,1]] 的 Gibbs 采样。"""
    cond_sd = math.sqrt(1 - rho * rho)
    x, y = x0, y0
    xs, ys = [], []
    for i in range(n + burn):
        x = rng.gauss(rho * y, cond_sd)       # x|y ~ N(ρy, 1-ρ²)
        y = rng.gauss(rho * x, cond_sd)       # y|x ~ N(ρx, 1-ρ²)
        if i >= burn:
            xs.append(x)
            ys.append(y)
    return xs, ys


def corr(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / n
    vx = sum((a - mx) ** 2 for a in xs) / n
    vy = sum((b - my) ** 2 for b in ys) / n
    return cov / math.sqrt(vx * vy)


rng = random.Random(1)

print("== 条件分布采样（每步都接受）==")
rho = 0.8
xs, ys = gibbs_bivariate(20000, rho, rng)
mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
print(f"  目标: 均值 (0, 0)，相关系数 ρ = {rho}")
print(f"  Gibbs: 均值 ({mx:.4f}, {my:.4f})，样本相关系数 = {corr(xs, ys):.4f}")

print("\n== 不同 ρ 下的恢复 ==")
print(f"  {'设定ρ':>8}{'样本相关':>10}")
for r in (-0.6, 0.0, 0.3, 0.8, 0.95):
    xs2, ys2 = gibbs_bivariate(8000, r, rng)
    print(f"  {r:>8.2f}{corr(xs2, ys2):>10.4f}")
print("  |ρ| 越接近 1，一次更新后两个坐标几乎同步 —— 混合变慢（强相关链）")

print("\n== Gibbs 的路径（前 60 步）==")
xs3, ys3 = gibbs_bivariate(60, 0.8, rng)
print("  x: " + "".join("▓" if v > 0 else "░" for v in xs3))
print("  y: " + "".join("▓" if v > 0 else "░" for v in ys3))
print("  x 与 y 高度同步 —— 强相关正是 Gibbs 慢的根源")

print("\n== 与 MH 的对比（同一相关目标）==")


def log_target2(x, y, r):
    return -(x * x - 2 * r * x * y + y * y) / (2 * (1 - r * r))


# MH 在二维随机游走
def mh2(logp, x0, y0, n, sigma, rng, burn=1000):
    x, y, lp = x0, y0, logp(x0, y0)
    accepted = 0
    out = []
    for i in range(n + burn):
        nx, ny = x + rng.gauss(0, sigma), y + rng.gauss(0, sigma)
        nlp = logp(nx, ny)
        if math.log(rng.random() + 1e-300) < nlp - lp:
            x, y, lp = nx, ny, nlp
            accepted += 1
        if i >= burn:
            out.append((x, y))
    return out, accepted / (n + burn)


mh_samples, acc = mh2(lambda a, b: log_target2(a, b, rho), 0.0, 0.0, 20000, 1.0, rng)
mh_corr = corr([s[0] for s in mh_samples], [s[1] for s in mh_samples])
print(f"  MH(2维随机游走, σ=1): 接受率 {acc:.2f}, 相关系数 {mh_corr:.4f}")
print(f"  Gibbs: 无需调 σ、接受率 100%，相关系数 {corr(xs, ys):.4f}")
print("  但 Gibbs 需要可采样的条件分布；MH 只需要可计算的目标密度")

print("\n== 数据增强（Gibbs 的杀手锏思路）==")
print("  混合模型中：先按当前参数把每个点『分配』给分量（E步式采样），")
print("  再在固定分配下更新各分量参数 —— 两步都是简单分布")
print("  这种『引入隐变量 + 交替采样』是 Gibbs 最重要的应用模式")

print("\n== 小结 ==")
for line in (
    "  Gibbs = 逐坐标 MH 的特例，条件分布可直接采样时零拒绝",
    "  强相关坐标会让链移动缓慢（每次只动一个方向）",
    "  数据增强把不可直接采样的模型拆成可采样的条件分布",
    "  下一课：不采样后验本身，而是找「最好的单点近似」—— 变分推断",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现三坐标链：三元正态 (ρxy=0.9, 其余独立)，观察 xy 两坐标的混合是否变慢。
# 2. 用 Gibbs 做「已知 σ 的正态均值 + 缺失数据」：3 个观测 + 2 个缺失值，
#    缺失值从 N(μ,σ²) 补采样，μ 从 Normal-Normal 共轭采样，验证后验均值。
# 3. 给 Gibbs 加稀疏化（每 10 步取 1 样本），对比相关系数估计的标准差。
# 4. 思考：为什么 Gibbs 不会出现「拒绝」？它付出的是什么代价？
