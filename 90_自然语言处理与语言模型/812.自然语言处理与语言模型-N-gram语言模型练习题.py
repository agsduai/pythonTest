# ===== 第812课：自然语言处理与语言模型-N-gram语言模型 =====
# 知识点：
#   - 语言模型 LM：给句子打概率 P(w1,...,wn)，评估一句话「是否像人说的」
#   - N-gram 假设：P(w_i | w_{i-n+1}...w_{i-1}) 只依赖前 n-1 个词（马尔可夫性）
#   - 最大似然估计 MLE：P(w_i|context) = count(context, w_i) / count(context)
#   - 数据稀疏：n 越大，count=0 的 context 越多 → 必须平滑（第813课）
#   - 生成：按概率采样下一个词，可生成「像训练语料」的新句子
#   - 与 BPE 结合：字符级 n-gram 不需要分词，天然处理未登录词
# 依赖：无（标准库）
import math
import random
from collections import Counter, defaultdict

CORPUS = [
    "the cat sat on the mat",
    "the cat ate the mouse",
    "the dog sat on the mat and the cat ate the fish",
    "a dog sat near the cat and the dog saw the cat",
    "the cat and the dog play on the mat",
    "the fish sat on the mat near the cat",
    "a cat ate a fish and the dog ate the cat",
]

def tokenize(text): return text.split()

def build_ngram_model(corpus, n=2):
    """构建 n-gram 语言模型：返回 {context: {next_word: count}}。"""
    model = defaultdict(Counter)
    for line in corpus:
        tokens = ["<s>"] * (n-1) + tokenize(line) + ["</s>"]
        for i in range(len(tokens) - n + 1):
            context = tuple(tokens[i:i+n-1])
            word = tokens[i+n-1]
            model[context][word] += 1
    return model


def prob_ngram(model, context, word, n, vocab_size=1000):
    """MLE 概率 P(word|context)。"""
    count_ctx = sum(model.get(context, {}).values())
    count_joint = model.get(context, Counter()).get(word, 0)
    if count_ctx == 0:
        return 1 / vocab_size            # 未见过的 context：均匀兜底
    return count_joint / count_ctx


def sentence_prob(model, text, n, vocab_size=1000):
    tokens = ["<s>"] * (n-1) + tokenize(text) + ["</s>"]
    log_prob = 0.0
    for i in range(len(tokens) - n + 1):
        context = tuple(tokens[i:i+n-1])
        word = tokens[i+n-1]
        p = prob_ngram(model, context, word, n, vocab_size)
        log_prob += math.log2(p) if p > 0 else -20.0    # OOV 兜底
    return 2 ** log_prob, log_prob


def generate(model, n=2, max_len=15, seed=0):
    rng = random.Random(seed)
    tokens = ["<s>"] * (n-1)
    out = []
    for _ in range(max_len):
        context = tuple(tokens[-(n-1):]) if n > 1 else ()
        candidates = model.get(context, Counter())
        if not candidates:
            break
        words, probs = [], []
        total = sum(candidates.values())
        for w, c in candidates.items():
            words.append(w); probs.append(c/total)
        chosen = rng.choices(words, weights=probs)[0]
        if chosen == "</s>":
            break
        out.append(chosen)
        tokens.append(chosen)
    return " ".join(out)


print("== 构建 2-gram（bigram）模型 ==")
m2 = build_ngram_model(CORPUS, n=2)
print(f"  训练语料 {len(CORPUS)} 句")
print(f"  上下文种类: {len(m2)}")
for ctx in list(m2)[:6]:
    print(f"    {ctx}: {dict(m2[ctx])}")

print("\n== P(w|context) ==")
for ctx, word in ((("the",), "cat"), (("the",), "dog"), (("the",), "fish"),
                  (("cat",), "sat"), (("cat",), "flew")):
    p = prob_ngram(m2, ctx, word, 2)
    print(f"  P({word}|{ctx[0]}) = {p:.4f}")

print("\n== 句子概率 ==")
for text in ("the cat sat on the mat", "the mat ate the cat",
             "cat the on mat the sat", "the dog ate the fish"):
    prob, lp = sentence_prob(m2, text, 2)
    print(f"  {text!r:<42} -> P={prob:.6f}  log2P={lp:.2f}")
print("  语法正确的句子概率更高；乱序句子概率急剧下降")

print("\n== 2-gram vs 3-gram 对比 ==")
m3 = build_ngram_model(CORPUS, n=3)
print("  2-gram（bigram）:")
for text in ("the cat sat on the mat", "the cat ate the fish"):
    p, lp = sentence_prob(m2, text, 2)
    print(f"    {text!r:<38} P={p:.8f}")
print("  3-gram（trigram）:")
for text in ("the cat sat on the mat", "the cat ate the fish"):
    p, lp = sentence_prob(m3, text, 3)
    print(f"    {text!r:<38} P={p:.10f}")
print("  3-gram 有更多上下文但更多 count=0 → 需要 smoothing（第813课）")

print("\n== 文本生成 ==")
print("  bigram 生成（seed=1,2,3）:")
for seed in (1, 2, 3):
    print(f"    {generate(m2, n=2, seed=seed)!r}")
print("  trigram 生成（seed=1,2）:")
for seed in (1, 2):
    print(f"    {generate(m3, n=3, seed=seed)!r}")
print("  bigram 语法可能断裂（只看前一个词）；trigram 更连贯但仍有限")

print("\n== 未登录词（OOV）问题 ==")
oov_text = "the elephant danced gracefully"
p, lp = sentence_prob(m2, oov_text, 2)
print(f"  {oov_text!r}: P={p:.10f}")
print("  elephant/danced 不在训练语料 → count=0 → 概率坍缩")
print("  解决方案：Laplace 平滑 / 良好折中 / BPE 子词（第813课）")

print("\n== 工程要点 ==")
for line in [
    "  n-gram 模型是「统计型 LM」；GPT 等是「神经型 LM」，原理相通",
    "  两者都预测下一个 token；区别在于上下文的表示方式",
    "  n-gram 内存 O(语料去重 n-gram 数)；GPT 是参数量 × 4 字节",
    "  评估指标：困惑度 perplexity = 2^(avg log loss)，越低越好（第813课）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 4-gram 模型，观察上下文种类和 count=0 的比例。
# 2. 实现「下一词预测」函数：给定前缀返回 top-3 候选词及概率。
# 3. 对比不同 n 值的文本生成质量（人工评估连贯性）。
# 4. 思考：为什么语言模型的马尔可夫假设在大 n 时失效？
