# ===== 第886课：概率图模型与结构化推断-马尔可夫随机场与Ising模型 =====
# 知识点：
#   - MRF：用无向图 + 势函数定义分布（不像贝叶斯网络有方向/条件表）
#   - Ising 模型：格点上自旋 ±1，能量 E = -J·Σ 邻接·s_i·s_j - Σ h_i·s_i
#   - P(s) ∝ exp(-E(s))：配分函数求和爆炸 -> 只能采样/近似推断
#   - 吉布斯采样（870 课思想用在离散网格上）：按邻居条件分布逐点翻转
#   - 温度参数控制有序/无序；ICM（条件众数迭代）求 MAP 近似
# 依赖：无（标准库）
import math
import random


def make_grid(n, rng, p=0.5):
    return [[1 if rng.random() < p else -1 for _ in range(n)] for _ in range(n)]


def neighbors(grid, i, j, n):
    for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        yield grid[(i + di) % n][(j + dj) % n]


def local_field(grid, i, j, n):
    """邻居自旋之和（外场 h=0 的教学设定）。"""
    return sum(neighbors(grid, i, j, n))


def energy(grid, n, J=1.0):
    """E = -J·Σ_{<i,j>} s_i·s_j（每对只数一次）。"""
    e = 0.0
    for i in range(n):
        for j in range(n):
            for di, dj in ((0, 1), (1, 0)):
                e += grid[i][j] * grid[(i + di) % n][(j + dj) % n]
    return -J * e


def magnetization(grid):
    total = sum(sum(row) for row in grid)
    return total / (len(grid) * len(grid))


def gibbs_sweep(grid, n, beta, rng):
    """一次扫描：逐点按条件分布 P(s_i=+1|邻居) ∝ exp(2β·邻居和) 采样。"""
    for i in range(n):
        for j in range(n):
            nb = local_field(grid, i, j, n)
            p_up = 1.0 / (1.0 + math.exp(-2 * beta * nb))
            grid[i][j] = 1 if rng.random() < p_up else -1


def icm_sweep(grid, n):
    """ICM：逐点取使局部能量最小的自旋 -> MAP 的贪心近似。"""
    for i in range(n):
        for j in range(n):
            grid[i][j] = 1 if local_field(grid, i, j, n) >= 0 else -1


def render(grid):
    return "\n".join("".join("█" if s == 1 else "·" for s in row)
                     for row in grid)


rng = random.Random(41)
n = 10

print("== Ising 模型设定 ==")
print(f"  {n}x{n} 周期网格，能量 E = -Σ 邻接 s_i·s_j（J=1，无外场）")
print("  P(s) ∝ exp(-β·E)：β 大 = 偏向同色有序，β 小 = 接近随机")

print("\n== 温度扫描：从无序到有序 ==")
print(f"  {'β':>6}{'扫描数':>8}{'平均磁化|':>12}{'能量':>10}")
for beta in (0.1, 0.3, 0.44, 0.6, 1.0):
    grid = make_grid(n, rng)
    for _ in range(300):
        gibbs_sweep(grid, n, beta, rng)
    mags = []
    for _ in range(200):
        gibbs_sweep(grid, n, beta, rng)
        mags.append(abs(magnetization(grid)))
    print(f"  {beta:>6.2f}{500:>8}{sum(mags) / len(mags):>12.3f}"
          f"{energy(grid, n):>10.1f}")
print("  β≈0.44 附近磁化率激增（2D Ising 相变 βc≈0.4407）—— 采样捕捉相变")

print("\n== 两种状态的可视化 ==")
grid_hot = make_grid(n, rng)
for _ in range(50):
    gibbs_sweep(grid_hot, n, 0.2, rng)
grid_cold = make_grid(n, rng)
for _ in range(50):
    gibbs_sweep(grid_cold, n, 0.2, rng)
for _ in range(800):
    gibbs_sweep(grid_cold, n, 1.0, rng)
print("  β=0.2（高温无序）:")
print(render(grid_hot))
print("  β=1.0（低温有序，磁化取同一符号）:")
print(render(grid_cold))

print("\n== 从随机初值出发的弛豫 ==")
grid = make_grid(n, rng)
print(f"  初始磁化 = {magnetization(grid):.3f}")
done = 0
for sweep in (0, 50, 200, 1000):
    for _ in range(sweep - done):
        gibbs_sweep(grid, n, 0.8, rng)
    done = sweep
    print(f"  {sweep:>5} 次扫描后 |磁化| = {abs(magnetization(grid)):.3f}, 能量 = {energy(grid, n):.1f}")
print("  系统滑向低能量有序态 —— 吉布斯采样的平稳分布偏向低能量构型")

print("\n== ICM 求 MAP（近似）==")
grid_map = make_grid(n, rng)
for _ in range(30):
    icm_sweep(grid_map, n)
e_icm = energy(grid_map, n)
grid_ref = make_grid(n, rng)
for _ in range(3000):
    gibbs_sweep(grid_ref, n, 3.0, rng)
print(f"  ICM 能量 = {e_icm:.1f}")
print(f"  低温吉布斯（β=3）能量 = {energy(grid_ref, n):.1f}")
print("  ICM 快但易卡在亚稳态；真实 MAP 需要图割/模拟退火（715 课思想）")

print("\n== 为什么必须采样 ==")
print(f"  配分函数 Z = Σ_s exp(-βE(s)) 有 2^(n²) = 2^{n * n} 项 —— 无法枚举")
print("  所有期望量（磁化/能量）都只能靠：MCMC 采样、变分近似或特殊可解情形")
print("  这正是概率图模型推断难度的『教科书标本』")

print("\n== 小结 ==")
for line in (
    "  MRF 用局部势定义全局分布：能量低 ≠ 概率 1，而是 exp 加权",
    "  吉布斯采样把「全网求和」变成「逐点条件采样」，代价是收敛慢",
    "  Ising 的相变展示了『简单局部规则涌现全局结构』",
    "  887 课：当图是树时，推断其实可以精确 —— 信念传播",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 加外场 h>0：P(s_i=+1) ∝ exp(β(J·邻居和 + h))，观察磁化曲线的滞后现象。
# 2. 实现模拟退火求 Ising 基态，与 ICM 对比能量。
# 3. 用「平均场近似」（871 课思想）：假设每个点独立，自洽求解平均磁化，
#    与吉布斯采样结果对照。
# 4. 思考：为什么吉布斯采样的平稳分布恰好是 Ising 分布？条件分布与联合分布
#    的关系是什么？
