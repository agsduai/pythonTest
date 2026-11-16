# ===== 第857课：生物信息学与序列算法-DeBruijn图序列组装 =====
# 知识点：
#   - 组装：把大量短读段（reads）拼回原始基因组 —— 短读测序的基本问题
#   - De Bruijn 图：每个 k-mer 是一条边，其 (k-1)-mer 前缀/后缀是节点
#   - 组装 = 在图上走完所有边（欧拉路径），把节点末字符连起来
#   - 基因组中长度 ≥ k-1 的重复序列会造成分支 -> 需要更大的 k
#   - 比传统 read-overlap（O(N²) 两两比对）高效得多：只数 k-mer
# 依赖：无（标准库）
import random


def rand_seq(n, rng):
    return "".join(rng.choice("ACGT") for _ in range(n))


def shred(genome, read_len, step):
    """把基因组切成短读段。step=1 时覆盖所有 k-mer。"""
    return [genome[i:i + read_len] for i in range(0, len(genome) - read_len + 1, step)]


def build_dbg(reads, k):
    """reads -> {((k-1)mer前缀, (k-1)mer后缀): 计数}"""
    edges = {}
    for r in reads:
        for i in range(len(r) - k + 1):
            kmer = r[i:i + k]
            edges[(kmer[:-1], kmer[1:])] = edges.get((kmer[:-1], kmer[1:]), 0) + 1
    return edges


def assemble(edges):
    """沿欧拉路径消耗式走边 -> (拼装序列, 用掉的边数, 分支数)。"""
    adj = {}
    indeg = {}
    for (a, b) in edges:
        adj.setdefault(a, []).append(b)
        indeg[b] = indeg.get(b, 0) + 1
    branches = sum(1 for a, lst in adj.items() if len(lst) > 1)
    starts = [a for a, lst in adj.items() if len(lst) > indeg.get(a, 0)]
    start = starts[0] if starts else next(iter(adj))
    remaining = {a: list(lst) for a, lst in adj.items()}
    parts = [start]
    used = 0
    cur = start
    while remaining.get(cur):
        cur = remaining[cur].pop()
        parts.append(cur[-1])
        used += 1
    return "".join(parts), used, branches


print("== 原始基因组与读段 ==")
rng = random.Random(11)
genome = rand_seq(80, rng)
print(f"  基因组(80bp) = {genome}")
reads = shred(genome, 16, 1)
print(f"  切成 {len(reads)} 条 16bp 读段（步长1，覆盖全部 k-mer）")
print(f"  示例: {reads[0]} / {reads[5]} / {reads[-1]}")

print("\n== 从小 k 到大 k：重复序列迫使 k 增大 ==")
print(f"  {'k':>3}{'节点':>6}{'边':>6}{'分支':>6}{'用边':>6}{'拼装长':>8}  结果")
for k in range(4, 13):
    g = build_dbg(reads, k)
    seq, used, branches = assemble(g)
    ok = seq == genome
    print(f"  {k:>3}{len(g):>6}{sum(g.values()):>6}{branches:>6}{used:>6}{len(seq):>8}"
          f"  {'完整复原' if ok else '不完整（k 太小，(k-1)-mer 有重复）'}")
    if ok:
        print(f"  -> k={k} 时基因组中所有 {k-1}-mer 互不重复，图无分支，欧拉路径唯一")
        break

print("\n== 拼装结果 ==")
k_ok = None
for k in range(4, 13):
    g = build_dbg(reads, k)
    seq, used, branches = assemble(g)
    if seq == genome:
        k_ok = k
        print(f"  k={k}: 拼装 = {seq}")
        print(f"  与原序列一致: {seq == genome}")
        break

print("\n== 读段步长放宽：步长=3 ==")
reads_s3 = shred(genome, 16, 3)
g = build_dbg(reads_s3, k_ok)
seq3, used3, _ = assemble(g)
print(f"  {len(reads_s3)} 条读段 -> 拼装一致: {seq3 == genome}")
print("  步长只要让每个 k-mer 至少被一条读段完整覆盖即可")

print("\n== 人工重复导致分支 ==")
repeat_genome = rand_seq(20, rng) + "ACGTTGCA" + rand_seq(20, rng) + "ACGTTGCA" + rand_seq(10, rng)
for k in range(4, 10):
    g = build_dbg(shred(repeat_genome, 16, 1), k)
    seq, used, branches = assemble(g)
    if branches > 0:
        print(f"  含 8bp 重复的 78bp 基因组：k={k} 时分支数 = {branches}，拼装长 {len(seq)} ≠ {len(repeat_genome)}")
        break
print("  重复片段产生相同 (k-1)-mer 对 -> 同一节点多条出边 -> 单路径走法必然丢信息")
print("  真实组装器靠读段对(pair-end)与覆盖深度信息解消重复")

print("\n== 小结 ==")
for line in (
    "  De Bruijn 组装 = 数 k-mer 建图 + 走欧拉路径，不比较读段对",
    "  k 必须 > 基因组中最长重复的长度，否则图分支、拼装碎片化",
    "  节点数 ~ O(基因组长度)，与读段数量解耦 —— 可扩展到真人大小的基因组",
    "  读段错误会产生低覆盖的假边：真实组装器会按深度剪枝",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给读段加错（如 2% 碱基替换），统计每个 k-mer 的覆盖深度，删除深度=1 的假边
#    后再组装，比较正确率。
# 2. 实现分支报告：输出图中的分支节点及其出边，演示重复序列的位置。
# 3. 用步长=2、读长=8 组装，找出「不再能完整复原」的最小读长，并解释原因。
# 4. 思考：De Bruijn 组装与读段重叠（read overlap）法各适合什么场景？短读长
#    高覆盖时代为什么选择了 De Bruijn？
