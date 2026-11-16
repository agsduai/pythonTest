# ===== 第811课：自然语言处理与语言模型-文本规范化与分词 =====
# 知识点：
#   - 文本规范化 pipeline：小写化 -> 标点/URL 处理 -> 分词 -> 停用词/词形还原
#   - 英文分词：空格 + 标点分割；正则分词器是工业标准
#   - 中文分词：无空格分隔，可用「正向最大匹配」「n-gram 统计」「jieba」
#   - 词形还原 lemmatization vs 词干提取 stemming：前者更准但需词典
#   - BPE (Byte Pair Encoding)：子词切分，现代 LLM 的分词方案
#   - 与第36章的区别：36 做搜索/分类的特征提取，这里做「规范化 + 分词算法本身」
# 依赖：无（标准库）
import re
from collections import Counter


def normalize(text):
    """基础规范化。"""
    text = text.lower()
    text = re.sub(r"https?://\S+", " <URL> ", text)         # URL 替换
    text = re.sub(r"\d+", " <NUM> ", text)                   # 数字替换
    text = re.sub(r"\s+", " ", text).strip()                 # 合并空白
    return text


def tokenize_english(text):
    """正则分词器：字母数字序列或标点各为一个 token。"""
    return re.findall(r"[a-z']+|[.,!?;:]", text.lower())


STOPWORDS = {"the", "a", "an", "is", "in", "it", "of", "to", "and", "for", "on"}

def remove_stopwords(tokens, stopwords=STOPWORDS):
    return [t for t in tokens if t not in stopwords]


def simple_stem(token):
    """简化 Porter 词干提取（去 -ing/-ed/-s/-er 等）。"""
    suffixes = [("ing", ""), ("ied", "y"), ("ed", ""), ("ly", ""),
                ("ers", ""), ("er", ""), ("ies", "y"), ("s", "")]
    for suffix, replacement in suffixes:
        if token.endswith(suffix) and len(token) > len(suffix) + 2:
            return token[:-len(suffix)] + replacement
    return token


print("== 文本规范化 ==")
raw = "  Check out https://example.com for more info!   The price is 99.99 dollars.  "
print(f"  原文: {raw!r}")
print(f"  规范化: {normalize(raw)!r}")

print("\n== 英文分词 ==")
text = "Hello, world! This is a test."
print(f"  原文: {text}")
print(f"  分词: {tokenize_english(text)}")

print("\n== 停用词移除 ==")
tokens = tokenize_english("The quick brown fox is jumping over the lazy dog")
filtered = remove_stopwords(tokens)
print(f"  原始: {tokens}")
print(f"  过滤: {filtered}")

print("\n== 简单词干提取 ==")
for word in ("running", "jumped", "cats", "studies", "programming", "better"):
    print(f"  {word:<14} -> {simple_stem(word)}")
print("  简化版可能出错（better -> bet）；真实用 NLTK/SpaCy 的 PorterStemmer")

print("\n== 中文分词：正向最大匹配 ==")
DICT = {"自然语言", "处理", "是", "人工", "智能", "的", "核心", "技术", "之一",
        "深度", "学习", "模型", "语言", "机器", "翻译", "文本", "分类"}
def segment_chinese(text, dictionary, max_len=5):
    """正向最大匹配分词。"""
    result = []
    i = 0
    while i < len(text):
        matched = None
        for length in range(min(max_len, len(text)-i), 0, -1):
            cand = text[i:i+length]
            if cand in dictionary:
                matched = cand; break
        if matched:
            result.append(matched); i += len(matched)
        else:
            result.append(text[i]); i += 1      # 单字
    return result

for text in ("自然语言处理是人工智能的核心技术", "深度学习模型"):
    seg = segment_chinese(text, DICT)
    print(f"  {text} -> {' / '.join(seg)}")
print("  正向最大匹配简单但不保证最优；jieba 用 HMM+词典混合方案")

print("\n== BPE 子词切分（简化版） ==")
def bpe_train(corpus, merges=10):
    """从语料学习 BPE 合并规则。"""
    # 统计字符频率
    vocab = Counter()
    for word in corpus:
        for c in word:
            vocab[c] += 1
        vocab["</w>"] += 1
    pairs = Counter()
    for word in corpus:
        symbols = list(word) + ["</w>"]
        for a, b in zip(symbols, symbols[1:]):
            pairs[(a, b)] += 1
    rules = []
    for _ in range(merges):
        if not pairs: break
        best = pairs.most_common(1)[0][0]
        rules.append(best)
        pairs = Counter({k: v for k, v in pairs.items()
                        if k != best})
        # 简化：不再重扫全语料
    return rules

corpus = ["low", "lowest", "newer", "wider", "low", "low"]
rules = bpe_train(corpus, merges=5)
print(f"  语料: {corpus}")
print(f"  BPE 合并规则（前 5）: {rules}")
print("  BPE 是 GPT/BERT 等 LLM 的分词方案：高频子词合并成单 token")

print("\n== N-gram 切分（字符级） ==")
def char_ngrams(text, n):
    return [text[i:i+n] for i in range(len(text)-n+1)]

for n in (1, 2, 3):
    print(f"  {n}-gram of 'hello': {char_ngrams('hello', n)}")
print("  字符 n-gram 不需要词典，适合拼写纠错与语言识别（第812课）")

print("\n== 规范化 pipeline 总结 ==")
for line in (
    "  1. 小写化 / URL/数字替换",
    "  2. 分词（英文正则 / 中文词典或 BPE）",
    "  3. 停用词移除（搜索场景保留，语言模型保留全部）",
    "  4. 词形还原/词干提取（可选）",
    "  5. N-gram 构造（后续步骤的输入）",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  规范化必须一致：训练和推理用同一套 pipeline",
    "  停用词表按场景选择：搜索引擎去掉，情感分析可能保留否定词",
    "  中文分词用 jieba/pkuseg，BPE 用 HuggingFace tokenizers 库",
    "  规范化丢失的信息（大小写、标点）在 NER/语法分析中很重要",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现逆向最大匹配中文分词，与正向结果对比。
# 2. 给 BPE 加「学习真实合并规则」的完整实现（扫描语料更新 pairs）。
# 3. 用 re 写一个「HTML 标签感知」的分词器。
# 4. 思考：为什么 LLM 用 BPE 而不是词典分词？
