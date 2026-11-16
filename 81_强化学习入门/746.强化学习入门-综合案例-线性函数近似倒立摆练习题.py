# ===== 第746课：强化学习入门-综合案例-线性函数近似倒立摆 =====
# 知识点：
#   - 综合串起本章：MDP 环境 -> 探索利用 -> TD/Q-learning -> 函数近似 -> 评估
#   - 表格 Q 在连续状态上不可行，用线性函数近似 Q(s,a) = w_a · φ(s)
#   - 特征工程：位置/速度/角度/角速度 + 归一化 + 交互项（瓦片编码思路）
#   - 半梯度 SGD：w += α·δ·∇_w Q = α·δ·φ(s)，目标用自举（不对其求梯度）
#   - 简化 CartPole：状态 4 维，动作左右推力，杆倒下或出界即终止
#   - 可注入 rng、固定 seed、纯标准库；报告训练曲线与最终存活步数
# 依赖：无（标准库）
import math
import random
import statistics

LEFT, RIGHT = 0, 1
ACTIONS = [LEFT, RIGHT]
G = 9.8
MASS_CART, MASS_POLE = 1.0, 0.1
LENGTH, FORCE, DT = 0.5, 10.0, 0.02
TOTAL_MASS = MASS_CART + MASS_POLE


class CartPole:
    """简化倒立摆：状态 (x, x_dot, theta, theta_dot)。"""

    def __init__(self, seed=0):
        self.rng = random.Random(seed)
        self.reset()

    def reset(self):
        self.s = [self.rng.uniform(-0.05, 0.05) for _ in range(4)]
        self.steps = 0
        return list(self.s)

    def step(self, a):
        x, xd, th, thd = self.s
        f = FORCE if a == RIGHT else -FORCE
        costh, sinth = math.cos(th), math.sin(th)
        temp = (f + MASS_POLE * LENGTH * thd * thd * sinth) / TOTAL_MASS
        thacc = (G * sinth - costh * temp) / (
            LENGTH * (4/3 - MASS_POLE * costh * costh / TOTAL_MASS))
        xacc = temp - MASS_POLE * LENGTH * thacc * costh / TOTAL_MASS
        x = x + DT * xd
        xd = xd + DT * xacc
        th = th + DT * thd
        thd = thd + DT * thacc
        self.s = [x, xd, th, thd]
        self.steps += 1
        done = (abs(x) > 2.4 or abs(th) > 0.2095 or self.steps >= 200)
        reward = 1.0 if not done else 0.0
        return list(self.s), reward, done


def features(s):
    """手工特征：归一化状态 + 符号交互 + 常数项。"""
    x, xd, th, thd = s
    return [
        1.0,
        x / 2.4, xd / 3.0, th / 0.21, thd / 3.0,
        math.tanh(xd), math.tanh(thd),
        (1.0 if th * thd > 0 else -1.0),        # 角速度与角度同向 = 更危险
        abs(th) / 0.21, (1.0 if x * xd > 0 else -1.0),
    ]


class LinearQ:
    """每个动作一组线性权重；Q(s,a) = w_a · φ(s)。"""

    def __init__(self, n_features, n_actions=2, seed=0):
        rng = random.Random(seed)
        self.w = [[rng.uniform(-0.01, 0.01) for _ in range(n_features)]
                  for _ in range(n_actions)]

    def q(self, phi, a):
        return sum(wi * fi for wi, fi in zip(self.w[a], phi))

    def values(self, phi):
        return [self.q(phi, a) for a in ACTIONS]

    def update(self, phi, a, delta, alpha):
        for i, fi in enumerate(phi):
            self.w[a][i] += alpha * delta * fi


def eps_greedy(q, phi, eps, rng):
    if rng.random() < eps:
        return rng.randrange(2)
    vals = q.values(phi)
    return 0 if vals[0] >= vals[1] else 1


def train(episodes=600, alpha=0.01, gamma=0.99, eps0=0.3,
          decay=0.995, seed=7):
    env = CartPole(seed=seed)
    rng = random.Random(seed + 100)
    q = LinearQ(len(features(env.s)), seed=seed)
    lengths = []
    for ep in range(episodes):
        eps = max(0.01, eps0 * decay ** ep)
        s = env.reset()
        phi = features(s)
        for t in range(200):
            a = eps_greedy(q, phi, eps, rng)
            ns, r, done = env.step(a)
            nphi = features(ns)
            # 半梯度：目标用自举，不对目标求梯度
            target = r + (0.0 if done else gamma * max(q.values(nphi)))
            delta = target - q.q(phi, a)
            q.update(phi, a, delta, alpha)
            phi = nphi
            if done:
                break
        lengths.append(env.steps)
    return q, lengths


