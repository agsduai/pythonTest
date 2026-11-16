# ===== 第876课：网络科学与图分析-PageRank与影响力 =====
# 知识点：
#   - PageRank = 「随机冲浪者」的平稳分布：随机跳转 + 沿链接走
#   - 幂迭代：PR(v) = (1-d)/n + d·(Σ PR(u)/out(u))，d 为阻尼（典型 0.85）
#   - 悬空节点（无出链）把质量均分给全网，否则质量会「漏掉」
#   - 入链多不等于排名高：来自高 PR 页的一条链接胜过十条低 PR 链接
#   - 与 HITS（练习）的区别：PageRank 单一权威分，HITS 分 hub/authority
# 依赖：无（标准库）


def pagerank(adj, d=0.85, iters=200, tol=1e-12):
    nodes = list(adj)
    n = len(nodes)
    pr = {v: 1.0 / n for v in nodes}
    deltas = []
    for it in range(iters):
        dangling = sum(pr[v] for v in nodes if not adj[v])
        new = {v: (1 - d) / n + d * dangling / n for v in nodes}
        for v in nodes:
            out = adj[v]
            if out:
                share = d * pr[v] / len(out)
                for w in out:
                    new[w] += share
        delta = sum(abs(new[v] - pr[v]) for v in nodes)
        deltas.append(delta)
        pr = new
        if delta < tol:
            break
    return pr, deltas, it + 1


print("== 迷你网页图 ==")
web = {
    "首页":   {"新闻A", "新闻B", "门户"},
    "新闻A":  {"首页", "论坛"},
    "新闻B":  {"首页"},
    "门户":   {"新闻A", "论坛"},
    "论坛":   {"首页", "门户"},
    "孤页":   set(),
}
print("  链接结构:")
for v, outs in web.items():
    print(f"    {v} -> {sorted(outs) if outs else '（悬空：无出链）'}")

print("\n== 幂迭代收敛 ==")
pr, deltas, iters = pagerank(web)
print(f"  迭代 {iters} 次收敛（最终 Δ = {deltas[-1]:.1e}）")
print(f"  {'迭代':>6}{'全图差异 Δ':>14}")
for i in (0, 1, 2, 3, 5, 8, 12):
    if i < len(deltas):
        print(f"  {i:>6}{deltas[i]:>14.6f}")

print("\n== 排名 ==")
print(f"  总质量 = {sum(pr.values()):.6f}（应恰为 1）")
print(f"  {'页面':<8}{'PageRank':>10}{'入链数':>8}")
in_deg = {v: sum(1 for outs in web.values() if v in outs) for v in web}
for v in sorted(pr, key=lambda x: -pr[x]):
    print(f"  {v:<8}{pr[v]:>10.4f}{in_deg[v]:>8}")
print("  首页虽然只有 2 条入链，但都来自高价值页面 -> 排名第一")
print("  悬空节点『孤页』靠 dangling 质量均分保底，不会变成 0")

print("\n== 阻尼 d 的作用 ==")
print(f"  {'d':>6}{'首页PR':>10}{'孤页PR':>10}")
for dd in (0.0, 0.5, 0.85, 0.99):
    p, _, _ = pagerank(web, d=dd)
    print(f"  {dd:>6.2f}{p['首页']:>10.4f}{p['孤页']:>10.4f}")
print("  d=0 全部均分（纯随机跳转）；d→1 完全跟随链接（可能被链接农场操纵）")

print("\n== 质量来源分析：一条高质量链接 vs 十条垃圾链接 ==")
small = {
    "明星页":  {"目标页"},
    "水军1":  {"目标页"}, "水军2": {"目标页"}, "水军3": {"目标页"},
    "权威页":  {"目标页", "权威页2", "权威页3", "权威页4", "权威页5"},
    "目标页":  {"明星页"},
    "权威页2": {"权威页"},
    "权威页3": {"权威页"},
    "权威页4": {"权威页"},
    "权威页5": {"权威页"},
}
p, _, _ = pagerank(small)
print(f"  目标页 PageRank = {p['目标页']:.4f}")
print(f"  每条水军链接贡献 ≈ {1 / len(small) * 0.85:.4f}（页面 PR / 出链数）")
print(f"  权威页一条链接贡献 ≈ {p['权威页'] / 5:.4f}")
print("  链接的价值 = 来源 PR ÷ 来源出链数 —— 反作弊的基本原理")

print("\n== 收敛速度与图规模 ==")
import random
rng = random.Random(6)


def er_directed(n, p, rng):
    adj = {}
    for i in range(n):
        adj[i] = {j for j in range(n) if j != i and rng.random() < p}
    return adj


for n in (100, 1000):
    adj = er_directed(n, 0.02, rng)
    p, _, it = pagerank(adj)
    top = max(p, key=p.get)
    print(f"  ER 有向图 n={n}: {it} 次迭代收敛，最高 PR 节点 = {top} ({p[top]:.4f})")

print("\n== 小结 ==")
for line in (
    "  PageRank = 图上的马尔可夫链平稳分布，幂迭代即求解",
    "  阻尼项既是数学正则化，也是『用户随机输入网址』的行为建模",
    "  悬空节点与质量守恒是实现中最容易出错的两个细节",
    "  下一课：把『影响力』拆成度/接近/介数三种不同的度量",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 HITS：hub/authority 双幂迭代，比较与 PageRank 的排名差异。
# 2. 实现个性化 PageRank：随机跳转只回到「种子节点集合」，模拟局部影响力。
# 3. 用第 459 课的 Dijkstra 思想给边加权（点击成本），实现加权 PageRank。
# 4. 思考：为什么 d 取 0.85 而不是 0.99？从收敛速度与抗操纵两个角度分析。
