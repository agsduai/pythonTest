# ===== 第524课：推荐系统进阶-基于内容的推荐 =====
# 知识点：
#   - 内容推荐：给物品打标签/文本特征，推荐“和用户喜欢过的物品相似”的物品
#   - 物品画像：TF-IDF 或关键词向量
#   - 用户画像：用户喜欢过的物品向量的加权平均（评分做权重）
#   - 打分：余弦相似度（第384课），排除已看过的物品
#   - 优点：可解释、无冷启动物品问题；缺点：难以发现“跨品类惊喜”
#   - 与第36章文本处理、第384课余弦直接相关
import math
from collections import Counter


ITEMS = {
    "m1": "科幻 太空 冒险 硬核",
    "m2": "科幻 时间 悬疑",
    "m3": "爱情 都市 轻松",
    "m4": "动作 冒险 爆炸",
    "m5": "动画 家庭 治愈",
    "m6": "科幻 动画 家庭",
    "m7": "悬疑 犯罪 黑暗",
    "m8": "喜剧 都市 轻松",
}

# 用户看过的物品与评分（1~5）
USER_HISTORY = {
    "小明": {"m1": 5, "m2": 4, "m7": 3},
    "小红": {"m5": 5, "m6": 4, "m3": 4},
}


def tokenize(text: str) -> list[str]:
    return text.split()


def tf_vector(text: str) -> dict[str, float]:
    counts = Counter(tokenize(text))
    total = sum(counts.values()) or 1
    return {term: count / total for term, count in counts.items()}


def cosine(v1: dict, v2: dict) -> float:
    common = set(v1) & set(v2)
    dot = sum(v1[t] * v2[t] for t in common)
    n1 = math.sqrt(sum(v * v for v in v1.values()))
    n2 = math.sqrt(sum(v * v for v in v2.values()))
    return dot / (n1 * n2) if n1 and n2 else 0.0


item_vectors = {item: tf_vector(text) for item, text in ITEMS.items()}


def build_user_profile(history: dict) -> dict[str, float]:
    """按评分加权平均物品向量。"""
    profile: dict[str, float] = {}
    total_weight = sum(history.values())
    for item, rating in history.items():
        for term, value in item_vectors[item].items():
            profile[term] = profile.get(term, 0.0) + value * rating / total_weight
    return profile


def recommend(user: str, top_n: int = 3):
    history = USER_HISTORY[user]
    profile = build_user_profile(history)
    scores = []
    for item, vec in item_vectors.items():
        if item in history:                  # 已看过的不再推
            continue
        scores.append((item, cosine(profile, vec)))
    return sorted(scores, key=lambda x: -x[1])[:top_n]


for user in USER_HISTORY:
    print(f"== 给 {user} 推荐 ==")
    print("  已看：", USER_HISTORY[user])
    profile = build_user_profile(USER_HISTORY[user])
    print("  画像关键词：", dict(sorted(profile.items(), key=lambda kv: -kv[1])[:4]))
    for item, score in recommend(user):
        print(f"  {item}: {score:.3f}  ←  {ITEMS[item]}")
    print()

# ---- 解释推荐理由 ----
print("== 推荐理由 ==")
history = USER_HISTORY["小明"]
profile = build_user_profile(history)
for item, _ in recommend("小明")[:2]:
    shared = set(profile) & set(item_vectors[item])
    print(f"  {item} 与你的偏好共享：{sorted(shared)}")

# ---- 内容特征的优缺点 ----
print("\n== 优缺点 ==")
rows = [
    ("可解释", "能说清“因为喜欢科幻”", "标签质量决定上限"),
    ("新物品", "有标签就能被推荐（无冷启动）", "标签缺失就没法推"),
    ("多样性", "容易一直推同类，形成信息茧房", "需要加探索/去重"),
]
print(f"  {'维度':<8}{'优点':<26}{'风险'}")
for r in rows:
    print(f"  {r[0]:<8}{r[1]:<26}{r[2]}")

# ---- 改进方向 ----
print("\n== 改进方向 ==")
for item in [
    "用 TF-IDF 替代原始词频（第383课），降低常见词权重",
    "加入类型/导演/年代等结构化特征，不只靠文本",
    "用户画像做时间衰减：最近喜欢的权重更高",
    "与协同过滤混合（第529课），兼顾相似与惊喜",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 ITEMS 增加 2 部电影，观察推荐结果变化。
# 2. 用 TF-IDF 权重替换词频，重新计算相似度。
# 3. 实现“推荐理由”：输出共享的标签及贡献分数。
# 4. 思考：内容推荐为什么会造成“信息茧房”？怎么缓解？
