# ===== 第526课：推荐系统进阶-关联规则与购物篮分析 =====
# 知识点：
#   - 关联规则：从交易数据中发现“买了 A 也会买 B”
#   - 三个指标：支持度（出现频率）、置信度（A 出现时 B 的条件概率）、提升度
#   - Apriori 原理：频繁项集的子集也一定频繁 → 逐层剪枝
#   - 提升度 > 1 表示正相关；= 1 独立；< 1 负相关
#   - 应用：购物篮推荐、捆绑销售、页面交叉推荐
#   - 与第385课倒排索引：都在“找共现”，但关联规则关注组合
#   - 注意：规则多不等于有用，要结合业务与提升度筛选
from collections import defaultdict
from itertools import combinations


TRANSACTIONS = [
    {"面包", "牛奶", "鸡蛋"},
    {"面包", "牛奶"},
    {"面包", "尿布", "啤酒"},
    {"牛奶", "尿布", "啤酒", "鸡蛋"},
    {"面包", "牛奶", "尿布", "啤酒"},
    {"面包", "牛奶", "鸡蛋"},
    {"尿布", "啤酒"},
    {"面包", "尿布", "啤酒"},
]


def support_count(itemset, transactions):
    return sum(1 for t in transactions if itemset <= t)


def apriori(transactions, min_support=0.25, max_size=3):
    """返回频繁项集 {frozenset: 支持度计数}。"""
    n = len(transactions)
    min_count = min_support * n
    freq = {}
    # 1 项集
    candidates = {frozenset([item]) for t in transactions for item in t}
    k = 1
    while candidates and k <= max_size:
        current = {}
        for itemset in candidates:
            count = support_count(itemset, transactions)
            if count >= min_count:
                current[itemset] = count
        freq.update(current)
        print(f"  {k} 项集：通过 {len(current)} 个")

        # 生成 k+1 候选：只在频繁项集之间连接
        next_candidates = set()
        frequent_list = list(current)
        for a, b in combinations(frequent_list, 2):
            union = a | b
            if len(union) == k + 1:
                # 剪枝：所有 k 子集都必须频繁
                if all(frozenset(sub) in current for sub in combinations(union, k)):
                    next_candidates.add(union)
        candidates = next_candidates
        k += 1
    return freq


def generate_rules(freq, transactions, min_confidence=0.6, min_lift=1.0):
    n = len(transactions)
    rules = []
    for itemset, count in freq.items():
        if len(itemset) < 2:
            continue
        for r in range(1, len(itemset)):
            for antecedent in combinations(itemset, r):
                ante = frozenset(antecedent)
                cons = itemset - ante
                ante_count = support_count(ante, transactions)
                cons_count = support_count(cons, transactions)
                confidence = count / ante_count
                support = count / n
                lift = confidence / (cons_count / n)
                if confidence >= min_confidence and lift >= min_lift:
                    rules.append({
                        "antecedent": sorted(ante),
                        "consequent": sorted(cons),
                        "support": support,
                        "confidence": confidence,
                        "lift": lift,
                    })
    return sorted(rules, key=lambda x: (-x["lift"], -x["confidence"]))


print("== 交易数据 ==")
for i, t in enumerate(TRANSACTIONS, 1):
    print(f"  交易{i}: {sorted(t)}")

print("\n== Apriori 频繁项集（min_support=0.25）==")
freq = apriori(TRANSACTIONS, min_support=0.25)
for itemset, count in sorted(freq.items(), key=lambda kv: (-len(kv[0]), -kv[1])):
    print(f"  {sorted(itemset)}: {count}/{len(TRANSACTIONS)} = {count / len(TRANSACTIONS):.1%}")

print("\n== 关联规则（confidence>=0.6, lift>=1）==")
rules = generate_rules(freq, TRANSACTIONS, min_confidence=0.6, min_lift=1.0)
for rule in rules[:10]:
    print(f"  {rule['antecedent']} → {rule['consequent']} | "
          f"支持度 {rule['support']:.0%} | 置信度 {rule['confidence']:.0%} | "
          f"提升度 {rule['lift']:.2f}")

# ---- 指标含义 ----
print("\n== 指标含义 ==")
print("  支持度：这条规则覆盖多少交易（太低的规则可能只是噪声）")
print("  置信度：买了 A 的人里有多少也买了 B")
print("  提升度：比“B 的自然购买率”高多少倍")
print("  提升度 > 1 才是正相关；= 1 说明 A/B 独立")

# ---- 业务筛选 ----
print("\n== 业务筛选 ==")
for item in [
    "先按提升度排序，再看支持度（避免小众噪声）",
    "排除“本来就必买”的商品（如购物袋）",
    "规则太多时按品类分组，人工审核 TopN",
    "上线后做 A/B 验证（第48章），别只看离线指标",
]:
    print("  -", item)

# ---- Apriori 的局限 ----
print("\n== 局限 ==")
for item in [
    "需要多次扫描数据，候选集可能爆炸",
    "长事务/密集数据性能差",
    "只反映“共现”，不反映因果",
    "改进：FP-Growth（不生成候选集）、PrefixSpan（序列模式）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把 min_support 调到 0.4，观察频繁项集与规则变化。
# 2. 增加一条交易 {面包, 啤酒}，观察提升度变化。
# 3. 实现 FP-Growth 的简化版（或用字典树存事务）并对比性能。
# 4. 思考：为什么“置信度高”不一定代表推荐价值高？
