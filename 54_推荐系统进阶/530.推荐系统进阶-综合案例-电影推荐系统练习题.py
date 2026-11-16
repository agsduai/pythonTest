# ===== 第530课：推荐系统进阶-综合案例-电影推荐系统 =====
# 知识点：
#   - 综合运用：内容推荐（524）+ 协同过滤（525/432）+ 混合（529）
#     + 评估（527）+ 冷启动（528）
#   - 数据：用户对电影的评分 + 电影类型标签
#   - 两路召回：内容相似度、User-CF 预测评分
#   - 混合：归一化后加权；新用户切换为内容/热门
#   - 评估：留一法，看被藏起来的电影是否进入 TopK
#   - 输出：给老用户推荐、给新用户冷启动推荐
# 依赖：无（纯标准库）

import math
from collections import Counter

# ---------------- 1. 数据 ----------------
MOVIES = {
    "m1": ("星际穿越", {"科幻", "冒险", "太空"}),
    "m2": ("盗梦空间", {"科幻", "悬疑", "动作"}),
    "m3": ("爱在黎明", {"爱情", "都市"}),
    "m4": ("疯狂的麦克斯", {"动作", "冒险"}),
    "m5": ("寻梦环游记", {"动画", "家庭", "音乐"}),
    "m6": ("机器人总动员", {"动画", "科幻", "家庭"}),
    "m7": ("七宗罪", {"悬疑", "犯罪", "黑暗"}),
    "m8": ("布达佩斯大饭店", {"喜剧", "都市"}),
    "m9": ("阿凡达", {"科幻", "冒险", "动作"}),
    "m10": ("当幸福来敲门", {"家庭", "励志"}),
}

RATINGS = {
    "小明": {"m1": 5, "m2": 4, "m7": 4, "m4": 3},
    "小红": {"m5": 5, "m6": 4, "m3": 4, "m8": 3},
    "小刚": {"m4": 5, "m1": 3, "m9": 4, "m7": 4},
    "小丽": {"m3": 5, "m8": 4, "m5": 3, "m10": 4},
    "小强": {"m1": 4, "m2": 5, "m9": 5, "m7": 4},
}


# ---------------- 2. 内容通道 ----------------
def genre_vector(genres: set) -> dict[str, float]:
    return {g: 1.0 for g in genres}


def cosine(v1: dict, v2: dict) -> float:
    common = set(v1) & set(v2)
    dot = sum(v1[t] * v2[t] for t in common)
    n1 = math.sqrt(sum(v * v for v in v1.values()))
    n2 = math.sqrt(sum(v * v for v in v2.values()))
    return dot / (n1 * n2) if n1 and n2 else 0.0


MOVIE_VECS = {mid: genre_vector(genres) for mid, (_, genres) in MOVIES.items()}


def user_content_profile(user: str) -> dict[str, float]:
    history = RATINGS[user]
    profile = Counter()
    total = sum(history.values())
    for mid, rating in history.items():
        for genre in MOVIES[mid][1]:
            profile[genre] += rating / total
    return dict(profile)


def content_scores(user: str) -> dict[str, float]:
    profile = user_content_profile(user)
    return {mid: cosine(profile, vec) for mid, vec in MOVIE_VECS.items()}


# ---------------- 3. 协同过滤通道 ----------------
def user_similarity(u1: str, u2: str) -> float:
    r1, r2 = RATINGS[u1], RATINGS[u2]
    common = set(r1) & set(r2)
    if not common:
        return 0.0
    dot = sum(r1[i] * r2[i] for i in common)
    n1 = math.sqrt(sum(v * v for v in r1.values()))
    n2 = math.sqrt(sum(v * v for v in r2.values()))
    return dot / (n1 * n2) if n1 and n2 else 0.0


def cf_score(user: str, movie: str) -> float | None:
    if movie in RATINGS[user]:
        return None
    num = den = 0.0
    for other in RATINGS:
        if other == user or movie not in RATINGS[other]:
            continue
        sim = user_similarity(user, other)
        if sim <= 0:
            continue
        num += sim * RATINGS[other][movie]
        den += sim
    return num / den if den else None


