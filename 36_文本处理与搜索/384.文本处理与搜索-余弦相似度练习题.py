# ===== 第384课：文本处理与搜索-余弦相似度 =====
# 知识点：
#   - 文本向量化后，用夹角余弦衡量“方向是否一致”，忽略长度差异
#   - cos(A,B) = A·B / (|A|·|B|)，取值 [-1,1]，文本场景通常 [0,1]
#   - 余弦 vs 欧氏距离：余弦只看方向，适合“长短文档”比较
#   - 应用：文档去重、相似推荐、聚类、问答匹配
# 依赖：无（标准库 math）

import math
from collections import Counter
import re

DOCS = {
    "A": "machine learning needs data and features",
    "B": "machine learning models need data cleaning",
    "C": "the weather is nice today in beijing",
    "D": "data analysis with pandas and python",
}


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


def term_freq(text: str) -> Counter:
    return Counter(tokenize(text))


def cosine(v1: dict, v2: dict) -> float:
    common = set(v1) & set(v2)
    dot = sum(v1[t] * v2[t] for t in common)
    n1 = math.sqrt(sum(v * v for v in v1.values()))
    n2 = math.sqrt(sum(v * v for v in v2.values()))
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)


# ---- 词频向量版 ----
vectors = {doc_id: dict(term_freq(text)) for doc_id, text in DOCS.items()}

print("原始词频余弦相似度矩阵：")
ids = list(DOCS)
print("      " + "      ".join(ids))
for a in ids:
    row = [cosine(vectors[a], vectors[b]) for b in ids]
    print(f"  {a}  " + "  ".join(f"{v:5.3f}" for v in row))

# ---- 与“查询”比较：哪篇文档最相关 ----
query = "machine learning data"
q_vec = dict(term_freq(query))
print(f'\n查询 "{query}" 的相关度排序：')
for doc_id in sorted(ids, key=lambda x: -cosine(q_vec, vectors[x])):
    print(f"  {doc_id}: {cosine(q_vec, vectors[doc_id]):.3f}")

# ---- 余弦不受长度影响：把 A 复制一遍 ----
long_a = dict(term_freq(DOCS["A"] * 2))
print("\nA 复制一遍后与 B 的余弦：", f"{cosine(long_a, vectors['B']):.3f}",
      "（与原来几乎一致）")
print("欧氏距离则会因为向量变长而变大：",
      f"{math.dist([long_a.get(t, 0) for t in sorted(set(long_a) | set(vectors['B']))], [vectors['B'].get(t, 0) for t in sorted(set(long_a) | set(vectors['B']))]):.3f}")

# ---- 阈值判定：相似度 > 0.5 视为“同一主题” ----
pairs = [(a, b, cosine(vectors[a], vectors[b]))
         for i, a in enumerate(ids) for b in ids[i + 1:]]
print("\n相似对（>0.5）：")
for a, b, s in pairs:
    if s > 0.5:
        print(f"  {a}-{b}: {s:.3f}")

# ===== 练习题 =====
# 1. 用第383课的 TF-IDF 权重替换词频，重算相似度矩阵。
# 2. 添加一篇与 A 完全相同的文档，验证余弦为 1.0。
# 3. 实现“找出与文档 A 最不相似的一篇”。
# 4. 思考：余弦相似度在什么情况下会“误判”？（提示：否定词、反义词）
