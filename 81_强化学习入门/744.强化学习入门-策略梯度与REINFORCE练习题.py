# ===== 第744课：强化学习入门-策略梯度与 REINFORCE =====
# 知识点：
#   - 基于策略的方法直接参数化 π(a|s;θ)，不经过 Q 表格，天然支持连续动作
#   - 策略梯度定理：∇J(θ) = E[ G_t · ∇log π(a_t|s_t;θ) ]
#   - REINFORCE（蒙特卡洛策略梯度）：整回合采样，用回报 G_t 加权 log 概率梯度
#   - 减基线 baseline：用 V(s) 或均值减掉 G_t，降方差而不引入偏差
#   - softmax 参数化：logits -> 概率；梯度 = one_hot(a) - p
#   - 与值方法对比：策略梯度可学随机策略、收敛更稳，但样本效率低、方差大
# 依赖：无（标准库）
import math
import random

UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3
ACTIONS = [UP, DOWN, LEFT, RIGHT]
DELTAS = {UP:(-1,0), DOWN:(1,0), LEFT:(0,-1), RIGHT:(0,1)}


class ShortestPath:
    """3x4：起点(0,0) 终点(0,3)，每步 -1，到终点 0；最短 3 步。"""
    def __init__(self, rows=3, cols=4, seed=0):
        self.rows, self.cols = rows, cols
        self.start, self.goal = (0,0), (0,cols-1)
        self.rng = random.Random(seed)
        self.reset()
    def reset(self):
        self.pos = self.start
        return self.pos
    def step(self, a):
        dr, dc = DELTAS[a]
        r, c = self.pos
        nr, nc = max(0,min(self.rows-1,r+dr)), max(0,min(self.cols-1,c+dc))
        self.pos = (nr,nc)
        if self.pos == self.goal:
            return self.pos, 0.0, True
        return self.pos, -1.0, False
    def states(self):
        return [(r,c) for r in range(self.rows) for c in range(self.cols)]


def softmax(logits):
    m = max(logits)
    exps = [math.exp(x - m) for x in logits]
    s = sum(exps)
    return [e / s for e in exps]


def sample(probs, rng):
    u, acc = rng.random(), 0.0
    for i, p in enumerate(probs):
        acc += p
        if u < acc:
            return i
    return len(probs) - 1


def reinforce(episodes=1500, alpha=0.05, gamma=0.99, use_baseline=True,
              seed=7):
    env = ShortestPath(seed=seed)
    rng = random.Random(seed)
    theta = {(s, a): 0.0 for s in env.states() for a in ACTIONS}
    returns = []
    for ep in range(episodes):
        # 采样一整条轨迹
        s = env.reset()
        traj = []
        for _ in range(40):
            logits = [theta[(s, a)] for a in ACTIONS]
            p = softmax(logits)
            a = sample(p, rng)
            ns, r, done = env.step(a)
            traj.append((s, a, r, p))
            s = ns
            if done:
                break
        # 反向计算每个时刻的回报 G_t
        G = 0.0
        Gs = [0.0] * len(traj)
        for t in range(len(traj)-1, -1, -1):
            G = traj[t][2] + gamma * G
            Gs[t] = G
        returns.append(Gs[0] if Gs else 0.0)
        baseline = sum(Gs) / len(Gs) if (use_baseline and Gs) else 0.0
        # 策略梯度更新
        for t, (s, a, _, p) in enumerate(traj):
            adv = Gs[t] - baseline
            for j, aj in enumerate(ACTIONS):
                grad = (1.0 if aj == a else 0.0) - p[j]
                theta[(s, aj)] += alpha * (gamma ** t) * adv * grad
    return theta, returns, env


def greedy_path(theta, env):
    s = env.reset()
    path = [s]
    for _ in range(20):
        a = max(ACTIONS, key=lambda x: theta[(s, x)])
        s, r, done = env.step(a)
        path.append(s)
        if done:
            break
    return path


print("== 环境 ==")
env = ShortestPath()
print("  3x4 网格，起点左上、终点右上，每步 -1；最优 3 步")

print("\n== REINFORCE：有/无基线对比 ==")
for use_base in (False, True):
    theta, rets, e = reinforce(episodes=1200, seed=7, use_baseline=use_base)
    early, late = sum(rets[:100])/100, sum(rets[-100:])/100
    path = greedy_path(theta, e)
    print(f"  baseline={use_base!s:<5}: 前100回合均回报={early:>6.2f} "
          f"后100回合={late:>6.2f} 贪心路径={path} 步数={len(path)-1}")

print("\n== 学到的策略概率（起点与中间格）==")
theta, _, e = reinforce(episodes=1500, seed=7, use_baseline=True)
for s in [(0,0), (0,1), (1,0), (2,2)]:
    p = softmax([theta[(s,a)] for a in ACTIONS])
    print(f"  s={s}: " + " ".join(f"{['↑','↓','←','→'][a]}={p[a]:.2f}" for a in ACTIONS))

print("\n== 策略梯度公式拆解 ==")
logits = [1.0, 0.0, -1.0, 0.5]
p = softmax(logits)
print(f"  logits={logits} -> softmax={[round(x,3) for x in p]}")
a = 0
grad = [(1.0 if j == a else 0.0) - p[j] for j in range(4)]
print(f"  ∇logπ(a=0) = one_hot - p = {[round(x,3) for x in grad]}")
print("  梯度方向：提高被选动作概率、降低其他动作概率，幅度由 G_t 加权")

print("\n== 基线为什么能降方差且不引入偏差 ==")
for line in (
    "  E[∇logπ · b(s)] = b(s)·Σ_a ∇π = b(s)·∇1 = 0",
    "  只要基线不依赖当前动作 a，减掉它就不改变期望梯度",
    "  用状态价值 V(s) 作基线最优；简化版用「本回合平均回报」也有效",
    "  Actor-Critic 正是用可学习的 critic 充当基线（第745课）",
):
    print(" ", line)

print("\n== 值方法 vs 策略方法 ==")
print(f"  {'维度':<14}{'值方法(DQN/Q)':<22}{'策略方法(PG)'}")
for row in (("策略表示", "由 Q 贪心导出，确定性", "直接输出概率，可随机"),
            ("连续动作", "需离散化/额外技巧", "天然支持"),
            ("样本效率", "较高（可回放）", "较低（on-policy）"),
            ("方差", "低（自举）", "高（需基线）"),
            ("收敛", "可能不稳定", "通常更平滑")):
    print(f"  {row[0]:<14}{row[1]:<22}{row[2]}")

print("\n== 工程要点 ==")
for line in [
    "  回报要做标准化/裁剪，否则量级差异会让步长失控",
    "  on-policy：每次更新后旧轨迹就作废，不能像 DQN 那样回放",
    "  entropy bonus 加一点熵正则，防止策略过早坍缩",
    "  PPO/TRPO 通过信任域约束解决 PG 步长敏感问题",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「带可学习 V(s) 基线」的 Actor-Critic，对比与均值基线的方差。
# 2. 给策略加熵正则项，观察探索持续时间与最终回报。
# 3. 用 softmax 温度参数控制探索，验证温度衰减的效果。
# 4. 思考：为什么基线可以依赖状态 s，却不能依赖动作 a？