def evaluate(q, episodes=20, seed=99):
    scores = []
    for i in range(episodes):
        env = CartPole(seed=seed + i)
        s = env.reset()
        for _ in range(200):
            a = 0 if q.q(features(s), 0) >= q.q(features(s), 1) else 1
            s, r, done = env.step(a)
            if done:
                break
        scores.append(env.steps)
    return scores


print("== 环境 ==")
env = CartPole(seed=1)
print("  状态 (x, x_dot, theta, theta_dot)，动作 左/右推力")
print(f"  终止条件: |x|>2.4 或 |θ|>0.2095 rad 或 200 步；每存活一步 +1")
print(f"  特征维度: {len(features(env.s))}（含归一化、tanh、符号交互项）")

print("\n== 训练线性 Q（600 回合）==")
q, lengths = train(episodes=600, seed=7)
print(f"  前50回合均存活={statistics.fmean(lengths[:50]):.1f} 步")
print(f"  后50回合均存活={statistics.fmean(lengths[-50:]):.1f} 步")
curve = [round(statistics.fmean(lengths[i:i+60]), 1) for i in range(0, 600, 60)]
print(f"  学习曲线(每60回合): {curve}")

print("\n== 贪心策略评估（20 个新种子）==")
scores = evaluate(q, episodes=20)
print(f"  平均={statistics.fmean(scores):.1f} 步, 中位={statistics.median(scores):.1f}, "
      f"最好={max(scores)}, 最差={min(scores)}")
print(f"  达到满贯(200步)的比例: {sum(s >= 200 for s in scores)/len(scores):.0%}")

print("\n== 与随机策略对照 ==")
rng = random.Random(0)
rand_scores = []
for i in range(20):
    e = CartPole(seed=500+i)
    for _ in range(200):
        _, _, done = e.step(rng.randrange(2))
        if done: break
    rand_scores.append(e.steps)
print(f"  随机策略平均存活={statistics.fmean(rand_scores):.1f} 步")
print(f"  学到的策略提升约 {statistics.fmean(scores)/statistics.fmean(rand_scores):.1f}×")

print("\n== 学到的权重（动作 右 - 左 的差）==")
phi = features([0.0, 0.0, 0.05, 0.0])
diff = [q.w[RIGHT][i] - q.w[LEFT][i] for i in range(len(phi))]
print("  ", [round(d, 3) for d in diff])
print("  角度为正时若偏好右推，说明学到了「往倒的方向推」的基本控制律")

print("\n== 超参敏感性 ==")
for alpha in (0.001, 0.01, 0.05, 0.2):
    q2, lens = train(episodes=300, alpha=alpha, seed=3)
    sc = evaluate(q2, episodes=10, seed=77)
    print(f"  α={alpha:<6}: 后50训练均存活={statistics.fmean(lens[-50:]):>6.1f} "
          f"评估均存活={statistics.fmean(sc):>6.1f}")
print("  线性近似下半梯度不保证收敛，α 与特征缩放尤其关键")

print("\n== 表格法 vs 函数近似 ==")
for line in (
    "  表格法: 每 (s,a) 独立存储，小离散状态精确、可证收敛",
    "  函数近似: 参数共享、能泛化到未见状态，连续状态必需",
    "  致命三要素(deadly triad): 自举 + 离线 + 函数近似 同时存在可能发散",
    "  DQN 用经验回放 + 目标网络缓解；本课用小规模 + 好特征避开",
):
    print(" ", line)

print("\n== 分层回顾 ==")
for line in [
    "  环境层  : MDP 建模与终止条件（第739课）",
    "  探索层  : ε-greedy 衰减（第741课）",
    "  学习层  : TD 半梯度 Q-learning（第742/743课）",
    "  表示层  : 线性函数近似 + 手工特征（本课）",
    "  策略层  : 由 Q 贪心导出；也可改策略梯度（第744/745课）",
    "  评估层  : 独立种子、多次平均、与随机基线对照",
]:
    print("  -", line)

print("\n== 局限 ==")
for line in [
    "  这是极度简化的 CartPole，不是 gym 的标准物理参数",
    "  纯线性 + 手工特征，未用神经网络/经验回放/目标网络",
    "  真实 RL 还要处理奖励缩放、种子方差、超参搜索",
    "  目标是把本章概念串成一条可运行的完整链路",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 加入经验回放缓冲区，观察样本效率与训练稳定性变化。
# 2. 用瓦片编码/径向基特征替代手工特征，对比最终存活步数。
# 3. 实现 Double Q（两组权重交替选动作与评估），缓解最大化偏差。
# 4. 思考：为什么半梯度更新里「目标值」不能对权重求梯度？
