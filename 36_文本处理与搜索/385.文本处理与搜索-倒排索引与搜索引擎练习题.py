# ===== 第385课：文本处理与搜索-倒排索引与搜索引擎 =====
# 知识点：
#   - 正排索引：文档 → 词列表；倒排索引：词 → 文档列表（搜索靠它）
#   - 倒排表 posting：{doc_id: tf}，一个词对应“哪些文档出现过、出现几次”
#   - 查询处理：分词 → 取各词的倒排表 → 交集（AND）/ 并集（OR）
#   - 打分：TF-IDF 加和，越大越相关；排序后返回 TopN
#   - 这就是 Elasticsearch/Lucene 的最小原理模型
# 依赖：无（标准库 math / collections / re）

import math
import re
from collections import defaultdict

DOCS = {
    1: "python is great for data analysis and machine learning",
    2: "python pandas makes data analysis easy",
    3: "machine learning needs feature engineering and data cleaning",
    4: "the weather in beijing is nice today",
}


def tokenize(text: str) -> list[str]:
    stop = {"the", "is", "for", "and", "in", "a", "an", "to", "of", "with", "today"}
    return [w for w in re.findall(r"[a-z]+", text.lower()) if w not in stop]


class InvertedIndex:

    def __init__(self):
        self.index: dict[str, dict[int, int]] = defaultdict(dict)   # 词 -> {doc: tf}
        self.doc_len: dict[int, int] = {}

    def add(self, doc_id: int, text: str):
        tokens = tokenize(text)
        self.doc_len[doc_id] = len(tokens)
        for term in tokens:
            self.index[term][doc_id] = self.index[term].get(doc_id, 0) + 1

    def idf(self, term: str, N: int) -> float:
        df = len(self.index.get(term, {}))
        return math.log(N / (1 + df)) + 1

    def search_and(self, query: str, top_n: int = 3):
        """AND 语义：所有查询词都要出现；TF-IDF 打分排序。"""
        terms = tokenize(query)
        if not terms:
            return []
        # ① 候选：所有词都出现在同一文档里
        doc_sets = [set(self.index.get(t, {})) for t in terms]
        candidates = set.intersection(*doc_sets) if doc_sets else set()

        # ② 打分
        N = len(self.doc_len)
        scored = []
        for doc_id in candidates:
            score = 0.0
            for term in terms:
                tf = self.index[term][doc_id]
                score += tf * self.idf(term, N) / (self.doc_len[doc_id] or 1)
            scored.append((doc_id, score))
        return sorted(scored, key=lambda x: -x[1])[:top_n]

    def search_or(self, query: str, top_n: int = 3):
        """OR 语义：命中任一查询词即可。"""
        terms = tokenize(query)
        scores = defaultdict(float)
        N = len(self.doc_len)
        for term in terms:
            for doc_id, tf in self.index.get(term, {}).items():
                scores[doc_id] += tf * self.idf(term, N) / (self.doc_len[doc_id] or 1)
        return sorted(scores.items(), key=lambda x: -x[1])[:top_n]


idx = InvertedIndex()
for doc_id, text in DOCS.items():
    idx.add(doc_id, text)

print("倒排索引（部分）：")
for term in ["python", "data", "machine", "weather"]:
    print(f"  {term:8s} → {dict(idx.index[term])}")

print("\nAND 查询 'data analysis'：", idx.search_and("data analysis"))
print("AND 查询 'python machine'：", idx.search_and("python machine"))
print("OR  查询 'python weather'：", idx.search_or("python weather"))

# 展示“为什么 AND 是交集”
print("\ndata 出现在：", sorted(idx.index['data']))
print("analysis 出现在：", sorted(idx.index['analysis']))
print("交集 =", sorted(set(idx.index['data']) & set(idx.index['analysis'])))

# ===== 练习题 =====
# 1. 给 InvertedIndex 增加 remove(doc_id)：删除文档并清理倒排表。
# 2. 实现短语查询（"data analysis" 必须相邻出现）。
# 3. 把打分改成 BM25 的简化版，观察排名变化。
# 4. 思考：为什么搜索引擎不直接遍历所有文档做字符串匹配？
