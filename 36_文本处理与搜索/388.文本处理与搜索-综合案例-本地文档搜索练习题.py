# ===== 第388课：文本处理与搜索-综合案例-本地文档搜索 =====
# 知识点：
#   - 综合运用：预处理（382）+ TF-IDF（383）+ 倒排索引（385）
#   - 中文无分词库时：单字 + 二元组（bigram）组合，能覆盖大部分查询
#   - 搜索流程：扫描目录 → 建索引 → 查询打分 → 返回片段（snippet）
#   - 真实项目可替换为 jieba 分词 + Whoosh/Elasticsearch，结构不变
# 依赖：无（标准库）

import math
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path


def tokenize(text: str) -> list[str]:
    """英文按词、中文按“单字 + 二元组”，统一小写。"""
    tokens = []
    for seg in re.findall(r"[A-Za-z]+|[\u4e00-\u9fa5]+", text):
        if seg[0].isascii():
            tokens.append(seg.lower())
        else:
            tokens.extend(seg)                                   # 单字
            tokens.extend(seg[i:i + 2] for i in range(len(seg) - 1))  # 二元组
    return tokens


class LocalSearch:

    def __init__(self):
        self.docs: dict[int, dict] = {}          # id -> {path, title, text}
        self.index: dict[str, dict[int, int]] = defaultdict(dict)
        self.doc_len: dict[int, int] = {}

    def add_document(self, path: Path, text: str, title: str = ""):
        doc_id = len(self.docs) + 1
        tokens = tokenize(text)
        self.docs[doc_id] = {"path": path, "title": title or path.stem, "text": text}
        self.doc_len[doc_id] = len(tokens) or 1
        for term in tokens:
            self.index[term][doc_id] = self.index[term].get(doc_id, 0) + 1

    def _idf(self, term: str) -> float:
        df = len(self.index.get(term, {}))
        return math.log(len(self.docs) / (1 + df)) + 1

    def search(self, query: str, top_n: int = 3) -> list[dict]:
        terms = tokenize(query)
        if not terms:
            return []
        scores = defaultdict(float)
        for term in terms:
            for doc_id, tf in self.index.get(term, {}).items():
                scores[doc_id] += tf * self._idf(term) / self.doc_len[doc_id]
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])[:top_n]
        return [{
            "score": round(score, 4),
            **self.docs[doc_id],
            "snippet": self._snippet(self.docs[doc_id]["text"], query),
        } for doc_id, score in ranked]

    @staticmethod
    def _snippet(text: str, query: str, width: int = 36) -> str:
        pos = text.find(query)
        if pos < 0:                       # 没有完整匹配就找首个查询词
            for token in tokenize(query):
                pos = text.find(token)
                if pos >= 0:
                    break
        if pos < 0:
            return text[:width] + "…"
        start = max(0, pos - 12)
        return ("…" if start else "") + text[start:start + width] + "…"


def build_demo_docs(root: Path):
    root.mkdir(exist_ok=True)
    docs = {
        "concurrency.txt": "Python 并发编程：多线程适合 IO 密集任务，多进程适合 CPU 密集任务。"
                           "协程在单线程内通过事件循环实现并发，适合大量网络请求。",
        "pandas.txt": "Pandas 是数据分析的核心库，支持 DataFrame 的清洗、分组、透视表与时间序列处理。"
                      "读取 Excel 与 CSV 是常见入口。",
        "algorithms.txt": "算法入门介绍时间复杂度、排序、查找、哈希表与动态规划。"
                          "二分查找要求数据有序，时间复杂度为 O(log n)。",
    }
    for name, text in docs.items():
        (root / name).write_text(text, encoding="utf-8")


def run_demo():
    work = Path("search_demo_388")
    build_demo_docs(work)

    engine = LocalSearch()
    for path in sorted(work.glob("*.txt")):
        engine.add_document(path, path.read_text(encoding="utf-8"))

    print(f"已索引 {len(engine.docs)} 篇文档，词项 {len(engine.index)} 个")

    for query in ["并发 编程", "数据分析", "二分查找", "Excel"]:
        print(f"\n查询：{query}")
        results = engine.search(query, top_n=2)
        if not results:
            print("  （无结果）")
        for r in results:
            print(f"  [{r['score']:.3f}] {r['title']}（{r['path'].name}）")
            print(f"        {r['snippet']}")

    shutil.rmtree(work)


run_demo()

# ===== 练习题 =====
# 1. 增加一篇英文文档，验证英文按词、中文按二元组混排正常。
# 2. 给 search 增加 AND 语义：所有查询词必须命中。
# 3. 索引时跳过 .pyc/临时文件，支持把整个项目目录作为语料。
# 4. 思考：bigram 方案对“同义词”（如“协程”与“coroutine”）有效吗？怎么补？
