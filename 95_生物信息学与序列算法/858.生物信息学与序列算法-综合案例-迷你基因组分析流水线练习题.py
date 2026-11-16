# ===== 第858课：生物信息学与序列算法-综合案例-迷你基因组分析流水线 =====
# 知识点：
#   - 综合串起本章：FASTA 解析(851) + k-mer 距离(852) + ORF(853) + SW 比对(855)
#   - 流水线：数据生成 -> 逐序列统计 -> ORF 预测 -> 相似性搜索 -> 距离矩阵 -> UPGMA 聚类
#   - UPGMA：凝聚式层次聚类（平均连锁），输出逐级合并顺序
#   - 数据来自同一祖先基因加不同突变率 -> 真值已知，可验证结论
# 依赖：无（标准库）
import random

_AAS = "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"
_ORDER = [a + b + c for a in "TCAG" for b in "TCAG" for c in "TCAG"]
CODONS = dict(zip(_ORDER, _AAS))
NONSTOP = [c for c, a in CODONS.items() if a != "*"]


def rand_seq(n, rng):
    return "".join(rng.choice("ACGT") for _ in range(n))


def mutate(seq, rate, rng):
    return "".join(b if rng.random() >= rate
                   else rng.choice([c for c in "ACGT" if c != b]) for b in seq)


def gc_content(seq):
    acgt = sum(seq.count(b) for b in "ACGT")
    return (seq.count("G") + seq.count("C")) / acgt if acgt else 0.0


def jaccard_dist(a, b, k=4):
    sa = {a[i:i + k] for i in range(len(a) - k + 1)}
    sb = {b[i:i + k] for i in range(len(b) - k + 1)}
    return 1 - len(sa & sb) / len(sa | sb)


def longest_orf_protein(seq, min_aa=8):
    """正链上最长的完整 ORF 蛋白（ATG..终止子）。"""
    best = ""
    for frame in range(3):
        i = frame
        while i + 3 <= len(seq):
            if seq[i:i + 3] != "ATG":
                i += 3
                continue
            j = i + 3
            prot = []
            closed = False
            while j + 3 <= len(seq):
                aa = CODONS[seq[j:j + 3]]
                if aa == "*":
                    closed = True
                    break
                prot.append(aa)
                j += 3
            if closed and len(prot) > len(best):
                best = "".join(prot)
            i = j + 3 if closed else len(seq)
    return best if len(best) >= min_aa else None


def smith_waterman_score(a, b, match=2, mismatch=-1, gap=-2):
    prev = [0] * (len(b) + 1)
    best = 0
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        ai = a[i - 1]
        for j in range(1, len(b) + 1):
            s = match if ai == b[j - 1] else mismatch
            cur[j] = max(0, prev[j - 1] + s, prev[j] + gap, cur[j - 1] + gap)
            if cur[j] > best:
                best = cur[j]
        prev = cur
    return best


def upgma(labels, dist):
    """平均连锁 UPGMA。dist 的键为 tuple(sorted((簇a, 簇b)))。
    返回合并顺序 [(簇x, 簇y, 距离, 新簇名)]。"""
    cache = dict(dist)
    members = {l: [l] for l in labels}
    merges = []
    zid = 0
    while len(members) > 1:
        names = sorted(members)
        best = None
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                key = (names[i], names[j])
                if best is None or cache[key] < cache[best]:
                    best = key
        x, y = best
        zid += 1
        z = f"C{zid}"
        lx, ly = len(members[x]), len(members[y])
        merges.append((x, y, cache[best], z))
        members[z] = members.pop(x) + members.pop(y)
        for w in members:
            if w == z:
                continue
            dxw = cache[tuple(sorted((x, w)))]
            dyw = cache[tuple(sorted((y, w)))]
            cache[tuple(sorted((z, w)))] = (lx * dxw + ly * dyw) / (lx + ly)
    return merges


print("== 生成数据：同一祖先基因 -> 4 个'物种' ==")
rng = random.Random(42)
genes = {}


