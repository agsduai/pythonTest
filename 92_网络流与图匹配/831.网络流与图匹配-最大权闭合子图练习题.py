# ===== 第831课：网络流与图匹配-最大权闭合子图与项目选择 =====
# 知识点：
#   - 闭合子图：子图中每个节点的所有后继也在子图内
#   - 最大权闭合子图：每个节点有权重（可正可负），找权重和最大的闭合子图
#   - 建模：S -> 正权节点（容量=权重），负权节点 -> T（容量=|权重|），
#          依赖边 u->v（容量=∞），最大流 = 最小割，答案 = Σ正权 - 最小割
#   - 应用：项目选择（依赖的项目必须一起选）、广告收益最大化
#   - 与第719课 B&B 的对比：B&B 是通用精确方法，最大权闭合子图利用特殊结构多项式求解
# 依赖：无（标准库）
from collections import defaultdict, deque
import math

INF = math.inf


def max_weight_closure(profits, deps):
    """最大权闭合子图：profits = {项目: 收益(可负)}，deps = {项目: [前置项目]}。
    返回 (最优收益, 选中的项目集合)。"""
    # 构建流网络
    nodes = set(profits.keys())
    net_cap = defaultdict(lambda: defaultdict(float))
    for n in nodes:
        net_cap[n]  # 确保所有节点存在

    positive_sum = 0
    for n, p in profits.items():
        if p > 0:
            net_cap["S"][n] += p
            positive_sum += p
        elif p < 0:
            net_cap[n]["T"] += -p
    # 依赖边：如果选 a 则必须选 b，加边 a -> b（容量 ∞）
    for a, pres in deps.items():
        for b in pres:
            net_cap[a][b] = INF

    # Edmonds-Karp 求最大流
    residual = defaultdict(lambda: defaultdict(float))
    for u in net_cap:
        for v, c in net_cap[u].items():
            residual[u][v] += c
            residual[v][u] += 0
    flow = 0.0
    while True:
        parent = {"S": None}
        q = deque(["S"])
        found = False
        while q and not found:
            u = q.popleft()
            for v in net_cap[u]:
                if v not in parent and residual[u][v] > 1e-9:
                    parent[v] = u
                    if v == "T": found = True; break
                    q.append(v)
        if not found: break
        path, cur = [], "T"
        while cur != "S":
            path.append(cur); cur = parent[cur]
        path.reverse(); path.insert(0, "S")
        bottleneck = min(residual[path[i]][path[i+1]]
                        for i in range(len(path)-1))
        for i in range(len(path)-1):
            residual[path[i]][path[i+1]] -= bottleneck
            residual[path[i+1]][path[i]] += bottleneck
        flow += bottleneck
    # 最小割：S 可达集合 = 选中的项目
    selected = {"S"}
    q = deque(["S"])
    while q:
        u = q.popleft()
        for v in net_cap[u]:
            if v not in selected and residual[u][v] > 1e-9:
                selected.add(v); q.append(v)
    selected.discard("S")
    selected.discard("T")
    result = positive_sum - flow
    return result, selected


print("== 项目选择问题 ==")
# 5 个项目，各有收益/成本，有依赖关系
profits = {"P1": 30, "P2": 20, "P3": -10, "P4": -15, "P5": 25}
deps = {
    "P1": [],              # P1 无依赖
    "P2": [],              # P2 无依赖
    "P3": ["P1"],          # 做 P3 必须先做 P1
    "P4": ["P2", "P3"],    # 做 P4 必须先做 P2 和 P3
    "P5": ["P1"],          # 做 P5 必须先做 P1
}

print("  项目收益与依赖:")
for p, v in profits.items():
    d = deps[p] if deps[p] else "无"
    sign = "+" if v > 0 else ""
    print(f"    {p}: 收益={sign}{v}  依赖={d}")

print("\n== 最大权闭合子图 ==")
result, selected = max_weight_closure(profits, deps)
print(f"  最优收益 = {result:.1f}")
print(f"  选中的项目 = {sorted(selected)}")
print(f"  验证收益 = {sum(profits[p] for p in selected)}")
print(f"  闭合性检查: ", end="")
ok = all(all(dep in selected for dep in deps[p]) for p in selected)
print("所有选中项目的依赖都在选中集合内" if ok else "违反闭合性！")

print("\n== 依赖强制选择的机制 ==")
for line in (
    "  P3 收益 -10（负），单独不选",
    "  但 P5 收益 +25 依赖 P3，选 P5 就必须选 P3",
    "  建模: P3 -> T 的容量=10（负权的代价），S->P5 的容量=25（正权的收益）",
    "  如果 P3+P5 的收益 25-10=15 > 0，最小割会选择同时包含两者",
):
    print(" ", line)

print("\n== 边界情况 ==")
# 全负权
profits_neg = {"A": -5, "B": -3}
r_neg, sel_neg = max_weight_closure(profits_neg, {})
print(f"  全负权: 收益={r_neg} 选中={sel_neg or '空集'}（应为空集）")

# 无依赖
profits_simple = {"A": 10, "B": -5, "C": 3}
r_simple, sel_simple = max_weight_closure(profits_simple, {})
print(f"  无依赖: 收益={r_simple} 选中={sorted(sel_simple)}")
print(f"  验证: 选 A(10) + C(3) = 13，不选 B(-5) -> {10+3}")

print("\n== 建模原理 ==")
for line in (
    "  S -> 正权节点: 容量=权重（不选它就要割掉 = 损失收益）",
    "  负权节点 -> T: 容量=|权重|（选它就要割掉 = 付出成本）",
    "  依赖边 u->v: 容量=∞（不可割，保证闭合性）",
    "  最小割 S/T 划分: S 侧=选中的项目（闭合子图）",
    "  最优收益 = Σ正权 - 最小割",
):
    print(" ", line)

print("\n== 应用 ==")
for line in [
    "  项目投资：选哪些项目使总收益最大（考虑依赖关系）",
    "  广告位选择：选哪些广告位（有冲突/依赖）使总收益最大",
    "  开源组件选择：选哪些依赖库（有传递依赖）使收益最大",
    "  数据库设计：选哪些表建立索引（有查询依赖）",
]:
    print("  -", line)

print("\n== 与其他方法对比 ==")
for line in [
    "  B&B(第719课): 通用精确，适合无特殊结构的组合优化",
    "  最大权闭合子图: 利用依赖图结构，多项式时间 O(VE²) 精确求解",
    "  关键: 把「选择+依赖」建模为「闭合子图」，用网络流求解",
    "  类似结构: 最大独立集在二分图 = 总数 - 最大匹配（第828课）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 用第719课的分支定界验证最大权闭合子图的结果。
# 2. 实现「带预算约束」的闭合子图：选中的项目总成本不超过预算。
# 3. 构造一个「负权项目的收益超过正权项目」的实例并分析最优解。
# 4. 思考：为什么闭合子图问题可以用网络流多项式求解，而一般 0/1 背包不行？
