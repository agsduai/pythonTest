# ===== 第742课：强化学习入门-Q-learning 与时序差分 =====
# 知识点：
#   - 时序差分 TD：用「一步实测 + 自举估计」更新，无需等到回合结束
#   - TD 目标 = r + γ·max_a' Q(s',a')；TD 误差 δ = 目标 - Q(s,a)
#   - Q-learning（off-policy）：更新用贪心动作，行为用 ε-greedy，可学最优策略
#   - SARSA（on-policy）：更新用实际下一个动作，更保守（会绕开陷阱）
#   - 学习率 α：太大震荡、太小学得慢；ε 随时间衰减平衡探索/利用
#   - 收敛条件：所有 (s,a) 被无限次访问 + α 满足 Robbins-Monro 条件
# 依赖：无（标准库）
import math
import random
from collections import defaultdict

UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3
ACTIONS = [UP, DOWN, LEFT, RIGHT]
ARROWS = {UP: "↑", DOWN: "↓", LEFT: "←", RIGHT: "→"}
DELTAS = {UP: (-1,0), DOWN: (1,0), LEFT: (0,-1), RIGHT: (0,1)}


class CliffWorld:
    """4x6 悬崖行走：底行中间是悬崖(-100 并回起点)，右下是终点(+10)。"""
    def __init__(self, rows=4, cols=6, seed=0):
        self.rows, self.cols = rows, cols
        self.start = (rows-1, 0)
        self.goal = (rows-1, cols-1)
        self.cliff = {(rows-1, c) for c in range(1, cols-1)}
        self.rng = random.Random(seed)
        self.reset()

    def reset(self):
        self.pos = self.start
        return self.pos

    def step(self, a):
        dr, dc = DELTAS[a]
        r, c = self.pos
        ns = (max(0, min(self.rows-1, r+dr)), max(0, min(self.cols-1, c+dc)))
        self.pos = ns
        if ns in self.cliff:
            self.pos = self.start
            return self.start, -100.0, False
        if ns == self.goal:
            return ns, 10.0, True
        return ns, -1.0, False

    def states(self):
        return [(r,c) for r in range(self.rows) for c in range(self.cols)]


def eps_greedy(Q, s, eps, rng):
    if rng.random() < eps:
        return rng.choice(ACTIONS)
    qs = [Q[(s, a)] for a in ACTIONS]
    best = max(qs)
    return rng.choice([a for a, q in zip(ACTIONS, qs) if q == best])


def train(algorithm, episodes=800, alpha=0.1, gamma=0.9,
          eps0=0.3, decay=0.995, seed=7, slip=0.0):
    env = CliffWorld()
    rng = random.Random(seed)
    Q = defaultdict(float)
    returns = []
    for ep in range(episodes):
        eps = max(0.01, eps0 * decay ** ep)
        s = env.reset()
        total = 0.0
        a = eps_greedy(Q, s, eps, rng)
        for step in range(100):
            # 行为策略带 slip（随机环境），体现 on/off-policy 差异
            actual = rng.choice(ACTIONS) if rng.random() < slip else a
            ns, r, done = env.step(actual)
            total += r
            a_next = eps_greedy(Q, ns, eps, rng)
            if algorithm == "qlearning":
                target = r + gamma * max(Q[(ns, x)] for x in ACTIONS)
            else:  # SARSA：用实际会执行的下一个动作
                target = r + gamma * Q[(ns, a_next)]
            Q[(s, a)] += alpha * (target - Q[(s, a)])
            s, a = ns, a_next
            if done:
                break
        returns.append(total)
    return Q, returns, env


def greedy_policy(Q, env):
    pol = {}
    for s in env.states():
        if s == env.goal or s in env.cliff:
            continue
        pol[s] = max(ACTIONS, key=lambda a: Q[(s, a)])
    return pol


def rollout(Q, env, max_steps=30):
    s = env.reset()
    path, total = [s], 0.0
    for _ in range(max_steps):
        a = max(ACTIONS, key=lambda x: Q[(s, x)])
        s, r, done = env.step(a)
        path.append(s); total += r
        if done:
            break
    return path, total, done


print("== 悬崖行走环境 ==")
e = CliffWorld()
for r in range(e.rows):
    print("   " + "".join("G" if (r,c)==e.goal else "S" if (r,c)==e.start
                         else "X" if (r,c) in e.cliff else "." for c in range(e.cols)))
print("  S=起点 G=终点 X=悬崖(-100回起点) 每步 -1")

print("\n== Q-learning vs SARSA（600 回合）==")
for algo in ("qlearning", "sarsa"):
    Q, rets, env = train(algo, episodes=600, seed=7)
    early = sum(rets[:50]) / 50
    late = sum(rets[-50:]) / 50
    pol = greedy_policy(Q, env)
    path, total, done = rollout(Q, env)
    print(f"  {algo:<10}: 前50回合均回报={early:>7.2f} 后50回合={late:>7.2f} "
          f"贪心路径步数={len(path)-1} 回报={total:.1f} 到终点={done}")

print("\n== 收敛曲线（每 100 回合平均回报）==")
for algo in ("qlearning", "sarsa"):
    _, rets, _ = train(algo, episodes=600, seed=7)
    curve = [round(sum(rets[i:i+100])/100, 1) for i in range(0, 600, 100)]
    print(f"  {algo:<10}: {curve}")

print("\n== 学到的贪心策略 ==")
Q, _, env = train("qlearning", episodes=600, seed=7)
pol = greedy_policy(Q, env)
for r in range(env.rows):
    print("   " + "".join("G" if (r,c)==env.goal else "S" if (r,c)==env.start
                         else "X" if (r,c) in env.cliff else ARROWS[pol[(r,c)]]
                         for c in range(env.cols)))

print("\n== 学习率 α 的影响 ==")
for alpha in (0.01, 0.1, 0.5, 1.0):
    Q, rets, env = train("qlearning", episodes=400, alpha=alpha, seed=3)
    late = sum(rets[-50:]) / 50
    print(f"  α={alpha:<5}: 后期均回报={late:>7.2f} "
          f"Q 绝对值均值={sum(abs(v) for v in Q.values())/len(Q):.2f}")
print("  α 太大在随机环境里震荡，太小收敛慢")

print("\n== 有 slip 时 on/off-policy 差异 ==")
for slip in (0.0, 0.1, 0.2):
    row = []
    for algo in ("qlearning", "sarsa"):
        Q, rets, env = train(algo, episodes=500, seed=5, slip=slip)
        late = sum(rets[-100:]) / 100
        _, total, _ = rollout(Q, env)
        row.append(f"{algo} 训练回报={late:>6.1f} 贪心评估={total:>6.1f}")
    print(f"  slip={slip}: " + " | ".join(row))
print("  SARSA 学到的是「考虑到自己会手滑」的保守路径，Q-learning 学最优路径")

print("\n== TD 误差与自举 ==")
for line in (
    "  δ = r + γ max Q(s',·) - Q(s,a)，用估计更新估计（bootstrapping）",
    "  相比蒙特卡洛：不必等回合结束，方差小但有偏差",
    "  TD(λ)/资格迹在偏差与方差之间平滑插值",
    "  函数近似（DQN）用神经网络替代表格，需经验回放 + 目标网络",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 实现 Double Q-learning，缓解 Q-learning 的最大化偏差。
# 2. 加入经验回放，对比样本效率与训练稳定性。
# 3. 实现 n-step TD 与 TD(λ) 资格迹，观察收敛曲线。
# 4. 思考：为什么 Q-learning 是 off-policy，而 SARSA 是 on-policy？
