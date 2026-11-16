# ===== 第419课：数据结构进阶-Trie前缀树 =====
# 知识点：
#   - Trie（字典树）：按字符逐层建树，公共前缀共享路径
#   - 三个核心操作：insert / search / starts_with，均为 O(长度)
#   - 自动补全：找到前缀节点后 DFS 收集所有后缀
#   - 比“遍历全部单词做 startswith”快得多（数据量大时差距明显）
#   - 应用：搜索框补全、拼写检查词表、IP 路由、敏感词过滤


class TrieNode:

    __slots__ = ("children", "is_end", "count")

    def __init__(self):
        self.children: dict[str, "TrieNode"] = {}
        self.is_end = False
        self.count = 0              # 该词被插入/搜索的次数（用于热度排序）


class Trie:

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str, count: int = 1):
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
        node.is_end = True
        node.count += count

    def search(self, word: str) -> bool:
        node = self._walk(word)
        return node is not None and node.is_end

    def starts_with(self, prefix: str) -> bool:
        return self._walk(prefix) is not None

    def _walk(self, text: str) -> TrieNode | None:
        node = self.root
        for ch in text:
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def autocomplete(self, prefix: str, limit: int = 5) -> list[tuple[str, int]]:
        """返回前缀匹配的词及热度，按热度降序。"""
        node = self._walk(prefix)
        if node is None:
            return []
        results: list[tuple[str, int]] = []

        def dfs(current: TrieNode, path: str):
            if current.is_end:
                results.append((path, current.count))
            for ch, child in current.children.items():
                dfs(child, path + ch)

        dfs(node, prefix)
        results.sort(key=lambda x: (-x[1], x[0]))
        return results[:limit]


trie = Trie()
for word, hot in [
    ("python", 100), ("pytorch", 60), ("pandas", 80), ("pattern", 20),
    ("java", 70), ("javascript", 65), ("json", 40), ("jungle", 5),
]:
    trie.insert(word, hot)

print("== 基础查询 ==")
for word in ("python", "py", "java", "json", "ruby"):
    print(f"  search({word!r}) = {trie.search(word)} | "
          f"starts_with = {trie.starts_with(word)}")

print("\n== 自动补全 ==")
for prefix in ("py", "ja", "j", "x"):
    print(f"  {prefix!r:5s} → {trie.autocomplete(prefix)}")

# ---- 热度更新：用户每搜一次，计数 +1 ----
print("\n== 热度更新 ==")
trie.insert("pytorch", 100)         # 模拟又搜了 100 次
print("  py 补全：", trie.autocomplete("py"))
print("  pytorch 已升到第一")

# ---- 与“列表遍历”对比：前缀越短，Trie 的优势越明显 ----
WORDS = [w for w, _ in [("python", 0), ("pytorch", 0), ("pandas", 0),
                        ("pattern", 0), ("java", 0), ("javascript", 0),
                        ("json", 0), ("jungle", 0)]]

def brute_force(prefix):
    return [w for w in WORDS if w.startswith(prefix)]

print("\n== 暴力对照 ==")
print("  暴力 py：", brute_force("py"), "| Trie：", [w for w, _ in trie.autocomplete("py")])
print("  小数据差不多，10 万词表时 Trie 只走前缀路径，暴力要扫全表")

# ===== 练习题 =====
# 1. 给 Trie 增加 delete(word)（注意清理无用节点）。
# 2. 实现 count_prefix(prefix)：返回以该前缀开头的单词数量。
# 3. 用 Trie 实现敏感词检测：给一段文本，返回命中的词（提示：逐位置走树）。
# 4. 思考：Trie 的内存开销主要在哪？中文场景有什么不同？
