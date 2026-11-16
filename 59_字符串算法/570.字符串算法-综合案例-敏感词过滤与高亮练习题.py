# ===== 第570课：字符串算法-综合案例-敏感词过滤与高亮 =====
# 知识点：
#   - 综合运用：Aho-Corasick（568）+ 字符串替换 + 高亮
#   - 需求：一次扫描找出所有敏感词，支持：
#     1. 替换为等长 ***（保留长度，避免泄露词长）
#     2. 返回命中位置与词，供高亮/审计
#     3. 大小写不敏感
#     4. 重叠命中全部处理
#   - 与第15章正则替换的区别：AC 适合大词库、多模式、O(n) 扫描
#   - 与第382课分词、第36章文本处理的配合
# 依赖：无
from collections import deque


class ACNode:
    __slots__ = ("children", "fail", "outputs")

    def __init__(self):
        self.children: dict[str, "ACNode"] = {}
        self.fail: "ACNode | None" = None
        self.outputs: list[str] = []


class SensitiveFilter:

    def __init__(self, words: list[str]):
        self.root = ACNode()
        for word in words:
            if word:
                self._add(word.lower())
        self._build()

    def _add(self, word: str):
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, ACNode())
        node.outputs.append(word)

    def _build(self):
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
                child.fail = (f.children[ch]
                              if f is not None and ch in f.children
                              else self.root)
                if child.fail is child:
                    child.fail = self.root
                child.outputs.extend(child.fail.outputs)
                queue.append(child)

    def find_all(self, text: str) -> list[tuple[int, int, str]]:
        """返回 [(start, end, word)]，end 为开区间。"""
        lower = text.lower()
        node = self.root
        hits = []
        for i, ch in enumerate(lower):
            while node is not self.root and ch not in node.children:
                node = node.fail
            node = node.children.get(ch, self.root)
            for word in node.outputs:
                start = i - len(word) + 1
                hits.append((start, i + 1, word))
        return sorted(hits)

    def replace(self, text: str, mask: str = "*") -> tuple[str, list]:
        hits = self.find_all(text)
        if not hits:
            return text, []
        chars = list(text)
        for start, end, _ in hits:
            for i in range(start, end):
                chars[i] = mask
        return "".join(chars), hits

    def highlight(self, text: str, left: str = "[", right: str = "]") -> str:
        hits = self.find_all(text)
        if not hits:
            return text
        # 合并重叠区间，避免标记嵌套
        merged = []
        for start, end, _ in hits:
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        pieces, cursor = [], 0
        for start, end in merged:
            pieces.append(text[cursor:start])
            pieces.append(left + text[start:end] + right)
            cursor = end
        pieces.append(text[cursor:])
        return "".join(pieces)


WORDS = ["坏词", "违规", "广告", "spam", "诈骗", "赌博"]
filter_ = SensitiveFilter(WORDS)

samples = [
    "这是一条正常消息",
    "这里有坏词和广告，还有 spam",
    "违规内容必须处理，坏词坏词连续出现",
    "SPAM 和 Spam 都要拦截",
    "诈骗与赌博是重点",
]

print("== 命中的词 ==")
for text in samples:
    hits = filter_.find_all(text)
    print(f"  {text!r}")
    print(f"    → {[(s, e, w) for s, e, w in hits]}")

print("\n== 替换为 *** ==")
for text in samples:
    masked, hits = filter_.replace(text)
    print(f"  {text!r}")
    print(f"    → {masked!r}")

print("\n== 高亮（合并重叠）==")
for text in samples[:3]:
    print(f"  {filter_.highlight(text)}")

# ---- 与正则/暴力对比 ----
print("\n== 与逐个替换对比 ==")
import re

def regex_replace(text, words, mask="*"):
    pattern = "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
    return re.sub(pattern, lambda m: mask * len(m.group()), text, flags=re.IGNORECASE)


for text in samples:
    ac_result, _ = filter_.replace(text)
    regex_result = regex_replace(text, WORDS)
    print(f"  {text!r}")
    print(f"    AC={ac_result!r}")
    print(f"    RE={regex_result!r} | 一致={ac_result == regex_result}")

# ---- 性能对比 ----
print("\n== 性能对比（大文本、多词库）==")
import timeit

big_text = ("正常内容" * 200 + "坏词" + "正常内容" * 200 + "广告" + "正常内容" * 200)
t_ac = timeit.timeit(lambda: filter_.find_all(big_text), number=100)
t_re = timeit.timeit(lambda: [m for m in re.finditer(
    "|".join(map(re.escape, WORDS)), big_text, re.IGNORECASE)], number=100)
print(f"  AC 扫描 100 次：{t_ac:.4f}s")
print(f"  正则扫描 100 次：{t_re:.4f}s")
print("  词库越大，AC 优势越明显（正则要尝试所有分支）")

# ---- 工程注意 ----
print("\n== 工程注意 ==")
for item in [
    "词库更新要重建自动机（可热加载，第545课）",
    "大小写/全半角/繁简先归一化",
    "替换保留长度可防“通过长度猜词”",
    "审计场景要保留命中词与位置，但日志脱敏",
    "对抗变体（拼音/拆字/谐音）需要额外规则或模型",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 SensitiveFilter 增加 add_word/remove_word（重建自动机）。
# 2. 实现“只替换整词”，不匹配词中词（提示：检查边界）。
# 3. 从文件加载词库，统计每类词命中次数。
# 4. 思考：为什么“保留长度替换”在隐私场景更安全？
