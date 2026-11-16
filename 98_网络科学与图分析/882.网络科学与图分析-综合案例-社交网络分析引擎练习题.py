# ===== 第882课：网络科学与图分析-综合案例-社交网络分析引擎 =====
# 知识点：
#   - 综合本章：图统计(875) + PageRank(876) + 中心性(877) + 社区(878) + 链路预测(881)
#   - 引擎一次输出「网络体检报告」：统计、影响力、桥梁、社区、推荐
#   - 数据：3 个 planted 社区 + 强制 hub，模拟真实社交平台的分层结构
#   - 各组件独立成函数，主流程只做编排 —— 分析引擎的典型架构
# 依赖：无（标准库）
import math
import random
from collections import deque


def build_social_graph(rng):
    """3 个社区（15/15/10 人）+ 2 个跨社区 hub。"""
    adj = {i: set() for i in range(40)}
    groups = [range(0, 15), range(15, 30), range(30, 40)]
    for gi, group in enumerate(groups):
        members = list(group)
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                if rng.random() < 0.22:
                    adj[members[i]].add(members[j])
                    adj[members[j]].add(members[i])
    hubs = [3, 17]                                  # 社区0/1 里的 hub
    for h in hubs:
        for other in adj:
            if other != h and rng.random() < 0.12:
                adj[h].add(other)
                adj[other].add(h)
    for a, b in ((3, 20), (17, 33), (3, 17)):       # 跨社区桥
        adj[a].add(b)
        adj[b].add(a)
    return adj


def stats(adj):
    n = len(adj)
    m = sum(len(v) for v in adj.values()) // 2
    clustering_total, cnt = 0.0, 0
    for v, nb in adj.items():
        if len(nb) < 2:
            continue
        links = sum(1 for a in nb for b in nb if a < b and b in adj[a])
        clustering_total += 2 * links / (len(nb) * (len(nb) - 1))
        cnt += 1
    return {"n": n, "m": m, "density": m / (n * (n - 1) / 2),
            "avg_deg": 2 * m / n,
            "clustering": clustering_total / cnt if cnt else 0.0}


def pagerank(adj, d=0.85, iters=100):
    nodes = list(adj)
    n = len(nodes)
    pr = {v: 1.0 / n for v in nodes}
    for _ in range(iters):
        dangling = sum(pr[v] for v in nodes if not adj[v])
        new = {v: (1 - d) / n + d * dangling / n for v in nodes}
        for v in nodes:
            if adj[v]:
                share = d * pr[v] / len(adj[v])
                for w in adj[v]:
                    new[w] += share
        pr = new
    return pr


def bfs_dist_all(adj, s):
    dist = {s: 0}
    queue = deque([s])
    while queue:
        v = queue.popleft()
        for w in adj[v]:
            if w not in dist:
                dist[w] = dist[v] + 1
                queue.append(w)
    return dist


def mean_path(adj):
    tot = 0.0
    for s in adj:
        d = bfs_dist_all(adj, s)
        tot += sum(d.values()) / (len(d) - 1) if len(d) > 1 else 0
    return tot / len(adj)


