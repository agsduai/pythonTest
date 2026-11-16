# ===== 第881课：网络科学与图分析-链路预测 =====
# 知识点：
#   - 链路预测：根据当前结构预测『尚未出现/尚未被观察到的边』
#   - 局部相似度：共同邻居(CN)、Jaccard、Adamic-Adar（对大 hub 降权）
#   - 全局指标：优先连接 PA（度乘积）、Katz（练习）
#   - 评测协议：隐藏一批真实边作为正例，随机采样不存在边为负例，算 AUC
#   - Adamic-Adar 对「通过大 hub 相连」降权 —— 质量优于数量
# 依赖：无（标准库）
import math
import random


def planted_graph(rng, n_half=30, p_in=0.25, p_out=0.02):
    n = 2 * n_half
    adj = {i: set() for i in range(n)}
    edges = set()
    for i in range(n):
        for j in range(i + 1, n):
            p = p_in if (i < n_half) == (j < n_half) else p_out
            if rng.random() < p:
                adj[i].add(j)
                adj[j].add(i)
                edges.add((i, j))
    return adj, edges


def common_neighbors(adj, u, v):
    return len(adj[u] & adj[v])


def jaccard_score(adj, u, v):
    union = adj[u] | adj[v]
    return len(adj[u] & adj[v]) / len(union) if union else 0.0


def adamic_adar(adj, u, v):
    total = 0.0
    for w in adj[u] & adj[v]:
        dw = len(adj[w])
        if dw > 1:
            total += 1 / math.log(dw)
    return total


def pa_score(adj, u, v):
    return len(adj[u]) * len(adj[v])


def auc(scores_pos, scores_neg):
    """AUC = P(正例分数 > 负例分数) + 0.5·P(相等)，全对比较。"""
    win = tie = total = 0
    for sp in scores_pos:
        for sn in scores_neg:
            total += 1
            if sp > sn:
                win += 1
            elif sp == sn:
                tie += 1
    return (win + 0.5 * tie) / total


rng = random.Random(12)
adj, edges = planted_graph(rng)
n = len(adj)

print("== 构造带两个社区的图 ==")
m = len(edges)
print(f"  n={n}，边数 m={m}（社区内 ~{m - sum(1 for a, b in edges if (a < 30) != (b < 30))} 条）")

print("\n== 隐藏 20% 的社区内边 ==")
intra = sorted(e for e in edges if (e[0] < 30) == (e[1] < 30))
rng.shuffle(intra)
hidden = set(intra[:len(intra) // 5])
train_adj = {v: set(nb) for v, nb in adj.items()}
for a, b in hidden:
    train_adj[a].discard(b)
    train_adj[b].discard(a)
print(f"  隐藏 {len(hidden)} 条边作为正例")

print("\n== 采样负例（当前不存在且非隐藏的边）==")
negatives = []
attempts = 0
while len(negatives) < 200 and attempts < 20000:
    attempts += 1
    a, b = rng.randrange(n), rng.randrange(n)
    if a == b or (min(a, b), max(a, b)) in hidden:
        continue
    if b in train_adj[a]:
        continue
    negatives.append((min(a, b), max(a, b)))
negatives = list(dict.fromkeys(negatives))
print(f"  采样到 {len(negatives)} 条非边作为负例")

print("\n== 四种指标的 AUC ==")
predictors = [("共同邻居", common_neighbors), ("Jaccard", jaccard_score),
              ("Adamic-Adar", adamic_adar), ("优先连接", pa_score)]
hidden_list = sorted(hidden)
print(f"  {'指标':<12}{'AUC':>8}{'评价':>10}")
for name, fn in predictors:
    sp = [fn(train_adj, a, b) for a, b in hidden_list]
    sn = [fn(train_adj, a, b) for a, b in negatives]
    score = auc(sp, sn)
    verdict = "好" if score > 0.8 else ("一般" if score > 0.6 else "差")
    print(f"  {name:<12}{score:>8.3f}{verdict:>10}")
print("  随机猜 AUC = 0.5；社区结构明显时局部相似度指标能到 0.85+")

print("\n== 为什么 Adamic-Adar 常胜出 ==")
hub = 0
for w in train_adj[0] & train_adj[31]:
    print(f"  共同邻居 {w}: 度 {len(train_adj[w])}, 贡献 1/ln(度) = "
          f"{1 / math.log(len(train_adj[w])):.3f}")
print("  度小的共同邻居（真正的小圈子）贡献大；hub 只贡献 ~0.2")
print("  这等于说：『一对朋友共同认识几个小圈子熟人』比『共同关注大V』更有预测力")

print("\n== Top-K 推荐评测 ==")
k = 20
all_pairs = sorted(hidden_list + negatives)
for name, fn in (("Adamic-Adar", adamic_adar), ("优先连接", pa_score)):
    ranked = sorted(all_pairs, key=lambda e: -fn(train_adj, e[0], e[1]))
    hits = sum(1 for e in ranked[:k] if e in hidden)
    print(f"  {name}: Top{k} 推荐命中 {hits} 条真实隐藏边（命中率 {hits / k:.0%}）")
print("  工业场景（好友推荐）看的正是 Top-K 命中率，而非全局 AUC")

print("\n== 随机对照：结构信息真的有用吗 ==")
rng.shuffle(hidden_list)
sp_rand = [rng.random() for _ in hidden_list]
sn_rand = [rng.random() for _ in negatives]
print(f"  随机打分 AUC = {auc(sp_rand, sn_rand):.3f}（≈0.5 基线）")
print("  结构指标对 0.5 的超越，就是『网络结构本身含有未来信息』的证据")

print("\n== 小结 ==")
for line in (
    "  链接预测 = 把结构相似性转成未来连接的概率",
    "  指标要按语义选：小圈子共同邻居 > hub 计数（Adamic-Adar 的洞见）",
    "  评测必须区分正负例并留出隐藏集，否则是自欺",
    "  下一课综合：把本章工具拼成社交网络分析引擎",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Katz 指标：Σ β^l · (路径数)，用矩阵幂级数展开（小图直接迭代）。
# 2. 实现资源分配指标 RA（1/度 而非 1/log 度），与 Adamic-Adar 对比 AUC。
# 3. 在 880 课的 BA 网络上重做评测，比较幂律网络与社区网络的预测难度。
# 4. 思考：链接预测的「时间切片」评测为什么比随机隐藏更可信？隐藏边的
#    选择如何引入偏差？
