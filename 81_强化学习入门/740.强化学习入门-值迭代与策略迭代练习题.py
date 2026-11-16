# ===== 第740课：强化学习入门-值迭代与策略迭代 =====
# 知识点：
#   - 贝尔曼最优方程：V*(s) = max_a ΣP(s'|s,a)[R + γV*(s')]
#   - 值迭代 VI：直接反复套用最优算子，收敛后从 V* 导出贪心策略
#   - 策略迭代 PI：交替做「策略评估(解 V^π)」+「策略改进(对 Q 取 argmax)」
#   - Q 值：Q(s,a) = ΣP[R + γV(s')]，策略 = argmax_a Q(s,a)
#   - 收敛性：γ<1 时贝尔曼算子是压缩映射，两种算法都收敛到同一 V*
#   - VI 每次迭代便宜但次数多；PI 每次评估贵但通常轮数少
# 依赖：无（标准库）
import time
from collections import defaultdict

UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3
ACTIONS = [UP, DOWN, LEFT, RIGHT]
ARROWS = {UP: "↑", DOWN: "↓", LEFT: "←", RIGHT: "→"}
DELTAS = {UP: (-1,0), DOWN: (1,0), LEFT: (0,-1), RIGHT: (0,1)}


class Grid:
    def __init__(self, rows=4, cols=4, gamma=0.9, step_cost=-0.1):
        self.rows, self.cols, self.gamma, self.step_cost = rows, cols, gamma, step_cost
        self.start = (rows-1, 0)
        self.goal = (0, cols-1)
        self.traps = {(1,1), (2,2)}
        self.states = [(r,c) for r in range(rows) for c in range(cols)]

    def terminal(self, s):
        return s == self.goal or s in self.traps

    def transitions(self, s, a):
        if self.terminal(s):
            return [(1.0, s, 0.0, True)]
        dr, dc = DELTAS[a]
        ns = (max(0, min(self.rows-1, s[0]+dr)), max(0, min(self.cols-1, s[1]+dc)))
        if ns == self.goal:
            return [(1.0, ns, 10.0, True)]
        if ns in self.traps:
            return [(1.0, ns, -10.0, True)]
        return [(1.0, ns, self.step_cost, False)]

    def q_value(self, s, a, V):
        return sum(p * (r + (0.0 if done else self.gamma * V[ns]))
                   for p, ns, r, done in self.transitions(s, a))

    def render(self, V=None, policy=None):
        for r in range(self.rows):
            if V is not None:
                print("   " + " ".join(f"{V[(r,c)]:+6.2f}" for c in range(self.cols)))
            else:
                row = []
                for c in range(self.cols):
                    s = (r,c)
                    if s == self.goal: row.append(" G ")
                    elif s in self.traps: row.append(" X ")
                    elif s == self.start: row.append(" S ")
                    else: row.append(f" {ARROWS[policy[s]]} ")
                print("   " + "".join(row))


def value_iteration(env, theta=1e-6, max_iter=1000):
    V = {s: 0.0 for s in env.states}
    for it in range(1, max_iter + 1):
        delta = 0.0
        newV = dict(V)
        for s in env.states:
            if env.terminal(s):
                continue
            newV[s] = max(env.q_value(s, a, V) for a in ACTIONS)
            delta = max(delta, abs(newV[s] - V[s]))
        V = newV
        if delta < theta:
            break
    policy = {s: max(ACTIONS, key=lambda a: env.q_value(s, a, V))
              for s in env.states if not env.terminal(s)}
    return V, policy, it


def policy_evaluation(env, policy, V=None, theta=1e-6, max_iter=1000):
    V = {s: 0.0 for s in env.states} if V is None else dict(V)
    for it in range(1, max_iter + 1):
        delta = 0.0
        for s in env.states:
            if env.terminal(s):
                continue
            v = env.q_value(s, policy[s], V)
            delta = max(delta, abs(v - V[s]))
            V[s] = v
        if delta < theta:
            break
    return V, it