def betweenness(adj):
    bc = {v: 0.0 for v in adj}
    for s in adj:
        S, P = [], {v: [] for v in adj}
        sigma = {v: 0 for v in adj}
        sigma[s] = 1
        dist = {s: 0}
        queue = deque([s])
        while queue:
            v = queue.popleft()
            S.append(v)
            for w in adj[v]:
                if w not in dist:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    P[w].append(v)
        delta = {v: 0.0 for v in adj}
        while S:
            w = S.pop()
            for v in P[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                bc[w] += delta[w]
    for v in bc:
        bc[v] /= 2
    return bc


def label_propagation(adj, rng, max_iter=30):
    labels = {v: i for i, v in enumerate(adj)}
    for _ in range(max_iter):
        order = list(adj)
        rng.shuffle(order)
        changed = False
        for v in order:
            if not adj[v]:
                continue
            counts = {}
            for w in adj[v]:
                counts[labels[w]] = counts.get(labels[w], 0) + 1
            best = max(counts.values())
            cands = [c for c, n in counts.items() if n == best]
            new = rng.choice(cands) if len(cands) > 1 else cands[0]
            if new != labels[v]:
                labels[v] = new
                changed = True
        if not changed:
            break
    return labels


def adamic_adar(adj, u, v):
    return sum(1 / math.log(len(adj[w]))
               for w in adj[u] & adj[v] if len(adj[w]) > 1)


print("== 生成社交网络 ==")
rng = random.Random(14)
adj = build_social_graph(rng)
st = stats(adj)
print(f"  {st['n']} 用户 / {st['m']} 关系 / 密度 {st['density']:.3f} / "
      f"平均度 {st['avg_deg']:.1f} / 聚类系数 {st['clustering']:.3f}")

print("\n== 报告 1：影响力排行（PageRank Top5）==")
pr = pagerank(adj)
for v in sorted(pr, key=lambda x: -pr[x])[:5]:
    print(f"  用户 {v:>2}: PR = {pr[v]:.4f}  (度 = {len(adj[v])})")
print("  hub 3/17 因为连接多且连着重要的人而霸榜")

print("\n== 报告 2：桥梁人物（介数 Top5）==")
bet = betweenness(adj)
for v in sorted(bet, key=lambda x: -bet[x])[:5]:
    print(f"  用户 {v:>2}: 介数 = {bet[v]:.1f}")
print("  介数高 ≈ 信息流动的咽喉 —— 疫情隔离/舆情控制的目标人群")

print("\n== 报告 3：社区结构（标签传播）==")
labels = label_propagation(adj, rng)
comps = {}
for v, c in labels.items():
    comps.setdefault(c, []).append(v)
print(f"  发现 {len(comps)} 个社区:")
for c, members in sorted(comps.items(), key=lambda x: -len(x[1])):
    print(f"    社区{c}: {len(members)} 人 -> {sorted(members)}")

print("\n== 报告 4：小世界体检 ==")
L = mean_path(adj)
print(f"  平均路径长 L = {L:.2f}，聚类系数 C = {st['clustering']:.3f}")
print(f"  L/log(n) = {L / math.log(st['n']):.2f}（远小于 n 时为小世界特征）")
print(f"  L/n = {L / st['n']:.3f}；C 相对 ER(p=平均度/n) 增益 = "
      f"{st['clustering'] / (st['avg_deg'] / st['n']):.1f} 倍")
print("  C 增益 >> 1 且 L ~ log(n) -> 同时具备抱团与全球可达")

print("\n== 报告 5：好友推荐（Adamic-Adar Top6）==")
suggestions = []
for a in range(40):
    for b in range(a + 1, 40):
        if b not in adj[a]:
            aa = adamic_adar(adj, a, b)
            if aa > 0:
                suggestions.append((aa, a, b))
suggestions.sort(reverse=True)
for score, a, b in suggestions[:6]:
    common = sorted(adj[a] & adj[b])
    print(f"  推荐用户 {a} ↔ {b}: Adamic-Adar = {score:.3f}"
          f"（共同好友 {common}）")
print("  推荐逻辑：还没认识但共同认识几个小圈子好友的人最可能成为新连接")

print("\n== 引擎架构 ==")
for line in (
    "  build_social_graph()   数据层：可替换为真实抓取/数据库",
    "  stats/pagerank/...     指标层：每个函数只算一件事",
    "  报告编排               逻辑层：按业务组合指标并输出结论",
    "  可扩展：时序网络（边带时间戳）、属性图（用户画像）、动态监测",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  网络分析引擎 = 结构统计 + 影响力 + 社区 + 预测的编排流水线",
    "  每个报告回答一个业务问题：推谁、封谁、找谁、给谁看",
    "  所有组件都在前几课手写过 —— 合在一起就是可用的分析平台雏形",
    "  隐私与伦理：影响力排序/社区画像涉及个人数据，落地必须合规",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给引擎加「时间衰减」：边带时间戳，RecentGraph 只统计最近 30 天的边，
#    观察影响力排名变化。
# 2. 实现影响力最大化：贪心选 3 个种子使「激活人数」最大（独立级联模型），
#    与 PageRank Top3 对比。
# 3. 把社区发现换成 878 课的 Girvan-Newman，比较两种划分的模块度。
# 4. 思考：如果引擎被用于「精准广告」和「舆情操纵」两种目的，同一套指标
#    的伦理边界分别在哪里？
