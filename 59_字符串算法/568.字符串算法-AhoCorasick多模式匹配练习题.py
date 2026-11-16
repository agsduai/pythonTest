# ===== 第568课：字符串算法-Aho-Corasick多模式匹配 =====
# 知识点：
#   - 多模式匹配：一次扫描文本，同时找出所有模式串（敏感词过滤、关键词高亮）
#   - AC 自动机 = Trie（第419课）+ 失败指针（类似 KMP 的 π 表）+ 输出集合
#   - 失败指针：当前节点匹配失败时，跳到“最长后缀仍是 Trie 前缀”的节点
#   - BFS 构建失败指针；每个节点的 outputs 合并失败节点的 outputs
#   - 搜索 O(n + 匹配数)，与模式数量无关
#   - 与第563-566课的单模式算法对比：多模式不能逐个跑
# 依赖：无
from collections import deque


class ACNode:
    __slots__ = ("children", "fail", "outputs")

    def __init__(self):
        self.children: dict[str, "ACNode"] = {}
        self.fail: "ACNode | None" = None
        self.outputs: list[str] = []


class AhoCorasick:

    def __init__(self):
        self.root = ACNode()

    def add(self, word: str):
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, ACNode())
        node.outputs.append(word)

    def build(self):
        """BFS 构建失败指针与输出集合。"""
        queue = deque()
        for child in self.root.children.values():
            child.fail = self.root
            queue.append(child)

        while queue:
            node = queue.popleft()
            for ch, child in node.children.items():
                f = node.fail
                while f is not None and ch not in f.children:
                    f = f.fail
                child.fail = f.children[ch] if f is not None and ch in f.children else self.root
                if child.fail is child:              # 防御：避免自指
                    child.fail = self.root
                child.outputs.extend(child.fail.outputs)
                queue.append(child)

    def search(self, text: str) -> list[tuple[int, str]]:
        """返回 [(起始下标, 命中的模式)]，按结束位置顺序。"""
        result = []
        node = self.root
        for i, ch in enumerate(text):
            while node is not self.root and ch not in node.children:
                node = node.fail
            node = node.children.get(ch, self.root)
            for word in node.outputs:
                result.append((i - len(word) + 1, word))
        return result


ac = AhoCorasick()
for w in ("he", "she", "his", "hers"):
    ac.add(w)
ac.build()

print("== 模式集合 ==")
print("  ", ["he", "she", "his", "hers"])

text = "ushers"
matches = ac.search(text)
print(f"\n== 搜索 {text!r} ==")
for pos, word in matches:
    print(f"  位置 {pos}: {word!r}")

# ---- 敏感词示例 ----
print("\n== 敏感词扫描 ==")
bad_words = ["坏词", "违规", "广告", "spam"]
ac2 = AhoCorasick()
for w in bad_words:
    ac2.add(w)
ac2.build()

samples = [
    "这是一条正常消息",
    "这里有坏词和广告",
    "spam 和 违规内容都要拦",
    "坏词坏词连续出现",
]
for text in samples:
    hits = ac2.search(text)
    print(f"  {text!r} → {[(p, w) for p, w in hits]}")

# ---- 与逐模式暴力对比 ----
print("\n== 与逐个模式搜索对比 ==")
def naive_multi(text, words):
    result = []
    for w in words:
        start = text.find(w)
        while start != -1:
            result.append((start, w))
            start = text.find(w, start + 1)
    return sorted(result)

for text in samples:
    a = sorted(ac2.search(text))
    b = naive_multi(text, bad_words)
    print(f"  {text!r}: AC={a} | 暴力={b} | 一致={a == b}")

# ---- 结构说明 ----
print("\n== 结构说明 ==")
for item in [
    "Trie：共享前缀，插入 O(长度)",
    "失败指针：失配时跳到最长后缀，保证不重扫文本",
    "outputs 合并：命中一个节点时，把后缀模式也一起输出",
    "构建 O(总模式长度)；搜索 O(文本长度 + 命中数)",
    "与 KMP 的关系：单模式的 π 表 ≈ 失败指针的简化版",
]:
    print("  -", item)

# ---- 注意 ----
print("\n== 注意 ==")
for item in [
    "中文按字符建 Trie 即可（不需要分词）",
    "大小写/全半角要提前归一化",
    "重叠命中会全部返回（如 he/she 在 she 中同时命中）",
    "超大词库要注意内存；可用双数组 Trie 压缩",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 统计每个敏感词命中的次数。
# 2. 实现不区分大小写的搜索（统一转小写后建树）。
# 3. 返回最长的命中词（同一位置重叠时优先长词）。
# 4. 思考：为什么 AC 自动机的搜索时间与模式数量无关？
