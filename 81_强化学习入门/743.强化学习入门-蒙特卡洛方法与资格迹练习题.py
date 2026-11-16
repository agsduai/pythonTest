# ===== 第743课：强化学习入门-蒙特卡洛方法与资格迹 =====
# 知识点：
#   - 蒙特卡洛 MC：等回合结束，用实际回报 G_t 更新，无偏但方差大
#   - 首次访问 / 每次访问 MC；增量式 Q(s,a) += α(G - Q)
#   - TD(λ)：用资格迹 e(s,a) 把「一步 TD」与「完整 MC」统一起来
#   - 累积迹 e = γλ·e + 1(访问)；每步对所有 (s,a) 按 δ 更新
#   - λ=0 退化为 TD(0)，λ=1 等价于 MC（在线实现有细微差异）
#   - 后向视图 backward view：一步 δ 沿迹回传，比前向 n-step 更好实现
# 依赖：无（标准库）
import random
from collections import defaultdict

UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3
ACTIONS = [UP, DOWN, LEFT, RIGHT]
DELTAS = {UP:(-1,0), DOWN:(1,0), LEFT:(0,-1), RIGHT:(0,1)}


class SimpleGrid:
    """5x5：到终点 +10，每步 -1，撞墙原地 -2。"""
    def __init__(self, n=5, seed=0):
        self.n = n
        self.start = (0, 0)
        self.goal = (n-1, n-1)
        self.rng = random.Random(seed)
        self.reset()
    def reset(self):
        self.pos = self.start
        return self.pos
    def step(self, a):
        dr, dc = DELTAS[a]
        r, c = self.pos
        nr, nc = r+dr, c+dc
        if not (0 <= nr < self.n and 0 <= nc < self.n):
            return self.pos, -2.0, False        # 撞墙
        self.pos = (nr, nc)
        if self.pos == self.goal:
            return self.pos, 10.0, True
        return self.pos, -1.0, False
    def states(self):
        return [(r,c) for r in range(self.n) for c in range(self.n)]


def eps_greedy(Q, s, eps, rng):
    if rng.random() < eps:
        return rng.choice(ACTIONS)
    vals = [Q[(s,a)] for a in ACTIONS]
    best = max(vals)
    return rng.choice([a for a, v in zip(ACTIONS, vals) if v == best])


def generate_episode(env, Q, eps, rng, max_steps=100):
    s = env.reset()
    ep = []
    for _ in range(max_steps):
        a = eps_greedy(Q, s, eps, rng)
        ns, r, done = env.step(a)
        ep.append((s, a, r))
        s = ns
        if done:
            break
    return ep


def mc_control(episodes=3000, alpha=0.1, gamma=0.95, eps=0.2, seed=1):
    env = SimpleGrid(seed=seed)
    rng = random.Random(seed)
    Q = defaultdict(float)
    returns = []
    for ep_i in range(episodes):
        ep = generate_episode(env, Q, eps, rng)
        G = 0.0
        visited = set()
        # 反向累计回报
        for t in range(len(ep)-1, -1, -1):
            s, a, r = ep[t]
            G = r + gamma * G
            if (s, a) not in visited:           # 首次访问 MC
                visited.add((s, a))
                Q[(s, a)] += alpha * (G - Q[(s, a)])
        returns.append(G)
    return Q, returns, env


def sarsa_lambda(episodes=3000, alpha=0.1, gamma=0.95, lam=0.6,
                 eps=0.2, seed=1):
    env = SimpleGrid(seed=seed)
    rng = random.Random(seed)
    Q = defaultdict(float)
    returns = []
    for ep_i in range(episodes):
        e = defaultdict(float)                  # 资格迹
        s = env.reset()
        a = eps_greedy(Q, s, eps, rng)
        G = 0.0
        for _ in range(100):
            ns, r, done = env.step(a)
            na = eps_greedy(Q, ns, eps, rng)
            delta = r + gamma * Q[(ns, na)] - Q[(s, a)]
            e[(s, a)] += 1.0                    # 累积迹：访问即 +1
            for key in list(e):
                Q[key] += alpha * delta * e[key]
                e[key] *= gamma * lam           # 迹按 γλ 衰减
            G += r
            s, a = ns, na
            if done:
                break
        returns.append(G)
    return Q, returns, env


def evaluate(Q, env, max_steps=50):
    s = env.reset()
    total, steps = 0.0, 0
    for _ in range(max_steps):
        a = max(ACTIONS, key=lambda x: Q[(s, x)])
        s, r, done = env.step(a)
        total += r; steps += 1
        if done:
            break
    return total, steps, done


print("== 环境：5x5 网格，起点(0,0) 终点(4,4) ==")
print("  每步 -1，撞墙 -2，到终点 +10；最优路径 8 步，回报 +3")

print("\n== 首次访问 MC 控制 ==")
Q_mc, rets_mc, env = mc_control(episodes=2000, seed=3)
print(f"  前200回合均回报={sum(rets_mc[:200])/200:.2f} "
      f"后200回合={sum(rets_mc[-200:])/200:.2f}")
total, steps, done = evaluate(Q_mc, env)
print(f"  贪心评估: 回报={total:.1f} 步数={steps} 到终点={done}")

print("\n== SARSA(λ)：不同 λ ==")
for lam in (0.0, 0.3, 0.6, 0.9, 1.0):
    Q, rets, e = sarsa_lambda(episodes=1500, lam=lam, seed=3)
    total, steps, done = evaluate(Q, e)
    print(f"  λ={lam:<4}: 后200回合均回报={sum(rets[-200:])/200:>6.2f} "
          f"贪心评估={total:>5.1f} 步数={steps} 到终点={done}")

print("\n== MC vs TD 的偏差-方差 ==")
for line in (
    "  MC: 用真实回报，无偏；但轨迹长、随机性叠加 -> 方差大",
    "  TD: 用自举估计，有偏；只依赖一步 -> 方差小、可在线学",
    "  λ 在两者之间插值：λ↑ 更接近 MC，λ↓ 更接近 TD",
):
    print(" ", line)

print("\n== 资格迹的前向/后向视图 ==")
for line in (
    "  前向视图: G_t^(n) = r+...+γ^n Q(s_{t+n})，再按 (1-λ)λ^{n-1} 加权",
    "  后向视图: 每步一个 TD 误差 δ，沿资格迹 e 回传给所有最近访问的状态",
    "  两者在离线线性情形下等价；后向视图实现更高效",
    "  替换迹(replacing) vs 累积迹(accumulating)影响重复访问时的权重",
):
    print(" ", line)

print("\n== 学习曲线（MC，每 200 回合）==")
curve = [round(sum(rets_mc[i:i+200])/200, 2) for i in range(0, 2000, 200)]
print("  ", curve)

print("\n== 工程要点 ==")
for line in [
    "  MC 必须等回合结束，不适合无终止的持续任务",
    "  资格迹需要 O(|S||A|) 内存，函数近似时用「迹向量」替代",
    "  λ 常取 0.6~0.9；太大方差回升，太小丢失长期信用分配",
    "  深层 RL 里 n-step return / GAE 是资格迹思想的现代形式",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「替换迹」资格迹，与累积迹在重复访问状态下的结果对比。
# 2. 用 n-step 前向视图复现 λ=0 与 λ=1 的等价性。
# 3. 给 MC 增加重要性采样，实现 off-policy 评估。
# 4. 思考：为什么 λ=1 时 SARSA(λ) 与蒙特卡洛「几乎」等价？
