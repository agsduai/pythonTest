# ===== 第875课：网络科学与图分析-图统计与随机图 =====
# 知识点：
#   - 图统计三件套：度分布、聚类系数、连通分量 —— 网络的「体检指标」
#   - 聚类系数 = 朋友的朋友也是朋友的概率（三角闭合倾向）
#   - ER 随机图 G(n,p)：每条边独立以 p 出现 —— 最朴素的网络零假设
#   - 理论对照：平均度 ≈ np、聚类系数 ≈ p、巨连通分量在 np > 1 附近涌现
#   - 真实网络与 ER 的差异（高聚类、幂律度分布）正是 880 课模型的动机
# 依赖：无（标准库）
import random


def er_graph(n, p, rng):
    adj = {i: set() for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def mean_degree(adj):
    return sum(len(v) for v in adj.values()) / len(adj)


def density(adj):
    n = len(adj)
    m = sum(len(v) for v in adj.values()) // 2
    return m / (n * (n - 1) / 2)


def clustering(adj):
    """平均局部聚类系数。"""
    total, cnt = 0.0, 0
    for v, nb in adj.items():
        if len(nb) < 2:
            continue
        links = sum(1 for a in nb for b in nb if a < b and b in adj[a])
        total += 2 * links / (len(nb) * (len(nb) - 1))
        cnt += 1
    return total / cnt if cnt else 0.0


def components(adj):
    seen = set()
    sizes = []
    for s in adj:
        if s in seen:
            continue
        comp, queue = {s}, [s]
        while queue:
            v = queue.pop()
            for w in adj[v]:
                if w not in comp:
                    comp.add(w)
                    queue.append(w)
        seen |= comp
        sizes.append(len(comp))
    return sorted(sizes, reverse=True)


def degree_dist(adj):
    hist = {}
    for v in adj:
        hist[len(adj[v])] = hist.get(len(adj[v]), 0) + 1
    return hist


rng = random.Random(5)

print("== 小图体检 ==")
adj_small = {0: {1, 2}, 1: {0, 2, 3}, 2: {0, 1}, 3: {1, 4}, 4: {3, 5, 6},
             5: {4, 6}, 6: {4, 5}}
print(f"  节点 {len(adj_small)}，平均度 {mean_degree(adj_small):.2f}，"
      f"密度 {density(adj_small):.3f}")
print(f"  聚类系数 = {clustering(adj_small):.3f}")
print(f"  连通分量 = {components(adj_small)}")
print(f"  度分布 = {degree_dist(adj_small)}")

print("\n== ER 随机图 vs 理论 ==")
print(f"  {'p':>6}{'平均度(np)':>12}{'实测平均度':>10}{'聚类系数':>9}{'理论p':>8}{'最大分量':>10}")
for p in (0.01, 0.02, 0.03, 0.05, 0.08):
    adj = er_graph(200, p, rng)
    comp_sizes = components(adj)
    print(f"  {p:>6.2f}{200 * p:>12.2f}{mean_degree(adj):>10.2f}"
          f"{clustering(adj):>9.3f}{p:>8.2f}{comp_sizes[0]:>10}")
print("  np ≈ 1（p≈0.005）是巨分量的相变点；p=0.05 时 200 节点几乎全连通")
print("  ER 的聚类系数 ≈ p：没有任何三角闭合偏好 —— 与真实社交网差距巨大")

print("\n== 相变演示：最大分量占比 ==")
print(f"  {'平均度 np':>10}{'最大分量占比':>12}")
for p in (0.002, 0.005, 0.008, 0.012, 0.02):
    adj = er_graph(500, p, rng)
    comp_sizes = components(adj)
    print(f"  {500 * p:>10.1f}{comp_sizes[0] / 500:>12.1%}")
print("  np < 1 时网络碎片化；np > 1 时出现覆盖大半网络的巨分量（渗流相变）")

print("\n== 度分布形状 ==")
adj = er_graph(1000, 0.02, rng)
hist = degree_dist(adj)
print("  ER G(1000, 0.02) 的度直方图:")
max_bar = max(hist.values())
for k in sorted(hist):
    bar = "#" * int(hist[k] / max_bar * 45)
    print(f"  度{k:>3} {bar} {hist[k]}")
print("  ER 度分布近似泊松（钟形）—— 真实网络是长尾幂律，见 880 课")

print("\n== 小结 ==")
for line in (
    "  图统计是网络分析的『血压体温』，也是一切模型对比的基准线",
    "  ER 图是零假设：真实网络偏离 ER 的地方就是结构性的证据",
    "  np=1 的巨分量相变是随机图理论最漂亮的结论之一",
    "  876 课：在图上定义『影响力』—— PageRank",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 WS 联络图聚类系数的解析公式 C = (3(k-2))/(4(k-1))·(1-p)³，与 879 课
#    实测对照。
# 2. 统计 ER 图的孤立节点比例随 p 的变化，验证其衰减速度。
# 3. 实现 k-core 分解：反复剥离度 < k 的节点，观察核数分布。
# 4. 思考：为什么社交网络的聚类系数远高于 ER？给出两个机制层面的解释。
