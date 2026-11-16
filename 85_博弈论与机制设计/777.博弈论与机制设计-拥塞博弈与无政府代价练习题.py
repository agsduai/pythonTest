# ===== 第777课：博弈论与机制设计-拥塞博弈与无政府代价 =====
# 知识点：
#   - 拥塞博弈：玩家选路径/资源，成本随使用人数上升（路由、网络、交通）
#   - Rosenthal 势函数：拥塞博弈是势博弈，纯策略纳什均衡必存在且可用最优反应动力学求出
#   - 无政府代价 Price of Anarchy：最差均衡总成本 / 社会最优总成本
#   - Pigou 例子（两条边：常数成本 1 与线性成本 x）：PoA = 4/3（仿射成本函数上界）
#   - Braess 悖论：加一条「零成本」新路反而让所有人的均衡变差
#   - 与第771课 NE、第776课外部性串联：自私路由把拥塞外部性忽略了
# 依赖：无（标准库）

print("== Pigou 网络：两条并行边 ==")
# 源点 S 到终点 T，1 单位流量（连续）或 n 个离散玩家
# 上边成本恒为 1，下边成本 = x（x 为走下边的比例）
def pigou_cost(x):
    return x*1 + (1-x)*1          # 上边 x 人各付 1，下边 (1-x) 人各付 (1-x)
# 用「下边比例 y」表述：上边 1-y 人、下边 y 人
def total_cost(y):
    return (1-y)*1 + y*y
def individual_lower(y):
    return y                     # 走下边的边际成本

print(f"  {'下边比例 y':<12}{'总成本':<10}{'走下边者成本':<14}")
for y in (0.0, 0.25, 0.5, 0.75, 1.0):
    print(f"  {y:<12.2f}{total_cost(y):<10.4f}{individual_lower(y):<14.4f}")

# NE: 下边成本 y = 上边成本 1 -> y=1 (所有人走下边) 是边界均衡
# 社会最优: min (1-y) + y² -> 导数 -1+2y=0 -> y=0.5
y_ne, y_so = 1.0, 0.5
c_ne, c_so = total_cost(y_ne), total_cost(y_so)
print(f"\n  纳什均衡: y={y_ne}, 总成本={c_ne:.4f}")
print(f"  社会最优: y={y_so}, 总成本={c_so:.4f}")
print(f"  PoA = {c_ne/c_so:.4f} = 4/3（仿射延迟函数的紧上界）")

print("\n== Braess 悖论 ==")
# 经典网络：S->A 成本 x, A->T 成本 1 ; S->B 成本 1, B->T 成本 x
# 无捷径时两条路对称，各分一半，总成本 1.5
# 加一条 A->B 零成本边后，所有人都走 S->A->B->T，成本 2
def braess_without_shortcut(split=0.5):
    # 上路 S-A-T: x + 1 ; 下路 S-B-T: 1 + x
    # 对称均衡各 0.5，每条路成本 1.5
    return 1.5
def braess_with_shortcut():
    # 新均衡：全走 S->A(成本1)->B(免费)->T(成本1) = 2
    return 2.0
print(f"  无捷径: 均衡每人成本={braess_without_shortcut():.2f}")
print(f"  加零成本捷径 A->B 后: 均衡每人成本={braess_with_shortcut():.2f}")
print(f"  变差 {braess_with_shortcut()/braess_without_shortcut()-1:.0%} -> 修路反而更堵")
print("  原因：个体只算自己的路，忽略给同路其他人增加的拥塞外部性")

print("\n== 离散拥塞博弈：最优反应动力学求 NE ==")
# 3 个玩家，4 条资源边，每个玩家有 2 条可选路径（各含 2 条边）
# 资源成本：c_r(k) = k（使用人数线性）
RESOURCES = ["e1","e2","e3","e4","e5"]
PATHS = [
    {"上": ["e1","e2"], "下": ["e3","e2"]},        # 玩家1
    {"上": ["e1","e4"], "下": ["e3","e5"]},        # 玩家2
    {"上": ["e1","e5"], "下": ["e4","e2"]},        # 玩家3
]

def cost_of(choices):
    """社会总成本 = Σ_r load_r · c_r(load_r)，这里 c_r(k)=k。"""
    loads = {}
    for path in choices.values():
        for r in path: loads[r] = loads.get(r,0)+1
    return sum(loads[r]*loads[r] for r in loads)

def path_cost(path, loads):
    """个人成本 = 路径上各资源的当前负载之和。"""
    return sum(loads.get(r, 0) for r in path)

def best_response_dynamics(seed=0, max_iter=50):
    import random
    rng = random.Random(seed)
    choices = {i: rng.choice(list(PATHS[i].values())) for i in range(len(PATHS))}
    for step in range(max_iter):
        changed = False
        for i in range(len(PATHS)):
            # 关键：评估候选路径时先移除玩家自己的贡献，
            # 否则「自己给自己加的拥塞」会造成伪改进与震荡
            loads = {}
            for j, p in choices.items():
                if j == i: continue
                for r in p: loads[r] = loads.get(r,0)+1
            cur = path_cost(choices[i], loads) + len(choices[i])
            best_name, best_v = None, cur
            for name, path in PATHS[i].items():
                # 候选成本 = 他人负载 + 自己在候选路径每条边上的贡献 1
                alt = path_cost(path, loads) + len(path)
                if alt < best_v:
                    best_name, best_v = name, alt
            if best_name is not None:
                choices[i] = PATHS[i][best_name]; changed = True
        if not changed:
            return choices, step+1
    return choices, max_iter

for seed in range(5):
    ch, iters = best_response_dynamics(seed)
    print(f"  seed={seed}: {iters} 轮收敛, 总成本={cost_of(ch)}, "
          f"选择={[list(PATHS[i].keys())[list(PATHS[i].values()).index(ch[i])] for i in range(3)]}")
print("  势博弈保证最优反应动力学收敛到纯策略 NE（Rosenthal 势函数单调下降）")

print("\n== 势函数 ==")
for line in (
    "  Φ(s) = Σ_r Σ_{k=1}^{load_r} c_r(k)",
    "  单个玩家改选路径时，Φ 的变化恰好等于他个人成本的变化",
    "  Φ 有下界且每次改进严格下降 -> 必然收敛到局部最小 = 纯 NE",
    "  这解释了为什么拥塞博弈比一般博弈「好求」",
):
    print(" ", line)

print("\n== PoA 上界速查 ==")
print(f"  {'成本函数类':<20}{'PoA 上界':<12}{'例子'}")
for row in (("仿射 ax+b", "4/3", "Pigou 线性"),
            ("多项式 次数 p", "Θ(p/log p)", "高次拥塞"),
            ("任意非减", "无界", "需机制干预")):
    print(f"  {row[0]:<20}{row[1]:<12}{row[2]}")

print("\n== 缓解手段 ==")
for line in [
    "  拥塞定价：按边际外部性收费，把 NE 拉回社会最优（第776课庇古税）",
    "  限流/配额、预约制、错峰激励",
    "  信息设计：不完全信息下引导流量（Bayesian persuasion）",
    "  网络设计：避免制造 Braess 悖论结构",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 用线性规划求 Pigou 网络的社会最优流，验证 y=0.5。
# 2. 构造一个 4 玩家 Braess 网络，数值验证加边后均衡变差。
# 3. 实现 Rosenthal 势函数并验证每次最优反应改进都使其下降。
# 4. 思考：为什么「加一条免费路」反而可能让所有人更慢？
