# ===== 第745课：强化学习入门-Actor-Critic 与优势函数 =====
# 知识点：
#   - Actor-Critic：Actor 管策略 π(a|s;θ)，Critic 学价值 V(s;w) 当基线
#   - 优势函数 A(s,a) = Q(s,a) - V(s)：这个动作比平均水平好多少
#   - 用 TD 误差 δ = r + γV(s') - V(s) 估计优势（一步自举），无需等回合结束
#   - 更新：θ += α·δ·∇logπ(a|s)；w += β·δ·∇V(s)（表格时 ∇V=1）
#   - 相比 REINFORCE：方差低、可在线逐步更新；引入自举偏差
#   - GAE(λ)：把多步 TD 误差按 λ 加权，平衡偏差与方差
# 依赖：无（标准库）
import math
import random
from collections import defaultdict

UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3
ACTIONS = [UP, DOWN, LEFT, RIGHT]
DELTAS = {UP:(-1,0), DOWN:(1,0), LEFT:(0,-1), RIGHT:(0,1)}
ARROWS = {UP:"↑", DOWN:"↓", LEFT:"←", RIGHT:"→"}


class Grid:
    def __init__(self, n=5, seed=0):
        self.n = n; self.start=(0,0); self.goal=(n-1,n-1)
        self.rng = random.Random(seed); self.reset()
    def reset(self): self.pos=self.start; return self.pos
    def step(self, a):
        dr,dc = DELTAS[a]; r,c = self.pos
        nr,nc = max(0,min(self.n-1,r+dr)), max(0,min(self.n-1,c+dc))
        self.pos=(nr,nc)
        if self.pos==self.goal: return self.pos, 10.0, True
        return self.pos, -1.0, False
    def states(self): return [(r,c) for r in range(self.n) for c in range(self.n)]


def softmax(xs):
    m=max(xs); e=[math.exp(x-m) for x in xs]; s=sum(e)
    return [v/s for v in e]

def sample(p, rng):
    u=rng.random(); acc=0.0
    for i,v in enumerate(p):
        acc+=v
        if u<acc: return i
    return len(p)-1


def actor_critic(episodes=1500, alpha=0.1, beta=0.2, gamma=0.95,
                 lam=0.0, seed=7):
    """表格型 Actor-Critic；lam>0 时用 GAE(λ) 累积优势。"""
    env=Grid(seed=seed); rng=random.Random(seed)
    theta=defaultdict(float)                  # actor logits
    V=defaultdict(float)                      # critic
    returns=[]
    for ep in range(episodes):
        s=env.reset(); total=0.0
        traj=[]
        for _ in range(100):
            p=softmax([theta[(s,a)] for a in ACTIONS])
            a=sample(p,rng)
            ns,r,done=env.step(a)
            traj.append((s,a,r,ns,done,p))
            total+=r; s=ns
            if done: break
        returns.append(total)
        # 反向计算 TD 误差与 GAE
        gae=0.0
        for t in range(len(traj)-1,-1,-1):
            s,a,r,ns,done,p=traj[t]
            v_next=0.0 if done else V[ns]
            delta=r+gamma*v_next-V[s]
            gae=gamma*lam*gae+delta
            adv=gae
            # Critic 更新（表格：∂V/∂w = 1）
            V[s]+=beta*adv
            # Actor 更新
            for j,aj in enumerate(ACTIONS):
                grad=(1.0 if aj==a else 0.0)-p[j]
                theta[(s,aj)]+=alpha*adv*grad
    return theta,V,returns,env


def evaluate(theta, env):
    s=env.reset(); path=[s]; total=0.0
    for _ in range(30):
        a=max(ACTIONS,key=lambda x:theta[(s,x)])
        s,r,done=env.step(a)
        path.append(s); total+=r
        if done: break
    return total,len(path)-1,done


print("== 环境 ==")
print("  5x5 网格，起点(0,0) 终点(4,4)，每步 -1，到终点 +10；最优 8 步回报 +3")

print("\n== Actor-Critic：不同 λ（GAE）==")
for lam in (0.0, 0.5, 0.9, 1.0):
    theta,V,rets,env = actor_critic(episodes=1200, lam=lam, seed=3)
    early,late = sum(rets[:100])/100, sum(rets[-100:])/100
    total,steps,done = evaluate(theta,env)
    print(f"  λ={lam:<4}: 前100均回报={early:>7.2f} 后100={late:>7.2f} "
          f"贪心评估={total:>5.1f} 步数={steps} 到终点={done}")

print("\n== Critic 学到的状态价值 V(s) ==")
theta,V,rets,env = actor_critic(episodes=1500, lam=0.9, seed=3)
for r in range(env.n):
    print("   " + " ".join(f"{V[(r,c)]:+6.1f}" for c in range(env.n)))
print("  越靠近终点价值越高，说明 Critic 提供了有意义的基线")

print("\n== 学到的策略 ==")
for r in range(env.n):
    row=[]
    for c in range(env.n):
        s=(r,c)
        row.append("G" if s==env.goal else "S" if s==env.start else
                   ARROWS[max(ACTIONS,key=lambda a:theta[(s,a)])])
    print("   " + " ".join(row))

print("\n== 优势函数与 TD 误差 ==")
print("  δ = r + γV(s') - V(s)")
print("  A(s,a) ≈ δ（一步）或 GAE(λ) = Σ (γλ)^k δ_{t+k}")
for lam in (0, 0.5, 0.9, 1.0):
    kind = "TD(0) 低方差高偏差" if lam==0 else ("近似 MC 高方差低偏差" if lam==1 else "折中")
    print(f"  λ={lam}: {kind}")

print("\n== REINFORCE vs Actor-Critic ==")
for line in (
    "  REINFORCE: 用整回合 G_t，无偏、方差大、必须等回合结束",
    "  AC       : 用 TD 优势，有偏、方差小、可逐步在线更新",
    "  AC 的 Critic 同时充当基线，省掉单独学 baseline 的麻烦",
    "  两者都属于 on-policy；PPO/SAC/TD3 是现代扩展",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  Actor 与 Critic 的学习率要分别调（β 通常 > α）",
    "  价值函数目标要做裁剪/归一化，否则 δ 量级会炸",
    "  共享网络时两个损失要加权，并注意梯度互相干扰",
    "  GAE 的 λ 是最关键的超参之一，常用 0.95",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 n-step Actor-Critic，对比与 GAE(λ) 的方差/收敛速度。
# 2. 给 Critic 换成 TD(λ) 资格迹更新，观察价值估计的平滑度。
# 3. 增加熵正则，防止 Actor 过早收敛到确定性策略。
# 4. 思考：为什么 Critic 的偏差不会让策略梯度方向系统性出错？
