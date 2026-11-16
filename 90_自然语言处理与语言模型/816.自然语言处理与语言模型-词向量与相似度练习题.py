# ===== 第816课：自然语言处理与语言模型-词向量与相似度 =====
# 知识点：
#   - 词向量 word embedding：把词映射到稠密向量，语义相近的词向量相近
#   - one-hot → PPMI（逐点互信息）→ SVD 降维 → dense embedding
#   - PPMI(w, c) = max(0, log2(P(w,c)/(P(w)·P(c))))：正的互信息才算
#   - SVD 截断：取最大的 k 个奇异值，把大稀疏矩阵压缩成低维稠密矩阵
#   - 余弦相似度：cos(θ) = a·b/(|a|·|b|)，忽略量级只看方向
#   - 与 word2vec 的关系：word2vec 用 SGD 直接学稠密向量（跳过 SVD）
#   - 本课手写 PPMI + SVD 管线，标准库实现
# 依赖：无（标准库）
import math
import random
from collections import Counter, defaultdict

CORPUS = [
    "the cat sat on the mat",
    "the dog sat on the mat",
    "the cat chased the dog",
    "the dog chased the cat",
    "the bird flew over the cat",
    "the bird sat on the tree",
    "the cat and the dog play",
    "the bird sings the song",
    "the dog barked at the bird",
    "the cat chased the bird",
]

def tokenize(text): return text.split()

# ---------- 共现矩阵 ----------
def cooccurrence_matrix(corpus, window=2):
    """统计词对在窗口内共现的次数。"""
    vocab = sorted(set(w for s in corpus for w in tokenize(s)))
    word_idx = {w: i for i, w in enumerate(vocab)}
    cooc = defaultdict(lambda: defaultdict(float))
    for sent in corpus:
        tokens = tokenize(sent)
        for i, w in enumerate(tokens):
            for d in range(1, window+1):
                if i-d >= 0:
                    cooc[word_idx[w]][word_idx[tokens[i-d]]] += 1/d
                if i+d < len(tokens):
                    cooc[word_idx[w]][word_idx[tokens[i+d]]] += 1/d
    return vocab, word_idx, cooc

vocab, word_idx, cooc = cooccurrence_matrix(CORPUS, window=2)
N = len(vocab)
print(f"== 共现矩阵 ==")
print(f"  词表大小={N}，窗口=2")
print(f"  词表: {vocab}")

print("\n== 部分共现值 ==")
for w1, w2 in (("cat","dog"), ("cat","mat"), ("bird","fly"), ("cat","sat")):
    i1, i2 = word_idx.get(w1,-1), word_idx.get(w2,-1)
    v = cooc[i1].get(i2, 0) if i1 >= 0 and i2 >= 0 else 0
    print(f"  cooc({w1},{w2}) = {v:.1f}")

print("\n== PPMI 矩阵 ==")
def ppmi(cooc, vocab_size):
    """逐点互信息：PPMI(w,c) = max(0, log2(P(w,c)/(P(w)·P(c))))"""
    total = sum(sum(row.values()) for row in cooc.values())
    word_totals = [sum(cooc[i].values()) for i in range(vocab_size)]
    ppmi = defaultdict(lambda: defaultdict(float))
    for i in range(vocab_size):
        for j, val in cooc[i].items():
            p_ij = val / total
            p_i = word_totals[i] / total
            p_j = word_totals[j] / total
            mi = math.log2(p_ij / (p_i * p_j)) if p_i * p_j > 0 else 0
            ppmi[i][j] = max(0, mi)
    return ppmi

pmi = ppmi(cooc, N)
for w1, w2 in (("cat","dog"), ("cat","fly"), ("sat","mat"), ("dog","barked")):
    i1, i2 = word_idx.get(w1,-1), word_idx.get(w2,-1)
    v = pmi[i1].get(i2, 0) if i1 >= 0 and i2 >= 0 else 0
    print(f"  PPMI({w1},{w2}) = {v:.3f}")

print("\n== 手写 SVD：幂迭代求主特征向量 ==")
def svd_top_k(matrix, k, iterations=100):
    """用幂迭代 + 矩阵降阶求前 k 个奇异值/向量（教学简化版）。"""
    n = len(matrix)
    # 构造实对称方阵 M = X^T · X
    M = [[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            v = matrix[i][j]
            if v != 0:
                for l in range(n):
                    M[i][l] += v * matrix[l][j]
    vectors = []
    work = [row[:] for row in M]
    for _ in range(k):
        v = [1.0/math.sqrt(n)] * n
        for _ in range(iterations):
            nv = [sum(work[i][j]*v[j] for j in range(n)) for i in range(n)]
            norm = math.sqrt(sum(x*x for x in nv)) or 1.0
            v = [x/norm for x in nv]
        eigenval = sum(work[i][j]*v[i]*v[j] for i in range(n) for j in range(n))
        vectors.append((math.sqrt(max(0, eigenval)), v[:]))
        # 矩阵降阶：work -= eigenval * v·v^T
        for i in range(n):
            for j in range(n):
                work[i][j] -= eigenval * v[i] * v[j]
    return vectors


print("\n== SVD 降维（手写幂迭代） ==")
# 把 PPMI 稀疏字典转成稠密列表
dense = [[pmi[i].get(j, 0.0) for j in range(N)] for i in range(N)]
sv = svd_top_k(dense, k=3, iterations=50)
for i, (val, vec) in enumerate(sv):
    print(f"  σ{i} = {val:.3f}  v = {[round(x,3) for x in vec[:6]]}...")

print("\n== 低维词向量（截取前 2 个奇异向量） ==")
k = 2
embeddings = {}
for i, w in enumerate(vocab):
    vec = [sv[j][1][i] * sv[j][0] for j in range(k)]
    embeddings[w] = vec
    print(f"  {w:<8}: {[round(v, 3) for v in vec]}")

print("\n== 余弦相似度 ==")
def cosine(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    la = math.sqrt(sum(x*x for x in a)) or 1
    lb = math.sqrt(sum(x*x for x in b)) or 1
    return dot / (la * lb)

pairs = [("cat","dog"), ("cat","bird"), ("cat","mat"), ("cat","the"),
         ("dog","bird"), ("sat","play")]
for w1, w2 in pairs:
    if w1 in embeddings and w2 in embeddings:
        sim = cosine(embeddings[w1], embeddings[w2])
        print(f"  cos({w1}, {w2}) = {sim:.4f}")

print("\n== 相似度排序 ==")
query = "cat"
ranked = sorted((w, cosine(embeddings[query], embeddings[w]))
                for w in vocab if w != query)
ranked.sort(key=lambda x: -x[1])
print(f"  与 '{query}' 最相似的词:")
for w, s in ranked[:5]:
    print(f"    {w}: {s:.4f}")

print("\n== 方法谱系 ==")
for line in [
    "  count-based: PPMI + SVD（本课，可解释性好）",
    "  word2vec skip-gram: SGD 学稠密向量（工业标准）",
    "  GloVe: 全局共现 + 最小二乘（count + SGD 混合）",
    "  BERT/GPT embedding: 上下文相关向量（一词多义可区分）",
    "  与第36章 TF-IDF 的区别：TF-IDF 是文档级向量，这里是词级语义向量",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 把窗口从 2 扩到 5，观察语义聚类的变化。
# 2. 实现 PPMI 加权（对高频词做子采样）避免 "the" 等高频词主导。
# 3. 用 word2vec 思路（SGD 优化 skip-gram 目标）训练 2 维向量。
# 4. 思考：为什么 "cat" 和 "dog" 相似度高，而 "cat" 和 "the" 相似度低？
