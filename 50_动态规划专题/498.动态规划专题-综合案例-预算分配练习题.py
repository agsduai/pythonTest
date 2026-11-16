# ===== 第498课：动态规划专题-综合案例-预算分配 =====
# 知识点：
#   - 综合运用：0/1 背包（491）+ 分组背包（每组最多选一个）+ 方案重建
#   - 场景：旅行预算分配，每个类别最多选一个方案（住宿/交通/餐饮/门票）
#   - 分组背包：对每组，用“上一组的结果”更新本组，避免同组多选
#   - 方案重建：保存每组更新前的 dp 快照，回溯找出选择
#   - 对照组：暴力枚举所有组合，验证 DP 正确性
#   - 与第491课的区别：那课是每件物品独立，本课是“组内互斥”
# 依赖：无
import itertools


CATEGORIES = {
    "住宿": [("青旅", 2, 3), ("民宿", 4, 6), ("酒店", 6, 9)],
    "交通": [("火车", 2, 4), ("高铁", 4, 7), ("飞机", 6, 8)],
    "餐饮": [("简餐", 1, 2), ("特色", 3, 5)],
    "门票": [("基础", 2, 3), ("全通", 4, 6)],
}
BUDGET = 12


# ---------------- 分组背包 DP ----------------
def group_knapsack(categories, budget):
    """返回 (最大价值, 选择 {类别: 方案名}, 花费, dp 历史)。"""
    dp = [0] * (budget + 1)
    history = [dp[:]]                     # history[g] = 处理完前 g 组后的 dp

    for options in categories.values():
        new_dp = dp[:]                    # 先复制“不选本组”的情况
        for name, cost, value in options:
            for c in range(cost, budget + 1):
                candidate = dp[c - cost] + value
                if candidate > new_dp[c]:
                    new_dp[c] = candidate
        dp = new_dp
        history.append(dp[:])

    # ---- 回溯方案 ----
    chosen = {}
    c = budget
    for g in range(len(categories) - 1, -1, -1):
        cat_name = list(categories)[g]
        prev = history[g]
        if dp[c] == prev[c]:              # 本组没选
            continue
        for name, cost, value in categories[cat_name]:
            if cost <= c and prev[c - cost] + value == dp[c]:
                chosen[cat_name] = (name, cost, value)
                c -= cost
                break
        dp = prev

    return max(history[-1]), chosen, budget - c, history


# ---------------- 暴力枚举对照 ----------------
def brute_force(categories, budget):
    names = list(categories)
    option_lists = [categories[n] + [("不选", 0, 0)] for n in names]
    best_value, best_combo = 0, None
    for combo in itertools.product(*option_lists):
        cost = sum(item[1] for item in combo)
        if cost > budget:
            continue
        value = sum(item[2] for item in combo)
        if value > best_value:
            best_value, best_combo = value, combo
    return best_value, best_combo


best_value, chosen, spent, history = group_knapsack(CATEGORIES, BUDGET)
brute_value, brute_combo = brute_force(CATEGORIES, BUDGET)

print("== 预算 ==", BUDGET, "| 类别与选项：")
for cat, options in CATEGORIES.items():
    print(f"  {cat}: " + "、".join(f"{n}({c}费{v}值)" for n, c, v in options))

print("\n== 分组背包结果 ==")
print(f"  最大价值：{best_value}")
print(f"  总花费：{spent}")
print("  选择方案：")
for cat, (name, cost, value) in chosen.items():
    print(f"    {cat}: {name}（花费 {cost}，价值 {value}）")

print(f"\n  暴力最优：{brute_value} | 一致：{best_value == brute_value}")
print("  暴力组合：", [(n, i[0]) for n, i in zip(CATEGORIES, brute_combo)])

# ---------------- dp 表演进 ----------------
print("\n== dp 演进（每行=处理完一个类别后）==")
print("       " + "".join(f"{c:>4d}" for c in range(BUDGET + 1)))
labels = ["初始"] + list(CATEGORIES)
for label, row in zip(labels, history):
    print(f"  {label:4s}" + "".join(f"{v:>4d}" for v in row))

# ---------------- 预算变化敏感性 ----------------
print("\n== 预算敏感性 ==")
for b in (6, 8, 10, 12, 14, 16):
    value, plan, spent, _ = group_knapsack(CATEGORIES, b)
    print(f"  预算 {b:2d} → 最大价值 {value:2d}，花费 {spent:2d}，"
          f"方案 {[(k, v[0]) for k, v in plan.items()]}")

# ---------------- 扩展：类别可多选（退化为 0/1 背包）----------------
print("\n== 扩展思路 ==")
for item in [
    "类别可多选 → 把所有方案摊平成 0/1 背包（第491课）",
    "方案有依赖（选了酒店必须选高铁）→ 树形背包",
    "预算之外还有时间/体力约束 → 多维背包",
    "需要给出多个备选方案 → DP 存 TopK 而不是单个最优值",
    "真实产品还会考虑偏好权重、退款规则、库存",
]:
    print("  -", item)

# ---------------- 正确性说明 ----------------
print("\n== 为什么分组背包要复制上一组 dp？==")
print("  若直接在当前组 dp 上更新，可能出现“同一组选两个方案”")
print("  new_dp 从旧 dp 复制，只允许从旧状态转移 → 组内互斥")

# ===== 练习题 =====
# 1. 增加“购物”类别（3 个选项），重跑并对比暴力。
# 2. 改成“每个类别必须选一个”（不允许跳过），方案怎么变？
# 3. 给每个方案加“满意度/花费比”，按比值贪心选择，对比 DP 结果。
# 4. 思考：分组背包与 0/1 背包在状态转移上的唯一区别是什么？