# ---------------- 4. 混合推荐 ----------------
def normalize(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    lo, hi = min(scores.values()), max(scores.values())
    if hi == lo:
        return {k: 0.5 for k in scores}
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


def recommend(user: str, top_n: int = 3, w_content: float = 0.4):
    seen = set(RATINGS[user])
    content = {m: s for m, s in content_scores(user).items() if m not in seen}
    cf_raw = {m: s for m in MOVIES if (s := cf_score(user, m)) is not None and m not in seen}

    if not cf_raw:                         # 冷启动/协同不可用
        return sorted(content.items(), key=lambda x: -x[1])[:top_n], "content"

    cf_n = normalize(cf_raw)
    content_n = normalize(content)
    hybrid = {
        m: w_content * content_n.get(m, 0) + (1 - w_content) * cf_n.get(m, 0)
        for m in set(cf_n) | set(content_n)
    }
    return sorted(hybrid.items(), key=lambda x: -x[1])[:top_n], "hybrid"


# ---------------- 5. 留一法评估 ----------------
def leave_one_out_eval(top_n: int = 2):
    hits = 0
    total = 0
    for user, ratings in RATINGS.items():
        for hidden in list(ratings):
            saved = ratings.pop(hidden)    # 暂时藏起
            recs, _ = recommend(user, top_n=top_n)
            if hidden in [m for m, _ in recs]:
                hits += 1
            total += 1
            ratings[hidden] = saved
    return hits / total if total else 0.0


print("== 推荐结果 ==")
for user in ("小明", "小红", "小刚"):
    recs, source = recommend(user, top_n=3)
    print(f"\n  {user}（{source}）：")
    for mid, score in recs:
        title, genres = MOVIES[mid]
        print(f"    {title:10s} 分数 {score:.3f} | {'/'.join(sorted(genres))}")

print("\n== 新用户冷启动 ==")
NEW_USER_GENRES = {"科幻", "悬疑"}
new_vec = genre_vector(NEW_USER_GENRES)
cold = sorted(
    ((mid, cosine(new_vec, vec)) for mid, vec in MOVIE_VECS.items()),
    key=lambda x: -x[1],
)[:3]
for mid, score in cold:
    print(f"  {MOVIES[mid][0]:10s} {score:.3f}")

print(f"\n== 留一法 Precision@2 ==")
p = leave_one_out_eval(top_n=2)
print(f"  命中率：{p:.2%}（样本很少，仅演示流程）")

# ---- 与单通道对比 ----
print("\n== 单通道 vs 混合 ==")
user = "小明"
seen = set(RATINGS[user])
for name, scores, source in (
    ("纯内容", content_scores(user), "content"),
    ("纯CF", {m: cf_score(user, m) or 0 for m in MOVIES if m not in seen}, "cf"),
    ("混合", dict(recommend(user, top_n=3)[0]), "hybrid"),
):
    top = sorted(((m, s) for m, s in scores.items() if m not in seen),
                 key=lambda x: -x[1])[:3]
    print(f"  {name}: {[MOVIES[m][0] for m, _ in top]}")

# ---- 系统清单 ----
print("\n== 系统落地清单 ==")
for item in [
    "数据：评分/点击/曝光日志 + 电影类型/简介/海报",
    "召回：热门前 100 + 内容相似 100 + CF 100 + 向量检索",
    "排序：混合分数或 GBDT/深度模型，融合用户/物品/上下文",
    "冷启动：引导选类型 + 热门兜底 + 新片探索流量",
    "评估：离线 Precision/NDCG + 线上 CTR/留存 A/B",
    "工程：离线训练、在线服务、特征一致、缓存、监控",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 MOVIES 增加 3 部电影，重新评估 Precision@3。
# 2. 把混合权重从 0.4 调到 0.2/0.8，观察推荐变化。
# 3. 实现“多样性重排”：Top3 中类型不能完全相同。
# 4. 思考：留一法评估有什么偏差？真实系统该怎么做？
