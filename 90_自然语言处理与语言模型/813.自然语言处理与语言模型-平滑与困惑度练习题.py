# ===== 第813课：自然语言处理与语言模型-平滑与困惑度 =====
# 知识点：
#   - 零概率问题：训练语料没见过的 n-gram，MLE 给 P=0，整句概率坍缩
#   - Laplace (加 1) 平滑：P(w|ctx) = (count+1)/(count_ctx+V)，V 为词表大小
#   - Add-k 平滑：k 可调，k=1 即 Laplace；k 太大过度平滑
#   - 良好折中 Good-Turing：把 count=c 的质量按 c+1 的期望重新分配
#   - 困惑度 perplexity = 2^(avg log loss)：语言模型的「平均分支因子」
#   - 评估：在留出集（测试集）上计算困惑度，越低越好
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
TRAIN = CORPUS[:5]
TEST = CORPUS[5:]

def tokenize(text): return text.split()


def build_model(corpus, n=2):
    model = defaultdict(Counter)
    vocab = set()
    for line in corpus:
        tokens = ["<s>"]*(n-1) + tokenize(line) + ["</s>"]
        vocab.update(tokens)
        for i in range(len(tokens)-n+1):
            ctx = tuple(tokens[i:i+n-1])
            model[ctx][tokens[i+n-1]] += 1
    return model, len(vocab)


def mle_prob(model, ctx, word):
    cc = sum(model.get(ctx, Counter()).values())
    cw = model.get(ctx, Counter()).get(word, 0)
    return cw / cc if cc else 0.0


def laplace_prob(model, ctx, word, vocab_size, k=1.0):
    cc = sum(model.get(ctx, Counter()).values())
    cw = model.get(ctx, Counter()).get(word, 0)
    return (cw + k) / (cc + k * vocab_size)


def perplexity(model, test_corpus, n, prob_fn):
    total_log2 = 0.0
    total_tokens = 0
    for line in test_corpus:
        tokens = ["<s>"]*(n-1) + tokenize(line) + ["</s>"]
        for i in range(len(tokens)-n+1):
            ctx = tuple(tokens[i:i+n-1])
            word = tokens[i+n-1]
            p = prob_fn(model, ctx, word)
            total_log2 += math.log2(p) if p > 0 else -math.inf
            total_tokens += 1
    if total_log2 == -math.inf:
        return math.inf
    return 2 ** (-total_log2 / total_tokens)


print("== 零概率问题 ==")
m2, V = build_model(TRAIN, n=2)
print(f"  训练集词表 V={V}")
for ctx, word in ((("cat",), "danced"), (("mat",), "on"), (("fish",), "cat")):
    mle = mle_prob(m2, ctx, word)
    lap = laplace_prob(m2, ctx, word, V)
    print(f"  P_MLE({word}|{ctx[0]})={mle:.4f}  P_laplace={lap:.6f}")
print("  MLE 的 count=0 直接给 0；Laplace 给一个小但非零的概率")

print("\n== 困惑度对比：MLE vs Laplace ==")
print(f"  {'模型':<14}{'训练集 PP':>14}{'测试集 PP':>14}")
for name, fn in (("MLE", lambda m, c, w: mle_prob(m, c, w)),
                 ("Laplace(1)", lambda m, c, w: laplace_prob(m, c, w, V, 1.0))):
    pp_train = perplexity(m2, TRAIN, 2, fn)
    pp_test = perplexity(m2, TEST, 2, fn)
    print(f"  {name:<14}{pp_train:>14.2f}{pp_test:>14.2f}")
print("  MLE 在测试集上困惑度 = ∞（count=0 坍缩）；Laplace 给出有限值")

print("\n== Add-k 平滑的超参扫描 ==")
print(f"  {'k':<10}{'测试集 PP':>14}")
for k in (0.001, 0.01, 0.1, 0.5, 1.0, 2.0, 5.0):
    pp = perplexity(m2, TEST, 2, lambda m, c, w, k=k: laplace_prob(m, c, w, V, k))
    print(f"  {k:<10.3f}{pp:>14.2f}")
print("  k 太小接近 MLE（测试集坍缩），太大过度平滑；最优 k 通常 < 1")

print("\n== Good-Turing 平滑（简化版） ==")
def good_turing_prob(model, ctx, word, vocab_size):
    cc = sum(model.get(ctx, Counter()).values())
    cw = model.get(ctx, Counter()).get(word, 0)
    if cw > 0:
        # count c -> c* = (c+1)·N_{c+1}/N_c（需要全局计数信息，简化处理）
        return cw / (cc + 1)
    # count=0 的概率质量 = N_1 / N（N_1 为出现 1 次的 n-gram 种类数）
    # 简化：给固定小概率
    return 0.5 / max(1, cc)
print("  Good-Turing 把 count=1 的概率质量重新分配给 count=0 的事件")
print("  简化版结果:")
for ctx, word in ((("cat",), "sat"), (("cat",), "danced")):
    mle = mle_prob(m2, ctx, word)
    gt = good_turing_prob(m2, ctx, word, V)
    print(f"  P_GT({word}|{ctx[0]})={gt:.6f}")

print("\n== N 值对困惑度的影响 ==")
for n in (1, 2, 3):
    m_n, V_n = build_model(TRAIN, n=n)
    pp_test = perplexity(m_n, TEST, n, lambda m, c, w: laplace_prob(m, c, w, V_n, 0.5))
    pp_train = perplexity(m_n, TRAIN, n, lambda m, c, w: laplace_prob(m, c, w, V_n, 0.5))
    print(f"  n={n}: 训练PP={pp_train:.2f} 测试PP={pp_test:.2f}")
print("  n 大时训练 PP 低但测试 PP 高（过拟合）；n 小则欠拟合")
print("  最优 n 取决于语料量与任务，通常 2~3")

print("\n== 困惑度的解读 ==")
for line in (
    "  PP = 2^(avg log loss) ≈ 词汇表的「有效大小」",
    "  PP=1 完美预测；PP=V 等价于均匀猜测",
    "  英文 bigram PP 通常 50~200；GPT-4 的 PP 远低于此",
    "  不同模型/分词器的 PP 不能直接比较（token 定义不同）",
):
    print(" ", line)

print("\n== 与现代 LM 的联系 ==")
for line in [
    "  GPT 的损失函数 = cross-entropy = log(perplexity)（等价）",
    "  LLM 的 top-p / top-k 采样就是「动态平滑」策略",
    "  良好折中 / Kneser-Ney 是统计 LM 的黄金标准",
    "  神经 LM 用 softmax + cross-entropy 替代显式平滑",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Kneser-Ney 平滑（低阶计数替代高阶计数）并对比困惑度。
# 2. 实现插值平滑（Jelinek-Mercer）：λ·P_n + (1-λ)·P_{n-1}。
# 3. 画出困惑度随 n 变化的曲线，标注过拟合/欠拟合区域。
# 4. 思考：为什么困惑度不能跨不同分词器的模型直接比较？
