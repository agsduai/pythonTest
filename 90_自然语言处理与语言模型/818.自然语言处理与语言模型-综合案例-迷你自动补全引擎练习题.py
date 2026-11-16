# ===== 第818课：自然语言处理与语言模型-综合案例-迷你自动补全引擎 =====
# 知识点：
#   - 综合串起本章：分词 -> n-gram 统计 -> 平滑 -> next-word 预测 -> top-k 建议
#   - 自动补全输入法：用户打字 -> 查前缀匹配 -> 按 (频率 × 上下文概率) 排序建议
#   - 分层：词典层（词频）+ n-gram 层（上下文）+ 编辑距离层（纠错，第814课）
#   - 前缀树 Trie：O(前缀长度) 查找所有匹配词，比线性扫快
#   - 每层可独立替换/加权组合，便于迭代与调优
#   - 全部标准库 + 固定语料 + 内存操作，离线可运行
# 依赖：无（标准库）
import math
import re
from collections import Counter, defaultdict


# ---------- 1) 词典与 Trie ----------
class Trie:
    def __init__(self):
        self.children = {}
        self.is_word = False
        self.freq = 0

    def insert(self, word, freq):
        node = self
        for ch in word:
            node = node.children.setdefault(ch, Trie())
        node.is_word = True
        node.freq = freq

    def words_with_prefix(self, prefix):
        node = self
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
        results = []
        def collect(node, prefix):
            if node.is_word:
                results.append((prefix, node.freq))
            for ch, child in node.children.items():
                collect(child, prefix + ch)
        collect(node, prefix)
        return results


class NGramModel:
    def __init__(self, n=2):
        self.n = n
        self.model = defaultdict(Counter)
        self.vocab_size = 0

    def train(self, sentences):
        for sent in sentences:
            toks = sent.lower().split()
            self.vocab_size += len(set(toks))
            tokens = ["<s>"]*(self.n-1) + toks + ["</s>"]
            for i in range(len(tokens)-self.n+1):
                ctx = tuple(tokens[i:i+self.n-1])
                self.model[ctx][tokens[i+self.n-1]] += 1

    def next_word_probs(self, context):
        if isinstance(context, str):
            context = context.lower().split()
        ctx = tuple(context)[-(self.n-1):]
        total = sum(self.model.get(ctx, Counter()).values())
        if not total:
            return {}
        return {w: c/total for w, c in self.model[ctx].items()}


