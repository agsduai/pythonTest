# ===== 第887课：概率图模型与结构化推断-信念传播与和积算法 =====
# 知识点：
#   - 因子图 = 变量节点 + 因子节点的二部图，统一表达乘积分布 P(x) ∝ Π φ
#   - 树/链状因子图上，和积（sum-product）消息传递给出精确边缘
#   - 消息 = 「聚合了子树全部信息」的边缘近似 —— 动态规划式复用
#   - 边缘 = 归一化的（所有到达该变量的消息之积）—— 两遍扫描完成
#   - 有环图上 BP 只是近似（Loopy BP）：消息循环计数证据 -> 过度自信
# 依赖：无（标准库）
from itertools import product as iproduct

DOMAIN = ("T", "F")


def enumerate_marginals(factors, query):
    """暴力枚举求 P(query) 作真值。factors: [(vars, table)]。"""
    all_vars = sorted({v for f in factors for v in f[0]})
    raw = {v: 0.0 for v in DOMAIN}
    for combo in iproduct(DOMAIN, repeat=len(all_vars)):
        a = dict(zip(all_vars, combo))
        p = 1.0
        for fvars, table in factors:
            p *= table[tuple(a[v] for v in fvars)]
        raw[a[query]] += p
    total = sum(raw.values())
    return {v: val / total for v, val in raw.items()}


def sum_product_chain(prior, pairwise, leaf=None):
    """链 x0 -φ1- x1 -φ2- x2 ... 上两遍消息传递求每个节点的边缘。
    prior: x0 的 unary 分布；pairwise: n-1 张两两因子表；
    leaf: 最右端节点的位势（可当软证据），缺省全 1。"""
    n = len(pairwise) + 1
    msgs_f2v = [None] * (n - 1)          # φ_{i+1} -> x_i？编号：msgs_f2v[k] = 进入 x_{k+1} 的左向消息
    msgs_f2l = [None] * (n - 1)          # msgs_f2l[k] = 进入 x_k 的右向消息
    # ---- 前向（左 -> 右）----
    msg_right = dict(prior)              # x0 的 unary 作为第一份消息
    for i in range(1, n):
        m = {}
        for xi in DOMAIN:
            s = 0.0
            for xl in DOMAIN:
                s += msg_right[xl] * pairwise[i - 1][(xl, xi)]
            m[xi] = s
        msgs_f2v[i - 1] = m
        msg_right = m
    # ---- 后向（右 -> 左）----
    msg_left = dict(leaf) if leaf else {v: 1.0 for v in DOMAIN}  # 最右端位势
    for i in range(n - 1, 0, -1):
        m = {}
        for xl in DOMAIN:
            s = 0.0
            for xi in DOMAIN:
                s += msg_left[xi] * pairwise[i - 1][(xl, xi)]
            m[xl] = s
        msgs_f2l[i - 1] = m              # 进入 x_{i-1} 的右向消息
        msg_left = m
    # ---- 边缘 = 两份消息之积 ----
    ones = {v: 1.0 for v in DOMAIN}
    marginals = []
    for i in range(n):
        left = dict(prior) if i == 0 else msgs_f2v[i - 1]
        right = (leaf if leaf else ones) if i == n - 1 else msgs_f2l[i]
        belief = {v: left[v] * right[v] for v in DOMAIN}
        marginals.append(belief)
    for m in marginals:
        total = sum(m.values())
        for v in m:
            m[v] /= total
    return marginals, msgs_f2v, msgs_f2l


def loopy_bp(factors_map, adj, iters):
    """环状 pairwise MRF 的 Loopy BP。
    adj[v] = [(w, rel)]，rel 的键为 (x_v, x_w)。"""
    msg, rel_of = {}, {}
    for v in adj:
        for w, rel in adj[v]:
            msg[(v, w)] = {d: 1.0 for d in DOMAIN}
            rel_of[(v, w)] = rel
    for _ in range(iters):
        new_msg = {}
        for v in adj:
            for w, _ in adj[v]:
                m = {}
                for dw in DOMAIN:
                    s = 0.0
                    for dv in DOMAIN:
                        prod = factors_map[v][dv]
                        for u, _ in adj[v]:
                            if u == w:
                                continue
                            prod *= msg[(u, v)][dv]
                        s += prod * rel_of[(v, w)][(dv, dw)]
                    m[dw] = s
                total = sum(m.values())
                new_msg[(v, w)] = {d: m[d] / total for d in DOMAIN}
        msg = new_msg
    beliefs = {}
    for v in adj:
        b = {}
        for dv in DOMAIN:
            prod = factors_map[v][dv]
            for u, _ in adj[v]:
                prod *= msg[(u, v)][dv]
            b[dv] = prod
        total = sum(b.values())
        beliefs[v] = {d: b[d] / total for d in DOMAIN}
    return beliefs


