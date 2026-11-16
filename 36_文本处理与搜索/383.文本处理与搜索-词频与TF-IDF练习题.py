# ===== 第383课：文本处理与搜索-词频与TF-IDF =====
# 知识点：
#   - TF（词频）：词在本文档中出现得多 → 对本文档越重要
#   - DF（文档频率）：有多少篇文档含这个词；IDF = log(N / (1+DF)) + 1
#   - TF-IDF = TF × IDF：既看本文档频率，又惩罚“到处都是”的常见词
#   - 归一化：向量除 L2 范数，让长文档短文档可比
#   - 这是搜索引擎排序与文本相似度的数学基础
# 依赖：无（标准库 math / collections）

import math
import re
from collections import Counter

STOPWORDS = set("the a an is are was were to of and in on for with it this that".split())

CORPUS = {
    "doc1": "python is a great programming language for data analysis",
    "doc2": "python and pandas are used for data analysis and machine learning",
    "doc3": "machine learning models need data cleaning and feature engineering",
    "doc4": "the weather in beijing is nice today but i prefer python",
}


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z]+", text.lower())
    return [w for w in words if w not in STOPWORDS]


# ---- 1. 每篇文档的词频 TF ----
tfs = {doc_id: Counter(tokenize(text)) for doc_id, text in CORPUS.items()}
print("doc1 的词频：", tfs["doc1"].most_common(5))

# ---- 2. 文档频率 DF 与 IDF ----
N = len(CORPUS)
df = Counter()
for tf in tfs.values():
    for term in tf:
        df[term] += 1

idf = {term: math.log(N / (1 + d)) + 1 for term, d in df.items()}
print("\n部分词的 IDF（越高越有区分度）：")
for term in ["python", "data", "machine", "great", "weather"]:
    print(f"  {term:10s} DF={df[term]} IDF={idf[term]:.3f}")

# ---- 3. TF-IDF 向量（含 L2 归一化）----
def tfidf_vector(tf: Counter) -> dict[str, float]:
    vec = {term: count * idf.get(term, 1.0) for term, count in tf.items()}
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {term: v / norm for term, v in vec.items()}


vectors = {doc_id: tfidf_vector(tf) for doc_id, tf in tfs.items()}

print("\n每篇文档权重最高的 3 个词：")
for doc_id, vec in vectors.items():
    top3 = sorted(vec.items(), key=lambda kv: -kv[1])[:3]
    print(f"  {doc_id}: " + ", ".join(f"{t}({w:.3f})" for t, w in top3))

# ---- 4. 查询“data analysis”的打分 ----
def score_query(query: str, vec: dict[str, float]) -> float:
    q_tokens = tokenize(query)
    return sum(vec.get(t, 0.0) for t in q_tokens)


print('\n查询 "data analysis" 的排序：')
for doc_id in sorted(CORPUS, key=lambda d: -score_query("data analysis", vectors[d])):
    print(f"  {doc_id}: {score_query('data analysis', vectors[doc_id]):.3f}")

# ===== 练习题 =====
# 1. 打印“python”与“data”在整个语料里的 IDF，解释谁更常见。
# 2. 去掉 L2 归一化，重新排序查询，观察长文档是否占便宜。
# 3. 把 IDF 公式改成 log(N/DF)，对比词权重变化。
# 4. 思考：如果一篇文档把关键词重复 100 次，TF-IDF 如何被“刷分”？怎么防？
