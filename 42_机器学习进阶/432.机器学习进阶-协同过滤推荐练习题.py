# ===== 第432课：机器学习进阶-协同过滤推荐 =====
# 知识点：
#   - 协同过滤：利用“相似用户/相似物品”的评分来预测未知评分
#   - User-CF：找和目標用户口味相似的邻居，按相似度加权平均他们的评分
#   - 余弦相似度：只在“共同评过分的物品”上计算（第384课）
#   - 冷启动：新用户/新物品没有评分，CF 无能为力（需要内容特征）
#   - 评估：留一法（藏起一个评分，预测后比较 MAE）
# 依赖：pip install numpy

import math
from collections import defaultdict

# 用户 → {物品: 评分 1~5}
RATINGS = {
    "小明": {"Python": 5, "算法": 4, "前端": 2, "数据库": 4},
    "小红": {"Python": 4, "算法": 5, "前端": 2, "数据库": 3},
    "小刚": {"Python": 2, "前端": 5, "设计": 4, "数据库": 1},
    "小丽": {"前端": 4, "设计": 5, "数据库": 2},
    "小强": {"Python": 5, "算法": 5, "数据库": 4, "后端": 5},
}


def cosine(u1: dict, u2: dict) -> float:
    """只在共同物品上算相似度；无交集返回 0。"""
    common = set(u1) & set(u2)
    if not common:
        return 0.0
    dot = sum(u1[i] * u2[i] for i in common)
    n1 = math.sqrt(sum(v * v for v in u1.values()))
    n2 = math.sqrt(sum(v * v for v in u2.values()))
    return dot / (n1 * n2) if n1 and n2 else 0.0


def predict_rating(user: str, item: str) -> float | None:
    """加权平均：相似度越高的邻居，票越重。"""
    if item in RATINGS[user]:
        return RATINGS[user][item]
    numerator = denominator = 0.0
    for other, ratings in RATINGS.items():
        if other == user or item not in ratings:
            continue
        sim = cosine(RATINGS[user], ratings)
        if sim <= 0:
            continue
        numerator += sim * ratings[item]
        denominator += sim
    if denominator == 0:
        return None
    return numerator / denominator


def recommend(user: str, top_n: int = 3) -> list[tuple[str, float]]:
    rated = set(RATINGS[user])
    candidates = {item for ratings in RATINGS.values() for item in ratings} - rated
    scored = []
    for item in candidates:
        score = predict_rating(user, item)
        if score is not None:
            scored.append((item, round(score, 3)))
    return sorted(scored, key=lambda x: -x[1])[:top_n]


# ---- 相似度矩阵 ----
users = list(RATINGS)
print("== 用户相似度（只算共同物品）==")
print("      " + "".join(f"{u:>8s}" for u in users))
for u in users:
    row = [cosine(RATINGS[u], RATINGS[v]) for v in users]
    print(f"  {u:4s}" + "".join(f"{v:8.2f}" for v in row))

# ---- 给小明推荐 ----
print("\n== 给小明推荐 ==")
for item, score in recommend("小明", top_n=3):
    print(f"  {item}: 预测 {score} 分")
print("  说明：小刚喜欢的“设计”不会推荐给小明（两人口味相反，相似度为负/低）")

# ---- 解释一个预测 ----
print("\n== 预测过程拆解：小明 对 后端 的评分 ==")
for other in users:
    if other == "小明" or "后端" not in RATINGS[other]:
        continue
    sim = cosine(RATINGS["小明"], RATINGS[other])
    print(f"  {other}: 相似度 {sim:.3f}，评分 {RATINGS[other]['后端']}")
pred = predict_rating("小明", "后端")
print("  加权结果：", None if pred is None else round(pred, 3))

# ---- 留一法评估 ----
print("\n== 留一法 MAE ==")
errors = []
for user, ratings in RATINGS.items():
    for item in list(ratings):
        actual = ratings.pop(item)             # 暂时藏起来
        predicted = predict_rating(user, item)
        ratings[item] = actual                 # 立刻恢复
        if predicted is not None:
            errors.append(abs(predicted - actual))
            print(f"  {user} / {item}: 实际 {actual} 预测 {predicted:.2f}")
print(f"  平均绝对误差 MAE = {sum(errors) / len(errors):.3f}（越小越准）")

# ---- 物品相似度（Item-CF 思路）----
print("\n== 物品相似度示例 ==")
item_users = defaultdict(dict)
for user, ratings in RATINGS.items():
    for item, score in ratings.items():
        item_users[item][user] = score
for pair in [("Python", "算法"), ("Python", "前端"), ("前端", "设计")]:
    a, b = pair
    print(f"  {a} ~ {b}: {cosine(item_users[a], item_users[b]):.2f}")

# ===== 练习题 =====
# 1. 把余弦换成皮尔逊相关系数（减去用户均分），对比推荐结果。
# 2. 用 Item-CF 给小明推荐，和 User-CF 结果比较。
# 3. 加入“热门惩罚”：越流行的物品权重越低，避免全推荐爆款。
# 4. 思考：新用户没有任何评分时，怎么给出第一版推荐？