def policy_iteration(env, max_rounds=100):
    policy = {s: RIGHT for s in env.states if not env.terminal(s)}
    V = None
    for rnd in range(1, max_rounds + 1):
        V, _ = policy_evaluation(env, policy, V)
        stable = True
        for s in env.states:
            if env.terminal(s):
                continue
            best = max(ACTIONS, key=lambda a: env.q_value(s, a, V))
            if best != policy[s]:
                policy[s] = best
                stable = False
        if stable:
            return V, policy, rnd
    return V, policy, max_rounds


print("== 值迭代 ==")
env = Grid(gamma=0.9)
t0 = time.perf_counter()
V_vi, pi_vi, iters_vi = value_iteration(env)
t_vi = time.perf_counter() - t0
print(f"  收敛迭代 {iters_vi} 次，耗时 {t_vi*1000:.1f}ms")
print("  最优状态价值 V*:")
env.render(V=V_vi)
print("  最优策略:")
env.render(policy=pi_vi)

print("\n== 策略迭代 ==")
t0 = time.perf_counter()
V_pi, pi_pi, rounds_pi = policy_iteration(env)
t_pi = time.perf_counter() - t0
print(f"  策略改进 {rounds_pi} 轮，耗时 {t_pi*1000:.1f}ms")
print("  最优策略:")
env.render(policy=pi_pi)

print("\n== 两种算法结果一致性 ==")
max_diff = max(abs(V_vi[s] - V_pi[s]) for s in env.states)
policy_diff = sum(pi_vi[s] != pi_pi[s] for s in pi_vi)
print(f"  V* 最大差={max_diff:.2e}（应≈0）  策略不同状态数={policy_diff}")
print(f"  V(start)={V_vi[env.start]:.3f}  V(goal旁)={V_vi[(0,2)]:.3f}")

print("\n== 从起点按最优策略走 ==")
s = env.start
path = [s]
for _ in range(10):
    if env.terminal(s):
        break
    a = pi_vi[s]
    tr = env.transitions(s, a)
    s, r, done = tr[0][1], tr[0][2], tr[0][3]
    path.append(s)
    if done:
        break
print("  路径:", " -> ".join(str(p) for p in path))
print(f"  步数={len(path)-1}，到终点={s == env.goal}")

print("\n== γ 对最优策略的影响 ==")
for g in (0.1, 0.5, 0.9, 0.99):
    e = Grid(gamma=g)
    V, pol, _ = value_iteration(e)
    s, steps = e.start, 0
    while not e.terminal(s) and steps < 20:
        s = e.transitions(s, pol[s])[0][1]
        steps += 1
    print(f"  γ={g:<5}: V(start)={V[e.start]:>8.2f} 到终点步数={steps}")

print("\n== 步数惩罚的影响 ==")
for cost in (0.0, -0.1, -1.0, -5.0):
    e = Grid(step_cost=cost)
    V, pol, _ = value_iteration(e)
    s, steps = e.start, 0
    while not e.terminal(s) and steps < 30:
        s = e.transitions(s, pol[s])[0][1]
        steps += 1
    print(f"  每步 {cost:>5}: 到终点步数={steps}（惩罚越重越倾向短路）")

print("\n== 复杂度与收敛 ==")
for line in (
    "  VI 每轮 O(|S|·|A|·|S'|)，但通常要几百轮才收敛",
    "  PI 每轮要解线性/迭代评估，但策略改进轮数常 <10",
    "  广义策略迭代 GPI：评估与改进都不必等到完全收敛",
    "  γ→1 时压缩因子变差，收敛显著变慢",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 实现「修正策略迭代」：评估只做 K 步就改进，观察总计算量。
# 2. 在 8x8 网格上对比 VI/PI 的迭代次数与耗时。
# 3. 给环境加随机 slip，用期望转移重算最优策略并对比确定性策略。
# 4. 思考：为什么 γ<1 能保证贝尔曼算子是压缩映射？
