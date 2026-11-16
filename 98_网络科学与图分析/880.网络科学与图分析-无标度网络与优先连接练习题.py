# ===== 第880课：网络科学与图分析-无标度网络与优先连接 =====
# 知识点：
#   - 真实网络的度分布是幂律：P(k) ∝ k^-γ（γ≈2~3），极度右偏
#   - Barabási–Albert 模型：增长 + 优先连接（富者愈富）-> 幂律涌现
#   - 新节点按度加权选 m 个目标连接：度大者更可能被新节点选中
#   - BA 的 hub 度 ~ n^0.5，远超 ER 的 np±波动 —— 枢纽是结构性的
#   - 幂律意味着「均值没意义」：少数枢纽承担绝大多数连接
# 依赖：无（标准库）
import math
import random


def ba_graph(n, m, rng, m0=5):
    adj = {i: set() for i in range(m0)}
    for i in range(m0):
        adj[i].add((i + 1) % m0)
        adj[(i + 1) % m0].add(i)
    for v in range(m0, n):
        adj[v] = set()                              # 新节点先入图
        weighted = []
        for u in adj:
            weighted.extend([u] * len(adj[u]))      # 度加权抽样池
        chosen = set()
        while len(chosen) < m:
            w = rng.choice(weighted)
            if w != v:
                chosen.add(w)
        for w in chosen:
            adj[v].add(w)
            adj[w].add(v)
    return adj


