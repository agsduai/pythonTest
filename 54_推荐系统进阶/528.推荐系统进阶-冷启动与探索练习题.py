# ===== 第528课：推荐系统进阶-冷启动与探索 =====
# 知识点：
#   - 冷启动三类：新用户、新物品、新系统
#   - 新用户：没有行为 → 热门兜底、引导选择兴趣、内容推荐
#   - 新物品：没有评分 → 内容特征、探索流量、专家标注
#   - 探索与利用（EE）：一直推已知最优会错过更好物品
#   - ε-greedy：以小概率随机探索；UCB/Thompson 更智能
#   - 与第48章 A/B、第524课内容推荐、第527课评估配合
# 依赖：无
import math
import random

# ---------------- 1. 物品与内容特征 ----------------
ITEMS = {
    "m1": {"科幻", "冒险"},
    "m2": {"科幻", "悬疑"},
    "m3": {"爱情", "都市"},
    "m4": {"动作", "冒险"},
    "m5": {"动画", "家庭"},
    "m6": {"动画", "科幻"},
    "m7": {"悬疑", "犯罪"},
    "m8": {"喜剧", "都市"},
}

# 老用户评分（用于协同过滤）
RATINGS = {
    "小明": {"m1": 5, "m2": 4, "m7": 3},
    "小红": {"m5": 5, "m6": 4, "m3": 4},
    "小刚": {"m4": 5, "m1": 3, "m8": 4},
}


def content_score(selected_genres: set, item: str) -> float:
    genres = ITEMS[item]
    return len(selected_genres & genres) / len(selected_genres | genres)


# ---------------- 2. 新用户：引导选择兴趣 ----------------
def recommend_for_new_user(selected_genres: set, top_n=3):
    scores = [(item, content_score(selected_genres, item)) for item in ITEMS]
    return sorted(scores, key=lambda x: -x[1])[:top_n]


print("== 新用户：引导选择兴趣 ==")
for genres in ({"科幻"}, {"动画", "家庭"}, {"悬疑"}):
    print(f"  选择 {sorted(genres)} → {recommend_for_new_user(genres)}")

# ---------------- 3. 热门兜底 ----------------
print("\n== 热门兜底（完全没有信息时）==")
popularity = {"m1": 8, "m2": 6, "m3": 5, "m4": 7, "m5": 4, "m6": 3, "m7": 5, "m8": 2}
print("  按热度推荐：", sorted(popularity.items(), key=lambda kv: -kv[1])[:3])

# ---------------- 4. ε-greedy 探索 ----------------
print("\n== ε-greedy：探索 vs 利用 ==")
# 每个物品真实点击率（模拟环境，算法不知道）
TRUE_CTR = {"m1": 0.30, "m2": 0.25, "m3": 0.10,
            "m4": 0.20, "m5": 0.05, "m6": 0.15,
            "m7": 0.12, "m8": 0.08}
counts = {item: 0 for item in TRUE_CTR}
rewards = {item: 0 for item in TRUE_CTR}
rng = random.Random(7)
epsilon = 0.1
total_reward = 0

for round_no in range(1, 1001):
    if rng.random() < epsilon or all(c == 0 for c in counts.values()):
        item = rng.choice(list(TRUE_CTR))          # 探索
    else:
        item = max(TRUE_CTR, key=lambda i: rewards[i] / counts[i] if counts[i] else 0)
    counts[item] += 1
    reward = 1 if rng.random() < TRUE_CTR[item] else 0
    rewards[item] += reward
    total_reward += reward

print(f"  1000 轮总点击：{total_reward}（平均 CTR {total_reward / 1000:.1%}）")
print("  各物品被展示次数与估计 CTR：")
for item in sorted(TRUE_CTR):
    est = rewards[item] / counts[item] if counts[item] else 0
    print(f"    {item}: 展示 {counts[item]:3d} 次，估计 CTR {est:.2%}，真实 {TRUE_CTR[item]:.0%}")

# ---- 与纯利用对比 ----
print("\n== 纯利用（ε=0）容易卡在次优 ==")
counts2 = {item: 0 for item in TRUE_CTR}
rewards2 = {item: 0 for item in TRUE_CTR}
# 初始随机试一轮
for item in TRUE_CTR:
    counts2[item] += 1
    rewards2[item] += 1 if rng.random() < TRUE_CTR[item] else 0
for _ in range(1000):
    item = max(TRUE_CTR, key=lambda i: rewards2[i] / counts2[i])
    counts2[item] += 1
    rewards2[item] += 1 if rng.random() < TRUE_CTR[item] else 0
print("  各物品展示次数：", counts2)
print("  可能把早期运气好的次优物品当成最优")

# ---- 冷启动策略清单 ----
print("\n== 冷启动策略 ==")
for item in [
    "新用户：热门 + 引导选择 3~5 个兴趣 + 内容推荐",
    "新物品：内容特征相似推荐 + 给一定探索流量",
    "新系统：先做热门/人工精选，积累行为后再上模型",
    "探索不能太激进：用 ε=5%~10%，并监控体验指标",
    "用 UCB/Thompson Sampling 平衡探索与利用（进阶）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把 ε 改成 0.01 / 0.3，观察总点击与探索分布。
# 2. 实现 UCB：选择“均值 + c*sqrt(ln N / n_i)”最大的物品。
# 3. 给新物品加“探索预算”：每天固定曝光 100 次。
# 4. 思考：为什么冷启动阶段“多样性”比“精准”更重要？
