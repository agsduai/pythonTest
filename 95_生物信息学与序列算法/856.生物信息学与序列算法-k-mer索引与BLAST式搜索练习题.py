# ===== 第856课：生物信息学与序列算法-k-mer索引与BLAST式搜索 =====
# 知识点：
#   - BLAST 的核心思想：不逐对做 O(n×m) 比对，而是先用「种子」粗筛
#   - 种子 = 数据库中所有序列的 k-mer 索引：kmer -> [(seq_id, pos)]
#   - 查询的每个 k-mer 命中即「种子命中」，再向两侧无空位延伸（ungapped extension）
#   - 延伸得分超过阈值才算真命中，按最佳得分排序输出
#   - 这是「先索引后查询」「粗筛+精算」两阶段策略的经典范例
# 依赖：无（标准库）


def kmer_index(seqs, k):
    """seqs: {id: 序列} -> {kmer: [(id, pos)]}"""
    idx = {}
    for sid, seq in seqs.items():
        for i in range(len(seq) - k + 1):
            idx.setdefault(seq[i:i + k], []).append((sid, i))
    return idx


def blast_lite(query, seqs, k=4, min_score=10):
    """迷你 BLAST：k-mer 种子 + 双向无空位延伸。
    返回 [(id, score, (q_start, q_end, s_start, s_end))] 按得分降序。"""
    idx = kmer_index(seqs, k)
    # 1) 收集种子命中
    hits = {}
    for i in range(len(query) - k + 1):
        for sid, pos in idx.get(query[i:i + k], []):
            hits.setdefault(sid, []).append((i, pos))
    # 2) 对每条数据库序列取最佳延伸
    results = []
    for sid, hl in hits.items():
        s = seqs[sid]
        best_score, best_span = 0, None
        for qi, si in hl:
            l = 0
            while qi - 1 - l >= 0 and si - 1 - l >= 0 and query[qi - 1 - l] == s[si - 1 - l]:
                l += 1
            r = 0
            while qi + k + r < len(query) and si + k + r < len(s) \
                    and query[qi + k + r] == s[si + k + r]:
                r += 1
            score = k + l + r
            if score > best_score:
                best_score = score
                best_span = (qi - l, qi + k + r, si - l, si + k + r)
        if best_score >= min_score:
            results.append((sid, best_score, best_span))
    results.sort(key=lambda x: -x[1])
    return results, len(idx), sum(len(v) for v in idx.values())


print("== 构建迷你数据库 ==")
db = {
    "geneA_human":   "ATGGCCTATTGGAACGTGCAAGCTTTGACCATGCCCTTGGAGGT",
    "geneA_mouse":   "ATGGCCTATTGGAACGTGCAAGCTTCGACCATGCCCTTGGAGGC",
    "geneA_zebra":   "ATGGCCTATTGGAGCTGCAAGCTTTGACCATGCCCTTCGAGGA",
    "geneB_human":   "GGTACCTTAGGCATTACGGCATTACGGATTACAGGCTTAAGG",
    "geneC_random":  "TTTACCGGATCGATTCGATCGGATCGAATTCGCGCGCGCGCTA",
}
k = 4
idx, total_kmers = kmer_index(db, k), 0
for sid, seq in db.items():
    total_kmers += len(seq) - k + 1
print(f"  数据库 {len(db)} 条序列，总长 {sum(len(s) for s in db.values())} bp")
print(f"  k={k} 索引：不同 k-mer {len(idx)} 种 / 条目 {total_kmers} 个")

print("\n== 查询：来自 geneA_mouse 的突变片段 ==")
query = "GGAACGTGCAAGCTTCGACCATGCCCTTGG"
results, _, _ = blast_lite(query, db, k=k, min_score=10)
print(f"  查询长度 = {len(query)} bp")
print(f"  {'命中ID':<16}{'延伸得分':>8}  查询区间         库内区间")
for sid, score, (qs, qe, ss, se) in results:
    print(f"  {sid:<16}{score:>8}  [{qs:>3},{qe:>3})      [{ss:>3},{se:>3})")
print("  真正来源 geneA_mouse 之外，同源基因 geneA_human/zebra 也靠共享 k-mer 命中")

print("\n== 种子命中的统计意义 ==")
q_kmers = [query[i:i + k] for i in range(len(query) - k + 1)]
print(f"  查询 {len(q_kmers)} 个 k-mer，被索引命中过的：")
for qk in q_kmers[:6]:
    n_hits = len(idx.get(qk, []))
    print(f"    {qk} -> {n_hits} 处种子命中")
print("  （无需任何 DP 矩阵就完成了候选定位）")

print("\n== 与暴力全比对的速度直觉 ==")
ops_blast = len(query) * k + sum(len(v) for v in idx.values())
ops_dp = len(query) * sum(len(s) for s in db.values())
print(f"  种子法访问量级 ≈ {ops_blast}（索引项 + 命中扩展）")
print(f"  逐对 SW 比对   ≈ {ops_dp}（查询长度 × 库总长）")
print("  库越大，两者差距越悬殊 —— 真实 BLAST 还用双重命中与 X-drop 修剪")

print("\n== 阈值的作用 ==")
for ms in (8, 12, 16, 20):
    res, _, _ = blast_lite(query, db, k=k, min_score=ms)
    print(f"  min_score={ms:>2} -> 命中 {len(res)} 条: {[r[0] for r in res]}")
print("  阈值高 -> 少而准；阈值低 -> 多而杂（可能一堆偶然短匹配）")

print("\n== 小结 ==")
for line in (
    "  BLAST = k-mer 种子索引 + 延伸验证，用少量假阳性换百倍速度",
    "  索引一次构建、多次查询，是数据库型负载的通用模式",
    "  无空位延伸简单快速；带空位延伸可再精化为局部比对（855 课）",
    "  k 的选择权衡敏感性（小 k 多命中）与特异性（大 k 少命中）",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「双重命中」过滤：只保留同一 (query, subject) 上至少 2 个种子命中且
#    对角线一致的候选，观察命中数与准确率变化。
# 2. 实现带 X-drop 的延伸：延伸过程中连续错配累积超过 X 就停止，比较结果长度。
# 3. 把无空位延伸的候选交给第 855 课的 Smith-Waterman 精算得分，输出两阶段流水线。
# 4. 思考：真实 BLAST 对蛋白序列用「相邻双词（neighborhood words）」允许一个
#    氨基酸替换，为什么 DNA 用精确 k-mer 就足够？