def er_graph(n, p, rng):
    adj = {i: set() for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def degree_hist(adj):
    hist = {}
    for v in adj:
        hist[len(adj[v])] = hist.get(len(adj[v]), 0) + 1
    return hist


def clustering(adj):
    total, cnt = 0.0, 0
    for v, nb in adj.items():
        if len(nb) < 2:
            continue
        links = sum(1 for a in nb for b in nb if a < b and b in adj[a])
        total += 2 * links / (len(nb) * (len(nb) - 1))
        cnt += 1
    return total / cnt if cnt else 0.0


def slope_loglog(hist, k_min=3):
    """对尾部做 log-log 最小二乘，估幂指数 γ 的负值。"""
    pts = [(math.log(k), math.log(c / sum(hist.values())))
           for k, c in sorted(hist.items()) if k >= k_min]
    if len(pts) < 3:
        return None
    n = len(pts)
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    sxy = sum(p[0] * p[1] for p in pts)
    sxx = sum(p[0] * p[0] for p in pts)
    return (n * sxy - sx * sy) / (n * sxx - sx * sx)


rng = random.Random(10)
n, m = 500, 2

print("== 生成 BA 无标度网络 ==")
ba = ba_graph(n, m, rng)
avg_deg = sum(len(v) for v in ba.values()) / n
er = er_graph(n, avg_deg / n, rng)
print(f"  BA: n={n}, m={m}（每新节点连 2 条），平均度 = {avg_deg:.2f}")
print(f"  同平均度的 ER 图作为对照")

print("\n== 枢纽对比 ==")
ba_degs = sorted((len(v) for v in ba.values()), reverse=True)
er_degs = sorted((len(v) for v in er.values()), reverse=True)
print(f"  {'指标':<16}{'BA':>8}{'ER':>8}")
print(f"  {'最大度':<16}{ba_degs[0]:>8}{er_degs[0]:>8}")
print(f"  {'前10度之和占比':<16}{sum(ba_degs[:10]) / sum(ba_degs):>8.1%}"
      f"{sum(er_degs[:10]) / sum(er_degs):>8.1%}")
print(f"  {'平均聚类系数':<16}{clustering(ba):>8.3f}{clustering(er):>8.3f}")
print("  BA 的 hub 度是 ER 的数倍；前 10 节点承担远超比例的连接")

print("\n== 度分布直方图（对数观感）==")
hist = degree_hist(ba)
peak = max(hist[k] for k in hist if k >= 1)
print("  度  计数(条形按对数尺度)")
for k in sorted(hist):
    if hist[k] >= 1:
        bar_len = int(math.log(hist[k] + 1) / math.log(peak + 1) * 40)
        print(f"  {k:>3} {bar_len:>40} {hist[k]}")
print("  长尾：绝大多数节点度很小，极少数 hub 度极大")

print("\n== 幂指数估计 ==")
gamma_est = slope_loglog(hist, k_min=3)
print(f"  BA 理论 γ = 3.0（P(k) ∝ k^-3）")
print(f"  实测 log-log 斜率 = {gamma_est:.2f}（小样本+尾部噪声，量级吻合即可）")
er_hist = degree_hist(er)
er_slope = slope_loglog(er_hist, k_min=3)
print(f"  ER 对照的斜率 = {er_slope if er_slope is None else f'{er_slope:.2f}'}"
      f"（泊松尾部衰减远快于幂律，拟合无意义）")

print("\n== 优先连接的直接验证 ==")
m_test = 3
ba2 = ba_graph(n, m_test, rng)
new_node_degree_pref = []
rng2 = random.Random(11)
adj = {i: set() for i in range(5)}
for i in range(5):
    adj[i].add((i + 1) % 5)
    adj[(i + 1) % 5].add(i)
hits_by_rank = {0: 0, 1: 0, 2: 0}
trials = 300
for _ in range(trials):
    weighted = []
    for u in adj:
        weighted.extend([u] * len(adj[u]))
    ranked = sorted(set(weighted), key=lambda u: -len(adj[u]))
    chosen = set()
    while len(chosen) < m_test:
        w = rng2.choice(weighted)
        chosen.add(w)
    for target in chosen:
        rank = ranked.index(target)
        if rank < 3:
            hits_by_rank[rank] += 1
total_hits = sum(hits_by_rank.values())
print(f"  新连接落在『度排名前3』节点的比例 = {total_hits / trials / m_test:.1%}")
for rank in hits_by_rank:
    share = hits_by_rank[rank] / total_hits
    deg_share = len(adj[ranked[rank]]) / sum(len(adj[r]) for r in ranked[:3])
    print(f"  度排名 {rank}: 获新边占比 {share:.1%}（其度占比 {deg_share:.1%}）")
print("  新连接近似按度比例分配 —— 优先连接机制的直接证据")

print("\n== hub 的鲁棒性与脆弱性 ==")
print(f"  {'移除策略':<22}{'最大分量占比':>12}")
seen, best = set(), 0
for s in ba:
    if s in seen:
        continue
    comp, stack = {s}, [s]
    while stack:
        v = stack.pop()
        for w in ba[v]:
            if w not in comp:
                comp.add(w)
                stack.append(w)
    seen |= comp
    best = max(best, len(comp))
print(f"  {'（原始）':<22}{best / n:>12.1%}")
sorted_by_deg = sorted(ba, key=lambda v: -len(ba[v]))
g = {v: set(nb) for v, nb in ba.items()}
for victim in sorted_by_deg[:3]:
    for v in g:
        g[v].discard(victim)
    g = {v: nb for v, nb in g.items() if v != victim}
seen2, best2 = set(), 0
for s in g:
    if s in seen2:
        continue
    comp, stack = {s}, [s]
    while stack:
        v = stack.pop()
        for w in g[v]:
            if w not in comp:
                comp.add(w)
                stack.append(w)
    seen2 |= comp
    best2 = max(best2, len(comp))
print(f"  {'移除度最高的3个hub':<22}{best2 / n:>12.1%}")
print("  无标度网络对随机故障鲁棒、对定向攻击脆弱 —— 一体两面")

print("\n== 小结 ==")
for line in (
    "  增长 + 优先连接两条简单规则涌现出幂律 —— 无需中央设计",
    "  幂律网络的统计要换视角：均值/方差被 hub 主导，应看秩-度曲线",
    "  hub 带来高效传播（信息/病毒）也带来攻击脆弱性",
    "  下一课：用这些结构特征预测『还没发生的连接』",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「初始吸引度」变体：A(α) 模型给每个节点加常数 α 抑制富者愈富，
#    观察 γ 随 α 变化。
# 2. 实现 k-着色网络鲁棒性曲线：按度从高到低逐个移除 hub，画出最大分量占比
#    的崩塌曲线；与随机移除对照。
# 3. 用 875 课的秩-度（log-log）散点对比 BA 与 ER 的尾部形状。
# 4. 思考：为什么互联网拓扑（AS 级）是幂律但电网不是？优先连接在什么条件
#    下失效？