def make_gene(rng, n_codons=35):
    body = [rng.choice(NONSTOP) for _ in range(n_codons)]
    return "ATG" + "".join(body) + "TGA"


ancestor = make_gene(rng)
species = {}
for name, rate in (("SP1", 0.02), ("SP2", 0.05), ("SP3", 0.10), ("SP4", 0.18)):
    genes[name] = mutate(ancestor, rate, rng)
    flank_l, flank_r = rand_seq(40, rng), rand_seq(40, rng)
    species[name] = flank_l + genes[name] + flank_r
    print(f"  {name}: 突变率 {rate:.0%}，序列长 {len(species[name])}bp")

print("\n== 阶段1：基础统计 ==")
print(f"  {'物种':<6}{'长度':>5}{'GC%':>8}")
for name, seq in species.items():
    print(f"  {name:<6}{len(seq):>5}{gc_content(seq):>8.1%}")

print("\n== 阶段2：ORF 预测（正链最长 ORF）==")
ancestor_prot = longest_orf_protein(ancestor)
print(f"  祖先基因 ORF 蛋白 = {len(ancestor_prot)} aa")
for name, seq in species.items():
    prot = longest_orf_protein(seq)
    if prot is None:
        state = "未找到 ORF"
    elif prot == ancestor_prot:
        state = "与祖先一致"
    elif len(prot) == len(ancestor_prot):
        state = f"有氨基酸替换（长度不变 {len(prot)} aa）"
    else:
        state = f"被提前终止截短为 {len(prot)} aa"
    print(f"  {name}: {state}")
print("  突变的影响分三档：错义替换（长度不变）、提前终止（截短）、破坏起始（消失）")

print("\n== 阶段3：相似性搜索（祖先基因 vs 各物种 CDS，SW 得分）==")
scores = {}
for name in species:
    scores[name] = smith_waterman_score(ancestor, genes[name])
for name in sorted(species, key=lambda n: -scores[n]):
    print(f"  {name}: SW 得分 = {scores[name]:>3}（突变率 {[r for n_, r in (('SP1', 0.02), ('SP2', 0.05), ('SP3', 0.10), ('SP4', 0.18)) if n_ == name][0]:.0%}）")
print("  得分总体随突变率下降；SW 是局部最优，个别名次会随机波动")

print("\n== 阶段4：k-mer 距离矩阵 ==")
names = sorted(species)
dist = {}
print("      " + "  ".join(f"{n:>6}" for n in names))
for a in names:
    row = []
    for b in names:
        d = 0.0 if a == b else jaccard_dist(species[a], species[b])
        dist[tuple(sorted((a, b)))] = d
        row.append(f"{d:>6.3f}")
    print(f"  {a}  " + "  ".join(row))

print("\n== 阶段5：UPGMA 聚类（平均连锁）==")
merges = upgma(names, dist)
for x, y, d, z in merges:
    print(f"  合并 {x} 与 {y}（距离 {d:.3f}）-> {z}")
print("  预期：突变率相近的 SP1/SP2 先合并，SP4 最晚加入")

print("\n== 小结 ==")
for line in (
    "  流水线 = 一串纯函数：每一步输入输出明确、可单独验证",
    "  免比对特征(k-mer)做初筛与聚类，比对得分做精细确认",
    "  用已知真值的数据检验流水线：突变率排序就是金标准",
    "  真实流程还要加质量修剪、重复序列屏蔽、多样本比对等步骤",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给流水线加「质检关卡」：N 含量或长度低于阈值的序列直接剔除并记录原因。
# 2. 把阶段 3 换成第 856 课的 k-mer 索引搜索，对比两种相似性度量的排序是否一致。
# 3. 实现 UPGMA 的树输出：合并顺序缩进打印成文本树（子节点缩进一级）。
# 4. 思考：为什么聚类用 Jaccard 距离而不用 SW 得分直接聚类？各自的成本与
#    语义差异是什么？
