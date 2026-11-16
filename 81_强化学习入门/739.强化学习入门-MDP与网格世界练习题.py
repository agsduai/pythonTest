# ===== 第739课：强化学习入门-MDP与网格世界 =====
# 知识点：
#   - MDP 五元组：状态 S、动作 A、转移 P(s'|s,a)、奖励 R、折扣 γ
#   - 回报 G_t = r_t + γ·r_{t+1} + γ²·r_{t+2} + ...；γ 越小越短视
#   - 策略 π(a|s)：状态到动作的映射；确定性/随机性
#   - 状态价值 V^π(s) = E[G_t | s]，动作价值 Q^π(s,a) = E[G_t | s,a]
#   - 贝尔曼期望方程：V(s) = Σπ(a|s)ΣP(s'|s,a)[R + γV(s')]
#   - 网格世界（GridWorld）是最小可运行环境：终态、陷阱、每步小惩罚
# 依赖：无（标准库）
import random
from dataclasses import dataclass, field

UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3
ACTIONS = [UP, DOWN, LEFT, RIGHT]
ARROWS = {UP: "↑", DOWN: "↓", LEFT: "←", RIGHT: "→"}
DELTAS = {UP: (-1, 0), DOWN: (1, 0), LEFT: (0, -1), RIGHT: (0, 1)}


class GridWorld:
    """4x4 网格：S 起点，G 终点(+10)，X 陷阱(-10)，每步 -0.1。"""

    def __init__(self, rows=4, cols=4, slip=0.0, seed=0):
        self.rows, self.cols, self.slip = rows, cols, slip
        self.start = (rows - 1, 0)
        self.goal = (0, cols - 1)
        self.traps = {(1, 1), (2, 2)}
        self.rng = random.Random(seed)
        self.reset()

    def reset(self):
        self.pos = self.start
        return self.pos

    @property
    def states(self):
        return [(r, c) for r in range(self.rows) for c in range(self.cols)]

    def is_terminal(self, s):
        return s == self.goal or s in self.traps

    def step(self, a):
        if self.is_terminal(self.pos):
            return self.pos, 0.0, True
        # slip：以一定概率走偏到随机方向（随机环境）
        if self.rng.random() < self.slip:
            a = self.rng.choice(ACTIONS)
        dr, dc = DELTAS[a]
        r, c = self.pos
        nr, nc = max(0, min(self.rows - 1, r + dr)), max(0, min(self.cols - 1, c + dc))
        self.pos = (nr, nc)
        if self.pos == self.goal:
            return self.pos, 10.0, True
        if self.pos in self.traps:
            return self.pos, -10.0, True
        return self.pos, -0.1, False

    def transitions(self, s, a):
        """返回 [(p, s', r, done)]，用于基于模型的算法（值迭代/策略迭代）。"""
        if self.is_terminal(s):
            return [(1.0, s, 0.0, True)]
        out = []
        # 展开 slip：主方向概率 1-slip，其余各 slip/(|A|-1)
        others = [x for x in ACTIONS if x != a]
        plans = [(a, 1 - self.slip)] + [(x, self.slip / len(others)) for x in others]
        for actual, p in plans:
            dr, dc = DELTAS[actual]
            nr = max(0, min(self.rows - 1, s[0] + dr))
            nc = max(0, min(self.cols - 1, s[1] + dc))
            ns = (nr, nc)
            if ns == self.goal:
                out.append((p, ns, 10.0, True))
            elif ns in self.traps:
                out.append((p, ns, -10.0, True))
            else:
                out.append((p, ns, -0.1, False))
        return out

    def render(self, policy=None, values=None):
        lines = []
        for r in range(self.rows):
            cells = []
            for c in range(self.cols):
                s = (r, c)
                if s == self.goal:
                    cells.append(" G ")
                elif s in self.traps:
                    cells.append(" X ")
                elif s == self.start:
                    cells.append(" S ")
                elif policy and s in policy:
                    cells.append(f" {ARROWS[policy[s]]} ")
                else:
                    cells.append(" . ")
            lines.append("".join(cells))
        return "\n".join(lines)


print("== 网格世界 ==")
env = GridWorld()
print(env.render())
print("  S=起点  G=终点(+10)  X=陷阱(-10)  每步 -0.1")

print("\n== 一条随机轨迹（γ=0.9）==")
env.reset()
rng = random.Random(2)
traj = [env.pos]
total = 0.0
gamma = 0.9
for t in range(8):
    a = rng.choice(ACTIONS)
    s, r, done = env.step(a)
    traj.append(s)
    total += (gamma ** t) * r
    print(f"  step {t+1}: {ARROWS[a]} -> {s}, r={r:+.1f}, done={done}")
    if done:
        break
print(f"  折扣回报 G_0 = {total:.3f}")

print("\n== 转移模型 P(s'|s,a) ==")
s = (3, 1)
for a in (UP, RIGHT):
    tr = env.transitions(s, a)
    print(f"  s={s} a={ARROWS[a]}（slip=0）: "
          f"{[(round(p,2), ns, r) for p, ns, r, _ in tr]}")
env2 = GridWorld(slip=0.2, seed=1)
tr = env2.transitions((3, 1), UP)
print(f"  slip=0.2 时: {[(round(p,2), ns) for p, ns, _, _ in tr]}")
print("  概率和 =", round(sum(p for p, *_ in tr), 6))

print("\n== 贝尔曼期望方程（迭代求解 V^π）==")
def evaluate_policy(env, policy, gamma=0.9, theta=1e-6):
    V = {s: 0.0 for s in env.states}
    for it in range(1000):
        delta = 0.0
        for s in env.states:
            if env.is_terminal(s):
                continue
            a = policy[s]
            # 终态转移仍计入即时奖励，只是不再加 gamma*V(终态)
            v = sum(p * (r + (0.0 if done else gamma * V[ns]))
                    for p, ns, r, done in env.transitions(s, a))
            delta = max(delta, abs(v - V[s]))
            V[s] = v
        if delta < theta:
            return V, it + 1
    return V, 1000

# 一个「一直向右/向上」的朴素策略
policy = {}
for r in range(env.rows):
    for c in range(env.cols):
        policy[(r, c)] = UP if r > 0 else RIGHT
V, iters = evaluate_policy(env, policy)
print(f"  收敛迭代 {iters} 次，部分 V 值:")
for r in range(env.rows):
    print("   ", [f"{V[(r,c)]:+6.2f}" for c in range(env.cols)])

print("\n== γ 对价值的影响 ==")
for g in (0.0, 0.5, 0.9, 0.99):
    Vg, _ = evaluate_policy(env, policy, gamma=g)
    print(f"  γ={g:<5}: V(start)={Vg[env.start]:>8.3f}  V(goal旁)={Vg[(0,2)]:>8.3f}")
print("  γ 越大越看重远期奖励，价值尺度也越大")

print("\n== 马尔可夫性质 ==")
for line in (
    "  下一状态只依赖 (当前状态, 当前动作)，与历史路径无关",
    "  若环境部分可观测（POMDP），需把历史压缩成 belief 状态",
    "  网格世界里位置就是充分统计量；真实场景常要拼帧/记忆",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 给环境增加「墙壁」状态，撞墙原地不动且奖励 -1。
# 2. 实现策略迭代：评估 + 贪心改进，直到策略稳定。
# 3. 用蒙特卡洛采样估计 V^π，与贝尔曼解析解对比。
# 4. 思考：为什么每步 -0.1 的「存活惩罚」能促使智能体走最短路？
