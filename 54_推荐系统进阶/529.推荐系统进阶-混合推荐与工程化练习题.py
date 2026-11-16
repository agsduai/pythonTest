# ===== 第529课：推荐系统进阶-混合推荐与工程化 =====
# 知识点：
#   - 单一推荐各有短板：CF 怕稀疏、内容怕茧房、热门没个性
#   - 混合方式：
#     1. 加权融合：score = w1*CF + w2*Content（需归一化）
#     2. 切换：CF 不可用（新用户）时切内容/热门
#     3. 级联：先用简单模型粗筛，再用复杂模型精排
#     4. 特征拼接：把多路分数作为特征喂给排序模型
#   - 分数量纲不同，融合前要归一化（min-max / z-score）
#   - 工程化：离线训练、在线服务、特征存储、缓存、A/B、监控
#   - 与第48章 A/B、第49章缓存、第523课两阶段架构呼应
# 依赖：无

# 假设两个召回通道的原始分数
CF_SCORES = {"m1": 4.8, "m2": 4.2, "m3": 3.1, "m4": 4.5, "m5": 2.0, "m6": 3.8}
CONTENT_SCORES = {"m1": 0.9, "m2": 0.85, "m3": 0.2, "m4": 0.6, "m5": 0.7, "m6": 0.75}
POPULARITY = {"m1": 0.9, "m2": 0.7, "m3": 0.6, "m4": 0.8, "m5": 0.5, "m6": 0.4}


def minmax(scores: dict) -> dict:
    lo, hi = min(scores.values()), max(scores.values())
    if hi == lo:
        return {k: 0.5 for k in scores}
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


cf_n = minmax(CF_SCORES)
content_n = minmax(CONTENT_SCORES)
pop_n = minmax(POPULARITY)

# ---------------- 1. 加权融合 ----------------
def weighted_hybrid(weights: dict, top_n=4):
    all_items = set(cf_n) | set(content_n) | set(pop_n)
    scores = {}
    for item in all_items:
        scores[item] = (
            weights.get("cf", 0) * cf_n.get(item, 0)
            + weights.get("content", 0) * content_n.get(item, 0)
            + weights.get("popularity", 0) * pop_n.get(item, 0)
        )
    return sorted(scores.items(), key=lambda x: -x[1])[:top_n]


print("== 1. 加权融合 ==")
for weights in (
    {"cf": 0.7, "content": 0.3},
    {"cf": 0.3, "content": 0.7},
    {"cf": 0.4, "content": 0.4, "popularity": 0.2},
):
    print(f"  权重 {weights} → {weighted_hybrid(weights)}")

# ---------------- 2. 切换策略 ----------------
def switching_recommend(user_has_history: bool, top_n=3):
    if user_has_history:
        return sorted(cf_n.items(), key=lambda x: -x[1])[:top_n], "CF"
    return sorted(content_n.items(), key=lambda x: -x[1])[:top_n], "Content（冷启动）"


print("\n== 2. 切换策略 ==")
for has_history in (True, False):
    recs, source = switching_recommend(has_history)
    print(f"  有历史={has_history}: {recs}（来源 {source}）")

# ---------------- 3. 级联 ----------------
def cascade_recommend(top_n=3, threshold=0.3):
    # 第一级：内容粗筛（快）
    coarse = [(item, s) for item, s in content_n.items() if s >= threshold]
    # 第二级：CF 精排（慢）
    refined = sorted(coarse, key=lambda x: -cf_n.get(x[0], 0))
    return refined[:top_n]


print("\n== 3. 级联 ==")
print("  内容粗筛 + CF 精排：", cascade_recommend())

# ---------------- 4. 工程架构 ----------------
print("\n== 4. 推荐系统工程架构 ==")
layers = [
    ("数据层", "埋点/日志/订单/内容元数据 → 数据仓库（第52章）"),
    ("离线层", "训练 CF/矩阵分解/内容画像，产出向量与规则"),
    ("特征层", "用户/物品/上下文特征，离线在线一致（特征存储）"),
    ("在线层", "召回（多路）→ 排序 → 重排，缓存热点结果（第49章）"),
    ("实验层", "A/B 分流、指标监控、灰度发布（第48章）"),
]
for name, desc in layers:
    print(f"  {name}: {desc}")

# ---------------- 5. 融合注意事项 ----------------
print("\n== 融合注意事项 ==")
for item in [
    "先归一化再加权，否则量纲大的通道会垄断",
    "权重用离线评估 + 线上 A/B 调，不要拍脑袋",
    "新用户走切换/内容，老用户走 CF 混合",
    "热门通道给一定权重，防止完全跑偏",
    "保留多样性：同类物品去重、类别打散",
]:
    print("  -", item)

# ---------------- 6. 线上指标 ----------------
print("\n== 线上看什么 ==")
rows = [
    ("点击率 CTR", "推荐是否吸引人", "短期"),
    ("转化率/GMV", "是否带来业务价值", "中期"),
    ("人均曝光/多样性", "是否信息茧房", "中期"),
    ("留存/复访", "长期健康度", "长期"),
    ("延迟 P99", "工程可用性", "实时"),
]
print(f"  {'指标':<16}{'回答的问题':<22}{'周期'}")
for r in rows:
    print(f"  {r[0]:<16}{r[1]:<22}{r[2]}")

# ===== 练习题 =====
# 1. 调整权重，让“内容”通道占比更高，观察 Top 列表变化。
# 2. 实现“多样性重排”：同一类别最多出现 2 个。
# 3. 给级联设置不同阈值，画出粗筛后剩余物品数。
# 4. 思考：离线融合权重调好后，线上一定更好吗？为什么？
