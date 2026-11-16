# ===== 第527课：推荐系统进阶-离线评估指标 =====
# 知识点：
#   - 推荐评估和搜索/分类不同：看“TopK 列表质量”，不是单点准确率
#   - Precision@K：推荐 K 个里有多少是用户真正喜欢的
#   - Recall@K：用户喜欢的物品里有多少被推荐出来
#   - MAP：每个相关位置上的精确率再平均，越靠前权重越高
#   - NDCG：按位置折损（1/log2(i+1)），并归一化到 0~1
#   - 离线指标高 ≠ 线上效果好：还要看新颖性、多样性、业务指标（第48章）
# 依赖：无
import math


# 每个用户“真正相关”的物品集合
RELEVANT = {
    "u1": {"a", "b", "d"},
    "u2": {"c", "e"},
    "u3": {"a", "f", "g"},
}

# 两个推荐器的输出（按排序）
RECOMMENDER_A = {
    "u1": ["b", "x", "d", "a", "y"],
    "u2": ["e", "c", "z", "w", "v"],
    "u3": ["a", "f", "q", "g", "r"],
}
RECOMMENDER_B = {
    "u1": ["a", "b", "c", "d", "e"],
    "u2": ["a", "b", "c", "d", "e"],
    "u3": ["a", "b", "c", "d", "e"],
}


def precision_at_k(recs, relevant, k):
    top = recs[:k]
    return sum(1 for x in top if x in relevant) / k if k else 0.0


def recall_at_k(recs, relevant, k):
    top = recs[:k]
    return sum(1 for x in top if x in relevant) / len(relevant) if relevant else 0.0


def average_precision(recs, relevant):
    hits, total = 0, 0.0
    for i, item in enumerate(recs, 1):
        if item in relevant:
            hits += 1
            total += hits / i
    return total / len(relevant) if relevant else 0.0


def dcg_at_k(recs, relevant, k):
    score = 0.0
    for i, item in enumerate(recs[:k], 1):
        rel = 1.0 if item in relevant else 0.0
        score += rel / math.log2(i + 1)
    return score


def ndcg_at_k(recs, relevant, k):
    dcg = dcg_at_k(recs, relevant, k)
    ideal = dcg_at_k(sorted(relevant), relevant, k)
    return dcg / ideal if ideal else 0.0


def evaluate(name, recs_by_user, k=3):
    print(f"\n== {name}（K={k}）==")
    totals = {"P": 0.0, "R": 0.0, "MAP": 0.0, "NDCG": 0.0}
    for user, recs in recs_by_user.items():
        relevant = RELEVANT[user]
        p = precision_at_k(recs, relevant, k)
        r = recall_at_k(recs, relevant, k)
        ap = average_precision(recs, relevant)
        ndcg = ndcg_at_k(recs, relevant, k)
        for key, val in (("P", p), ("R", r), ("MAP", ap), ("NDCG", ndcg)):
            totals[key] += val
        print(f"  {user}: P@{k}={p:.2f} R@{k}={r:.2f} AP={ap:.2f} NDCG={ndcg:.2f}")
    n = len(recs_by_user)
    print("  平均：", {k2: round(v / n, 3) for k2, v in totals.items()})
    return {k2: v / n for k2, v in totals.items()}


a = evaluate("推荐器A（个性化）", RECOMMENDER_A, k=3)
b = evaluate("推荐器B（热门/固定）", RECOMMENDER_B, k=3)

print("\n== 对比 ==")
for metric in ("P", "R", "MAP", "NDCG"):
    diff = a[metric] - b[metric]
    print(f"  {metric:5s}: A {a[metric]:.3f} | B {b[metric]:.3f} | 差值 {diff:+.3f}")

# ---- 逐步看 NDCG ----
print("\n== NDCG 逐步计算（u1, 推荐器A）==")
recs = RECOMMENDER_A["u1"]
relevant = RELEVANT["u1"]
for i, item in enumerate(recs[:3], 1):
    rel = 1 if item in relevant else 0
    gain = rel / math.log2(i + 1)
    print(f"  位置{i} {item}: rel={rel}，增益={gain:.3f}")
print(f"  DCG={dcg_at_k(recs, relevant, 3):.3f}，"
      f"IDCG={dcg_at_k(sorted(relevant), relevant, 3):.3f}，"
      f"NDCG={ndcg_at_k(recs, relevant, 3):.3f}")

# ---- 指标选择 ----
print("\n== 指标选择 ==")
for item in [
    "只看前 3 个 → Precision@3（用户注意力有限）",
    "不能漏掉重要物品 → Recall@K",
    "关心排序位置 → MAP / NDCG",
    "物品多、用户兴趣广 → 覆盖率、多样性、新颖性也要看",
    "离线指标要配线上 A/B（第482课），否则容易过拟合",
]:
    print("  -", item)

# ---- 常见坑 ----
print("\n== 常见坑 ==")
for item in [
    "测试集泄漏：推荐结果用到了未来行为",
    "负样本采样偏差：随机负样本太容易",
    "热门物品霸榜：precision 高但多样性差",
    "K 变了指标不可直接比较",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 计算两个推荐器在 K=5 时的指标，对比 K=3。
# 2. 实现“覆盖率”：推荐过的物品占全部物品的比例。
# 3. 给推荐器 B 加入随机扰动，观察 NDCG 变化。
# 4. 思考：为什么“推荐得准”不等于“用户会满意”？
