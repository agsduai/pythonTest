# ===== 第496课：动态规划专题-状态压缩DP =====
# 知识点：
#   - 状态压缩：用一个整数的二进制位表示“集合中哪些元素被选过”
#   - 适用：元素个数小（n <= 20 左右），需要枚举子集状态
#   - TSP（旅行商）：dp[mask][i] = 已访问集合 mask、当前在 i 的最小代价
#   - 转移：从 i 走到未访问的 j，mask 增加 j 这一位
#   - 最终结果：min(dp[全集][i] + dist[i][起点])
#   - 复杂度 O(2^n × n²)：n=20 时约 4 亿，通常 n<=15 更稳妥
#   - 与第335课回溯（全排列）的对比：状态压缩用空间换时间
# 依赖：无
import itertools


def tsp_bitmask(dist: list[list[int]]):
    """返回 (最小总距离, 访问顺序)。起点固定为 0。"""
    n = len(dist)
    full = (1 << n) - 1
    INF = float("inf")
    dp = [[INF] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]
    dp[1][0] = 0                                  # 只访问了 0，当前在 0

    for mask in range(1 << n):
        for u in range(n):
            if dp[mask][u] == INF:
                continue
            for v in range(n):
                if mask & (1 << v):                # 已访问
                    continue
                new_mask = mask | (1 << v)
                new_cost = dp[mask][u] + dist[u][v]
                if new_cost < dp[new_mask][v]:
                    dp[new_mask][v] = new_cost
                    parent[new_mask][v] = u

    # 回到起点
    best_cost, best_end = INF, -1
    for i in range(1, n):
        cost = dp[full][i] + dist[i][0]
        if cost < best_cost:
            best_cost, best_end = cost, i

    # 还原路径
    path, mask, cur = [], full, best_end
    while cur != -1:
        path.append(cur)
        prev = parent[mask][cur]
        mask ^= (1 << cur)
        cur = prev
    path.reverse()
    path.append(0)                                 # 回到起点
    return best_cost, path


# ---- 4 个城市：0=北京, 1=上海, 2=广州, 3=成都 ----
CITIES = ["北京", "上海", "广州", "成都"]
INF = 999
DIST = [
    [0, 1200, 1900, 1500],
    [1200, 0, 1400, 1800],
    [1900, 1400, 0, 1600],
    [1500, 1800, 1600, 0],
]
cost, path = tsp_bitmask(DIST)
print("== TSP 状态压缩 ==")
print(f"  最小总距离：{cost}")
print("  路线：", " → ".join(CITIES[i] for i in path))
print(f"  状态数：2^{len(CITIES)} = {1 << len(CITIES)} × {len(CITIES)} 个状态")

# ---- 与暴力全排列对比 ----
def tsp_brute(dist):
    n = len(dist)
    best, best_path = float("inf"), None
    for perm in itertools.permutations(range(1, n)):
        order = (0,) + perm + (0,)
        total = sum(dist[order[i]][order[i + 1]] for i in range(n))
        if total < best:
            best, best_path = total, order
    return best, list(best_path)


brute_cost, brute_path = tsp_brute(DIST)
print("\n== 与暴力对比 ==")
print(f"  暴力最优：{brute_cost}（{' → '.join(CITIES[i] for i in brute_path)}）")
print(f"  结果一致：{cost == brute_cost}")

# ---- 状态压缩的另一种常见用法：子集枚举 ----
print("\n== 子集枚举 ==")
items = ["A", "B", "C"]
n = len(items)
print("  所有子集：")
for mask in range(1 << n):
    subset = [items[i] for i in range(n) if mask & (1 << i)]
    print(f"    mask={mask:03b} → {subset}")

# ---- 遍历所有子集的子集（进阶技巧）----
print("\n== 枚举某个 mask 的所有子集 ==")
mask = 0b1011
sub = mask
subsets = []
while True:
    subsets.append(bin(sub))
    if sub == 0:
        break
    sub = (sub - 1) & mask
print(f"  mask=1011 的子集：{subsets}")

# ---- 常见题型 ----
print("\n== 常见状态压缩题 ==")
for item in [
    "TSP 旅行商 / 最短哈密顿回路",
    "棋盘覆盖（骨牌铺满，按行压缩）",
    "集合划分 / 选择若干物品满足条件",
    "课程安排（先修课用 mask 表示已修）",
]:
    print("  -", item)

# ---- 复杂度与边界 ----
print("\n== 边界 ==")
for item in [
    "n <= 15 很稳；n=20 需优化（滚动/剪枝）",
    "状态数组大小 2^n × n，n=20 时约 2000 万，内存要算清",
    "答案只依赖“当前集合 + 当前位置”时才能这样压缩",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把起点改成城市 1，重跑 TSP。
# 2. 实现“每个城市有开放时间”的变体（在转移时加时间约束）。
# 3. 用状态压缩求“集合划分成两个和相等的子集”是否存在。
# 4. 思考：为什么状态压缩 DP 通常比回溯快，但内存占用大？
