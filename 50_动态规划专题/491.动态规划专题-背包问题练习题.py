# ===== 第491课：动态规划专题-背包问题 =====
# 知识点：
#   - 0/1 背包：每件物品最多选一次，容量有限，价值最大
#   - dp[i][c] = 前 i 件、容量 c 的最优值；转移：不选 vs 选（容量够时）
#   - 一维滚动数组：倒序更新容量，省掉“件数”这一维
#   - 完全背包：每件可选无限次 → 容量正序遍历
#   - 重建方案：从 dp 表倒推选了哪些物品
#   - 与第255课入门 DP 的关系：这是最经典的二维 DP 模板
# 依赖：无


def knapsack_01(weights: list[int], values: list[int], capacity: int):
    """返回 (最大价值, 选中的下标, dp 表)。"""
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        w, v = weights[i - 1], values[i - 1]
        for c in range(capacity + 1):
            dp[i][c] = dp[i - 1][c]                    # 不选
            if w <= c:
                dp[i][c] = max(dp[i][c], dp[i - 1][c - w] + v)   # 选

    # 倒推方案
    chosen, c = [], capacity
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i - 1][c]:
            chosen.append(i - 1)
            c -= weights[i - 1]
    return dp[n][capacity], chosen[::-1], dp


def knapsack_01_1d(weights, values, capacity):
    """一维滚动数组：容量必须倒序遍历。"""
    dp = [0] * (capacity + 1)
    for w, v in zip(weights, values):
        for c in range(capacity, w - 1, -1):
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[capacity]


def knapsack_complete(weights, values, capacity):
    """完全背包：每件可选无限次，容量正序遍历。"""
    dp = [0] * (capacity + 1)
    for w, v in zip(weights, values):
        for c in range(w, capacity + 1):
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[capacity]


ITEMS = ["帐篷", "睡袋", "炉具", "相机", "水"]
WEIGHTS = [3, 2, 2, 4, 1]
VALUES = [8, 5, 4, 9, 2]
CAPACITY = 8

print("== 物品 ==")
for name, w, v in zip(ITEMS, WEIGHTS, VALUES):
    print(f"  {name}: 重量 {w}，价值 {v}")

best, chosen, dp = knapsack_01(WEIGHTS, VALUES, CAPACITY)
print(f"\n== 0/1 背包（容量 {CAPACITY}）==")
print(f"  最大价值：{best}")
print("  选中：", [(ITEMS[i], WEIGHTS[i], VALUES[i]) for i in chosen])
print(f"  总重量：{sum(WEIGHTS[i] for i in chosen)}")

print("\n== dp 表（行=前 i 件，列=容量）==")
print("      " + "".join(f"{c:>4d}" for c in range(CAPACITY + 1)))
for i, row in enumerate(dp):
    label = "空" if i == 0 else ITEMS[i - 1]
    print(f"  {label:4s}" + "".join(f"{v:>4d}" for v in row))

# ---- 一维与二维结果一致 ----
print("\n== 一维滚动数组 ==")
best_1d = knapsack_01_1d(WEIGHTS, VALUES, CAPACITY)
print(f"  结果：{best_1d}（与二维 {best} 一致：{best_1d == best}）")
print("  关键：容量倒序，保证每件物品只用一次")

# ---- 完全背包 ----
print("\n== 完全背包（每件无限次）==")
best_complete = knapsack_complete(WEIGHTS, VALUES, CAPACITY)
print(f"  最大价值：{best_complete}（比 0/1 的 {best} 更高，因为可以重复选）")

# ---- 如果正序遍历 0/1 背包会怎样 ----
print("\n== 错误示范：0/1 背包用正序 ==")
wrong = [0] * (CAPACITY + 1)
for w, v in zip(WEIGHTS, VALUES):
    for c in range(w, CAPACITY + 1):        # 正序 → 同一件被重复使用
        wrong[c] = max(wrong[c], wrong[c - w] + v)
print(f"  结果：{wrong[CAPACITY]}（变成了完全背包 {best_complete}，不是 0/1）")

# ---- 常见变体 ----
print("\n== 常见变体 ==")
for item in [
    "恰好装满：dp 初始化为 -∞，只有 dp[0]=0",
    "求方案数：转移从 max 改成求和",
    "二维费用（重量+体积）：dp 变三维或两个容量循环",
    "分组背包：每组最多选一个（第498课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 改成“恰好装满容量 8”，输出最大价值（可能无解）。
# 2. 统计装满容量 8 的方案数。
# 3. 增加“体积”维度，做二维费用背包。
# 4. 思考：一维滚动数组为什么必须倒序？用 dp 表举个例子。