# ---------- 2) 编辑距离（复用第36章，此处为内联简化） ----------
def edit_distance(a, b):
    m, n = len(a), len(b)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(m+1): dp[i][0] = i
    for j in range(n+1): dp[0][j] = j
    for i in range(1, m+1):
        for j in range(1, n+1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    return dp[m][n]


# ---------- 3) 自动补全引擎 ----------
class AutoComplete:
    def __init__(self, corpus):
        self.word_freq = Counter()
        self.ngram = NGramModel(n=2)
        self.trie = Trie()
        for sent in corpus:
            toks = sent.lower().split()
            self.word_freq.update(toks)
            self.ngram.train([sent])
        for word, freq in self.word_freq.items():
            self.trie.insert(word, freq)

    def _layer_trie(self, prefix, top_n):
        return sorted(self.trie.words_with_prefix(prefix),
                      key=lambda x: -x[1])[:top_n]

    def _layer_ngram(self, prev_words, top_n):
        probs = self.ngram.next_word_probs(prev_words)
        return sorted(probs.items(), key=lambda x: -x[1])[:top_n]

    def _layer_edit(self, partial, top_n, max_dist=2):
        cands = []
        for word, freq in self.word_freq.items():
            d = edit_distance(partial, word)
            if d <= max_dist and d > 0:
                cands.append((word, freq / (2 ** d)))   # 频率 / 编辑距离惩罚
        return sorted(cands, key=lambda x: -x[1])[:top_n]

    def suggest(self, text, top_n=5):
        """主入口：综合三层建议。"""
        text = text.lower().strip()
        tokens = text.split()
        prefix = tokens[-1] if tokens else ""
        prev_words = tokens[:-1]

        suggestions = {}
        # 层 1: Trie 前缀匹配（权重最高）
        for word, freq in self._layer_trie(prefix, top_n*2):
            score = freq * 1.0
            suggestions[word] = suggestions.get(word, 0) + score
        # 层 2: N-gram 上下文预测
        for word, prob in self._layer_ngram(prev_words, top_n*2):
            score = prob * 500                          # 上下文匹配也加分
            suggestions[word] = suggestions.get(word, 0) + score
        # 层 3: 编辑距离纠错（仅当 Trie 前缀匹配不足时）
        if len(suggestions) < top_n and len(prefix) > 2:
            for word, score in self._layer_edit(prefix, top_n):
                suggestions[word] = suggestions.get(word, 0) + score * 0.3

        ranked = sorted(suggestions.items(), key=lambda x: -x[1])[:top_n]
        return [(w, round(s, 1)) for w, s in ranked]


print("== 构建语料 ==")
CORPUS = [
    "the cat sat on the mat",
    "the cat ate the fish",
    "the dog sat on the mat",
    "the dog ate the bone",
    "the bird sat on the tree",
    "the cat and the dog play together",
    "a cat and a dog are friends",
    "the quick brown fox jumps",
    "the quick brown cat jumps too",
    "the weather is nice today",
    "the cat is sleeping on the mat",
    "the dog is running in the park",
    "she said hello to the cat",
    "he said hello to the dog and the bird",
    "the bird can fly high above the tree",
    "the fish can swim deep in the sea",
]
print(f"  语料 {len(CORPUS)} 句")

engine = AutoComplete(CORPUS)
print(f"  词表 {len(engine.word_freq)} 词，n-gram 上下文 {len(engine.ngram.model)} 种")

print("\n== 自动补全演示 ==")
inputs = [
    ("the ca",     "前缀匹配 + n-gram"),
    ("the dog a",  "多候选 n-gram"),
    ("cat",        "单词前缀"),
    ("teh cat",    "拼写纠错(teh->the)"),
    ("quik br",    "多词纠错"),
    ("bird c",     "不常见前缀"),
]
for text, note in inputs:
    suggestions = engine.suggest(text, top_n=5)
    print(f"\n  输入: {text!r:<18} ({note})")
    for w, s in suggestions:
        print(f"    {w:<10} score={s}")

print("\n== 分层贡献分析 ==")
text = "the ca"
tokens = text.lower().split()
prefix, prev_words = tokens[-1], tokens[:-1]
trie_hits = engine._layer_trie(prefix, 5)
ngram_hits = engine._layer_ngram(prev_words, 5)
print(f"  输入: {text!r}")
print(f"  Trie 层  : {trie_hits}")
print(f"  N-gram 层: {ngram_hits}")
print(f"  综合结果 : {engine.suggest(text)}")
print("  层 1 (Trie) 找到所有 'ca' 开头的词")
print("  层 2 (N-gram) 在 'the' 后给出概率最高的下一个词")

print("\n== Trie vs 线性扫描性能 ==")
import time
prefix = "th"
t0 = time.perf_counter()
for _ in range(10000):
    engine.trie.words_with_prefix(prefix)
t_trie = time.perf_counter() - t0
t0 = time.perf_counter()
for _ in range(10000):
    [w for w in engine.word_freq if w.startswith(prefix)]
t_linear = time.perf_counter() - t0
print(f"  Trie: {t_trie*1000:.2f}ms | 线性扫描: {t_linear*1000:.2f}ms "
      f"加速={t_linear/t_trie if t_trie else 0:.1f}×")

print("\n== 分层回顾 ==")
for line in [
    "  词典层  : Trie 前缀匹配 + 词频排序（本章）",
    "  上下文层: N-gram next-word 预测（第812课）",
    "  纠错层  : 编辑距离候选（第814课噪声信道）",
    "  排序层  : 加权综合 + 截断 top-N",
    "  扩展点  : 加 BPE 分词（第811课）、RLHF 排序（第81章 RL）",
]:
    print("  -", line)

print("\n== 与真实输入法的差距 ==")
for line in [
    "  真实 IME 有拼音→汉字映射、词组优先、个人化频率学习",
    "  更大的语料（GB 级）与更深的 n-gram（3~5）",
    "  用 Transformer 替代 n-gram 做上下文建模（GPT 思路）",
    "  本课是「从零构建完整 NLP 应用」的最小可行版本",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现逐字更新的增量建议（每输入一个字母刷新建议列表）。
# 2. 加「用户历史」层：用户最近用过的词优先建议。
# 3. 用 BPE 分词支持中文和子词补全。
# 4. 思考：为什么自动补全需要三层而不是只用 n-gram 预测？
