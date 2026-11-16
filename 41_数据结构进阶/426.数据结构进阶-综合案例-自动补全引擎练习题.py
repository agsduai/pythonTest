# ===== 第426课：数据结构进阶-综合案例-自动补全引擎 =====
# 知识点：
#   - 综合运用：Trie（419）+ 堆 TopK（331）+ LRU 缓存（421）
#   - 引擎能力：索引词条与热度、前缀补全、搜索后热度上升、缓存加速
#   - 热度更新会导致缓存失效 —— 本课用“整表清空”保守处理
#   - 真实系统还会加：拼音首字母、纠错（387）、分词（382）、分布式存储
import heapq
from collections import OrderedDict


class SuggestNode:
    __slots__ = ("children", "freq")

    def __init__(self):
        self.children: dict[str, "SuggestNode"] = {}
        self.freq = 0                    # 词尾节点的搜索次数


class AutocompleteEngine:

    def __init__(self, cache_size: int = 32):
        self.root = SuggestNode()
        self.cache: OrderedDict = OrderedDict()
        self.cache_size = cache_size
        self.cache_hits = 0
        self.cache_misses = 0

    # ---------------- 索引 ----------------
    def index(self, word: str, freq: int = 1):
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, SuggestNode())
        node.freq += freq
        self.cache.clear()               # 数据变了，旧补全结果全部作废

    # ---------------- 补全 ----------------
    def _walk(self, prefix: str):
        node = self.root
        for ch in prefix:
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def _collect(self, node: SuggestNode, prefix: str):
        results = []
        if node.freq:
            results.append((prefix, node.freq))
        for ch, child in node.children.items():
            results.extend(self._collect(child, prefix + ch))
        return results

    def suggest(self, prefix: str, k: int = 5) -> list[tuple[str, int]]:
        key = (prefix, k)
        if key in self.cache:
            self.cache_hits += 1
            self.cache.move_to_end(key)
            return self.cache[key]

        self.cache_misses += 1
        node = self._walk(prefix)
        if node is None:
            result = []
        else:
            candidates = self._collect(node, prefix)
            result = heapq.nlargest(k, candidates, key=lambda x: x[1])

        self.cache[key] = result
        if len(self.cache) > self.cache_size:
            self.cache.popitem(last=False)     # 淘汰最旧
        return result

    # ---------------- 用户搜索（同时提升热度） ----------------
    def search(self, word: str):
        self.index(word, freq=1)
        return f"搜索「{word}」完成"

    def stats(self):
        return {"hits": self.cache_hits, "misses": self.cache_misses,
                "cached_prefixes": len(self.cache)}


engine = AutocompleteEngine(cache_size=4)

QUERIES = {
    "python基础": 120, "python进阶": 90, "python爬虫": 70,
    "pandas教程": 80, "数据分析": 60, "数据可视化": 40,
    "机器学习": 55, "深度学习": 35, "pytorch入门": 50,
}
for word, freq in QUERIES.items():
    engine.index(word, freq)

print("== 初始补全 ==")
for prefix in ("python", "数据", "py", "机器", "x"):
    print(f"  {prefix!r:10s} → {engine.suggest(prefix)}")

print("\n== 用户连续搜索 pytorch入门 3 次 ==")
for _ in range(3):
    engine.search("pytorch入门")
print("  'py' 补全：", engine.suggest("py"))

print("\n== 缓存统计 ==")
# 再查两次同样的前缀，命中缓存
engine.suggest("python", 5)
engine.suggest("python", 5)
print(" ", engine.stats())
print("  说明：热度更新会清空缓存；真实系统可只失效受影响的前缀")

# ---- 延迟对比：Trie + 缓存 vs 每次全量扫描 ----
import timeit

def scan(prefix):
    return [(w, f) for w, f in QUERIES.items() if w.startswith(prefix)]

t_scan = timeit.timeit(lambda: scan("py"), number=10000)
t_engine = timeit.timeit(lambda: engine.suggest("py", 5), number=10000)
print("\n== 性能对比（1 万次查询）==")
print(f"  全量扫描：{t_scan:.4f}s | Trie+缓存：{t_engine:.4f}s")

# ---- 输出最终 Top5 ----
print("\n== 全局热度 Top5 ==")
all_words = [(w, f) for w, f in QUERIES.items()]
for word, freq in heapq.nlargest(5, all_words, key=lambda x: x[1]):
    print(f"  {word:12s} {freq}")

# ===== 练习题 =====
# 1. 给引擎增加“中文按首字 + 拼音首字母”双索引（拼音表可手写小字典）。
# 2. 把整表清空缓存改成“只失效以该前缀开头的缓存项”。
# 3. 持久化索引到 JSON（第232课），启动时加载。
# 4. 思考：热搜榜要求“近 1 小时热度”，用现有结构怎么改造？
