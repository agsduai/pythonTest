# ===== 第1105课：itertools迭代工具-combinations组合 =====
# 知识点：
#   - combinations(序列, r)：取 r 个"不看顺序"的组合，nCr = n!/(r!(n-r)!)
#   - 组合不看顺序：(A,B) 和 (B,A) 算同一种
#   - combinations_with_replacement：允许重复选取（如骰子可以掷出双 SAME）
#   - 实际场景：组队、两两对决赛程、优惠券搭配、投资组合

# 案例一：组队 —— 5 选 2
import itertools

candidates = ["小张", "小李", "小王", "小赵", "小周"]
teams = list(itertools.combinations(candidates, 2))
print(f"5 选 2 共 {len(teams)} 种组合：{[f'{a}&{b}' for a, b in teams]}")

# 案例二：循环赛赛程 —— 两两对决
# 场景：4 支球队主客各打一场，赛程即全部配对
teams_ = ["红队", "蓝队", "绿队", "黄队"]
schedule = list(itertools.combinations(teams_, 2))
print(f"共 {len(schedule)} 场对决：")
for home, away in schedule:
    print(f"  {home} vs {away}")

# 案例三：数量对比 —— 排列 vs 组合
n = len(teams_)
print(f"{n} 支球队：两两对决 {len(schedule)} 场（组合），若分主客双循环 {len(list(itertools.permutations(teams_, 2)))} 场（排列）")

# 案例四：允许重复的组合
# 场景：掷两颗骰子的所有点数组合（可以两颗一样）
dice = list(itertools.combinations_with_replacement(range(1, 7), 2))
print(f"骰子组合共 {len(dice)} 种：{dice[:6]} ...")
print(f"包含 (3,3) 这种重复：{(3, 3) in dice}")

# 案例五：凑单组合 —— 找出刚好满 100 的搭配
# 场景：购物车里挑几件凑满减
prices = {"苹果": 25, "牛奶": 40, "面包": 30, "鸡蛋": 35, "酸奶": 45}
for r in range(2, 4):  # 试 2 件和 3 件的组合
    for combo in itertools.combinations(prices, r):
        total = sum(prices[g] for g in combo)
        if total >= 100:
            print(f"凑单方案：{combo} = {total} 元")

# ===== 练习题 =====
# 1. 用 combinations 计算 6 选 3 的组合数并打印全部组合（应为 20 种）。
# 2. 朋友聚餐 [25, 38, 42, 30]（元/人份），用 combinations 找出"恰好两人合计 80 元以下"的所有两人搭配。
# 3. 写函数 pair_up(items)：返回列表所有两两配对组合，用 4 支球队测试应返回 6 场；再说明它和 permutations(len=2) 的数量关系。
