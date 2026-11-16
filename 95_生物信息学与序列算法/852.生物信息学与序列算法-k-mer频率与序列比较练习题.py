# ===== 第852课：生物信息学与序列算法-k-mer频率与序列比较 =====
# 知识点：
#   - k-mer = 长度为 k 的连续子串：序列可以概括为 k-mer 的多重集合
#   - 可能的 k-mer 有 4^k 种：k 越大越"特异性"，但数据越稀疏
#   - 观测到的不同 k-mer 数 / 理论上限 = 序列复杂度的一种度量
#   - k-mer 集合的 Jaccard 相似度 |A∩B|/|A∪B| 是免比对的序列距离
#   - 二核苷酸频率、k-mer 谱是组装（857）与检索（856）的地基
# 依赖：无（标准库）
import random
from collections import Counter


def rand_seq(n, rng):
    return "".join(rng.choice("ACGT") for _ in range(n))


def mutate(seq, rate, rng):
    out = []
    for b in seq:
        if rng.random() < rate:
            out.append(rng.choice([c for c in "ACGT" if c != b]))
        else:
            out.append(b)
    return "".join(out)


def kmer_counts(seq, k):
    if k <= 0 or k > len(seq):
        return Counter()
    return Counter(seq[i:i + k] for i in range(len(seq) - k + 1))


def jaccard(seq_a, seq_b, k):
    a = set(kmer_counts(seq_a, k))
    b = set(kmer_counts(seq_b, k))
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def dinucleotide_freq(seq):
    total = len(seq) - 1
    c = kmer_counts(seq, 2)
    return {d: c[d] / total for d in sorted(c)}


print("== k-mer 计数 ==")
rng = random.Random(7)
seq = rand_seq(120, rng)
print(f"  序列(120bp) = {seq}")
for k in (1, 2, 3, 4):
    c = kmer_counts(seq, k)
    possible = 4 ** k
    print(f"  k={k}: 观测到 {len(c):>3} 种 k-mer / 理论上限 {possible:>4} 种"
          f"  最高频: {c.most_common(1)[0][0]} × {c.most_common(1)[0][1]}")

print("\n== 最常见 k-mer ==")
for kmer, cnt in kmer_counts(seq, 3).most_common(5):
    print(f"  {kmer} × {cnt}")

print("\n== 二核苷酸频率 ==")
freq = dinucleotide_freq(seq)
print("  " + "  ".join(f"{d}:{freq[d]:.3f}" for d in sorted(freq)))

print("\n== 突变速率 vs Jaccard 相似度（k=5）==")
base = rand_seq(200, rng)
print(f"  {'突变率':>8}{'Jaccard':>10}")
for rate in (0.01, 0.03, 0.05, 0.10, 0.20):
    sim = jaccard(base, mutate(base, rate, rng), 5)
    print(f"  {rate:>8.0%}{sim:>10.3f}")
print("  突变越多共享 k-mer 越少 -> Jaccard 单调下降，可作免比对距离")

print("\n== 三个'物种'的相似度矩阵 ==")
species = {"A": base, "B": mutate(base, 0.03, rng), "C": mutate(base, 0.12, rng)}
names = sorted(species)
print("      " + "  ".join(f"{n:>6}" for n in names))
for a in names:
    row = "  ".join(f"{jaccard(species[a], species[b], 5):>6.3f}" for b in names)
    print(f"  {a}   {row}")

print("\n== k 的选择 ==")
for k in (2, 4, 6, 8):
    c = kmer_counts(seq, k)
    print(f"  k={k}: 不同 k-mer {len(c):>3} 种（{len(seq)-k+1} 个位置，上限 {4**k}）")
print("  k 太小 -> 无法区分位置；k 太大 -> 数据稀疏、组装碎片化")

print("\n== 小结 ==")
for line in (
    "  k-mer 是序列的'特征向量'：比较、检索、组装都建立在它之上",
    "  Jaccard 相似度免比对、速度快，适合海量序列初筛",
    "  观测 k-mer 数远小于 4^k 上限，正是序列复杂度的体现",
    "  856 课把 k-mer 变成索引，857 课把 k-mer 变成图",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现正则化 k-mer：取 kmer 与其反向互补中字典序较小者，使正负链统计一致，
#    并验证突变序列的正则 k-mer 谱更稳定。
# 2. 输出 k-mer 谱：所有观测 k-mer 按 k-mer 位置直方图（谱）打印成文本表格。
# 3. 用 3-mer 重叠串（overlap of 3-mers）推断两个序列间的突变位置数，与真实
#    突变率对照。
# 4. 思考：为什么基因组组装一般用 k=21~55 的较大 k？太小的 k 会在图中造成
#    什么问题？