print("== 链式因子图 ==")
prior = {"T": 0.6, "F": 0.4}                       # ψ0(x0)
pairwise = [{("T", "T"): 0.8, ("T", "F"): 0.2,
             ("F", "T"): 0.1, ("F", "F"): 0.9},
            {("T", "T"): 0.9, ("T", "F"): 0.1,
             ("F", "T"): 0.3, ("F", "F"): 0.7},
            {("T", "T"): 0.7, ("T", "F"): 0.3,
             ("F", "T"): 0.2, ("F", "F"): 0.8}]
marginals, f2v, f2l = sum_product_chain(prior, pairwise, leaf={"T": 3.0, "F": 1.0})
print("  x0 --φ1-- x1 --φ2-- x2 --φ3-- x3（x3 带软证据位势 3:1）")
chain_factors = [(("x0",), {("T",): 0.6, ("F",): 0.4})] + [(("x0", "x1"), pairwise[0]),
                                                           (("x1", "x2"), pairwise[1]),
                                                           (("x2", "x3"), pairwise[2]),
                                                           (("x3",), {("T",): 3.0, ("F",): 1.0})]
print(f"  {'节点':>6}{'BP边缘 P(T)':>14}{'枚举真值':>12}")
agree = True
for i in range(4):
    truth_i = enumerate_marginals(chain_factors, f"x{i}")
    agree = agree and abs(marginals[i]["T"] - truth_i["T"]) < 1e-9
    print(f"  x{i:<5}{marginals[i]['T']:>14.4f}{truth_i['T']:>12.4f}")
print(f"  树上 BP 与枚举完全一致: {agree} —— 无环时两遍消息即精确推断")

print("\n== 中间消息的样子 ==")
print(f"  φ1 聚合 x0 后发给 x1 的消息: {f2v[0]}")
print(f"  右侧子树聚合后发给 x1 的消息: {f2l[1]}")
print("  每条消息已『消化』一个子树 —— 指数求和被复用成线性传递")

print("\n== 有环图：Loopy BP 只是近似 ==")
# 三角环，共享因子按方向转置，保证 φ 是同一个函数
phi01 = {("T", "T"): 0.9, ("T", "F"): 0.1, ("F", "T"): 0.2, ("F", "F"): 0.8}
phi01r = {(a, b): phi01[(b, a)] for (a, b) in phi01}
phi02 = {("T", "T"): 0.85, ("T", "F"): 0.15, ("F", "T"): 0.25, ("F", "F"): 0.75}
phi02r = {(a, b): phi02[(b, a)] for (a, b) in phi02}
phi12 = {("T", "T"): 0.8, ("T", "F"): 0.2, ("F", "T"): 0.1, ("F", "F"): 0.9}
phi12r = {(a, b): phi12[(b, a)] for (a, b) in phi12}
unary = {"x0": {"T": 1.0, "F": 1.0}, "x1": {"T": 1.0, "F": 1.0},
         "x2": {"T": 1.0, "F": 1.0}}
adj = {"x0": [("x1", phi01), ("x2", phi02)],
       "x1": [("x0", phi01r), ("x2", phi12)],
       "x2": [("x0", phi02r), ("x1", phi12r)]}
beliefs = loopy_bp(unary, adj, iters=40)
tri_factors = [(("x0", "x1"), phi01), (("x0", "x2"), phi02),
               (("x1", "x2"), phi12)]
print(f"  {'节点':>6}{'LBP边缘 P(T)':>14}{'枚举真值':>12}{'偏差':>10}")
for v in ("x0", "x1", "x2"):
    truth_v = enumerate_marginals(tri_factors, v)
    print(f"  {v:<6}{beliefs[v]['T']:>14.4f}{truth_v['T']:>12.4f}"
          f"{abs(beliefs[v]['T'] - truth_v['T']):>10.4f}")
print("  环让消息反复绕行、重复计数同一证据 -> 边缘偏锐（过度自信）")
print("  工程上 LBP 仍广泛使用（LDPC 纠错码）：快、往往够用、无收敛保证")

print("\n== 消息传递 vs 变量消元 ==")
for line in (
    "  数学上等价：BP = 消元顺序最优化的 VE，只是组织成分布式消息",
    "  BP 的优点：每个节点只需与邻居通信 -> 天然分布式/流式实现",
    "  max-product 变体（Σ 换 max）给出 MAP，与 Viterbi 同源",
    "  888 课：反过来 —— 从数据里把图结构学出来",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 把链上 sum-product 改成 max-product + 回溯，输出 MAP 配置并与枚举对比。
# 2. 实现 4 节点星形因子图的 BP，验证与枚举一致。
# 3. 给 LBP 加阻尼：新消息 = λ·新 + (1-λ)·旧，观察三角环上的收敛性变化。
# 4. 思考：为什么环会让 BP 过度自信？「同一证据被计数多次」的本质是什么？
