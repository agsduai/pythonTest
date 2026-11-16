# ===== 第872课：贝叶斯推断与采样方法-粒子滤波 =====
# 知识点：
#   - 在线状态估计：传感器只给带噪声的观测，要实时追踪隐藏状态
#   - 卡尔曼滤波只适合线性高斯；粒子滤波用「一群带权样本」表示任意后验
#   - Bootstrap 滤波三步循环：预测（按过程模型撒粒子）-> 加权（按观测似然）
#     -> 重采样（ESS 低时集中粒子）
#   - ESS = 1/Σw² 是粒子有效数量的度量，低于阈值就重采样
#   - 非线性、非高斯、多模态都能处理 —— 这是它的核心优势
# 依赖：无（标准库）
import math
import random
import bisect


def systematic_resample(particles, weights, rng):
    """系统重采样：低方差，比逐个轮盘更均匀。"""
    n = len(weights)
    cum = []
    c = 0.0
    for w in weights:
        c += w
        cum.append(c)
    start = rng.random() / n
    positions = [start + i / n for i in range(n)]
    new_particles = []
    j = 0
    for u in positions:
        while u > cum[j]:
            j += 1
        new_particles.append(particles[j])
    return new_particles


def particle_filter(observations, rng, n=1000, x0=0.0,
                    process_std=0.6, obs_std=3.0, ess_frac=0.5):
    """模型: x_t = 0.9·x_{t-1} + N(0, σp);  z_t = x_t + N(0, σo)。"""
    particles = [x0 + rng.gauss(0, 2.0) for _ in range(n)]
    weights = [1.0 / n] * n
    estimates, ess_hist, resample_events = [], [], []
    for t, z in enumerate(observations):
        # 1) 预测
        particles = [0.9 * p + rng.gauss(0, process_std) for p in particles]
        # 2) 加权（观测似然，log 空间防下溢）
        logw = []
        for p in particles:
            logw.append(-0.5 * ((z - p) / obs_std) ** 2)
        mx = max(logw)
        weights = [math.exp(w - mx) for w in logw]
        total = sum(weights)
        weights = [w / total for w in weights]
        # 3) 估计 + ESS
        est = sum(w * p for w, p in zip(weights, particles))
        ess = 1.0 / sum(w * w for w in weights)
        estimates.append(est)
        ess_hist.append(ess)
        # 4) 重采样
        if ess < n * ess_frac:
            particles = systematic_resample(particles, weights, rng)
            weights = [1.0 / n] * n
            resample_events.append(t)
    return estimates, ess_hist, resample_events


rng = random.Random(3)

print("== 生成隐藏轨迹与观测 ==")
T = 60
true_state, observations = [], []
x = 5.0
for t in range(T):
    x = 0.9 * x + 1.5 + rng.gauss(0, 0.6)
    true_state.append(x)
    observations.append(x + rng.gauss(0, 3.0))
print(f"  真实状态(前5): {[round(v, 2) for v in true_state[:5]]}")
print(f"  观测(前5):     {[round(v, 2) for v in observations[:5]]}")
print(f"  观测噪声 σ = 3.0 —— 原始观测的 RMSE 应 ≈ 3.0")

print("\n== 运行粒子滤波（1000 粒子）==")
ests, ess, events = particle_filter(observations, rng)
print(f"  {'t':>3}{'真实':>9}{'观测':>9}{'滤波估计':>10}")
for t in range(0, T, 10):
    print(f"  {t:>3}{true_state[t]:>9.2f}{observations[t]:>9.2f}{ests[t]:>10.2f}")

print("\n== 精度对比 ==")


def rmse(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a))


r_obs = rmse(observations, true_state)
r_filt = rmse(ests, true_state)
print(f"  原始观测 RMSE = {r_obs:.3f}")
print(f"  粒子滤波 RMSE = {r_filt:.3f}  -> 降噪 {r_obs / r_filt:.2f} 倍")
print("  滤波器用过程模型 (x_t = 0.9 x_{t-1} + 1.5) 融合了历史信息")

print("\n== ESS 与重采样 ==")
print(f"  ESS 前 12 步: {[round(e) for e in ess[:12]]}")
print(f"  重采样发生 {len(events)} 次，出现在 t = {events[:8]}{'...' if len(events) > 8 else ''}")
print("  粒子权重退化（ESS 掉）-> 重采样把粒子集中到高似然区，权重复位")

print("\n== 粒子数的影响 ==")
print(f"  {'粒子数':>8}{'RMSE':>9}{'重采样次数':>10}")
for n in (50, 200, 1000, 5000):
    ests_n, _, ev_n = particle_filter(observations, rng, n=n)
    print(f"  {n:>8}{rmse(ests_n, true_state):>9.3f}{len(ev_n):>10}")
print("  粒子太少 -> 后验近似粗糙；太多 -> 只是计算成本，精度边际递减")

print("\n== 模型失配的代价 ==")
ests_bad, _, _ = particle_filter(observations, rng, process_std=5.0)
print(f"  过程噪声 σp 误设为 5.0 -> RMSE {rmse(ests_bad, true_state):.3f}")
print("  σp 过大 -> 滤波器太不信任自己的预测，几乎在追观测")
print("  σp 过小 -> 过度自信，跟不上真实运动 —— 调参就是调这两种失衡")

print("\n== 小结 ==")
for line in (
    "  粒子滤波 = 用加权样本在线逼近后验，循环：预测-加权-重采样",
    "  ESS 是粒子退化的体温计，系统重采样是低方差的恢复手段",
    "  非线性/非高斯/多模态都行；代价是维数灾难（高维粒子稀疏）",
    "  与 869 课 MCMC 对比：MCMC 离线精算，粒子滤波在线实时",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现无迹卡尔曼(UKF)思想的对照：在强非线性观测 z = x² + 噪声下对比粒子滤波。
# 2. 把权重更新改成「自适应观测噪声」：用最近 10 步残差估计 σo，观察 RMSE。
# 3. 实现多模态追踪：目标在两个房间之间跳变（过程模型加 5% 概率瞬移），
#    验证粒子滤波能同时维持两个假设直到观测分辨。
# 4. 思考：为什么重采样会造成「样本贫化」（多样本重复同一粒子）？有哪些缓解
#    手段（正则化/MCMC 移动步）？
