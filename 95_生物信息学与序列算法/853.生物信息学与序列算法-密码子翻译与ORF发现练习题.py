# ===== 第853课：生物信息学与序列算法-密码子翻译与ORF发现 =====
# 知识点：
#   - 遗传密码：64 个三联密码子 -> 20 种氨基酸 + 3 个终止子（*）
#   - 起始密码子 ATG 编码 M；终止子 TAA/TAG/TGA 不编码氨基酸
#   - 翻译按「阅读框」进行：每条链有 3 个框，双链共 6 个阅读框
#   - ORF（开放阅读框）= 从 ATG 开始、到终止子结束、长度达标的编码区
#   - 遗传密码有简并性：一种氨基酸可对应多个密码子，但一个密码子只对应一种
# 依赖：无（标准库）

_TABLE = ("TTT F TTC F TTA L TTG L CTT L CTC L CTA L CTG L "
          "ATT I ATC I ATA I ATG M GTT V GTC V GTA V GTG V "
          "TCT S TCC S TCA S TCG S CCT P CCC P CCA P CCG P "
          "ACT T ACC T ACA T ACG T GCT A GCC A GCA A GCG A "
          "TAT Y TAC Y TAA * TAG * CAT H CAC H CAA Q CAG Q "
          "AAT N AAC N AAA K AAG K GAT D GAC D GAA E GAG E "
          "TGT C TGC C TGA * TGG W CGT R CGC R CGA R CGG R "
          "AGT S AGC S AGA R AGG R GGT G GGC G GGA G GGG G")
_tokens = _TABLE.split()
CODONS = {_tokens[i]: _tokens[i + 1] for i in range(0, len(_tokens), 2)}
STOPS = {"TAA", "TAG", "TGA"}
AA2CODON = {}
for codon, aa in CODONS.items():
    if aa != "*" and aa not in AA2CODON:
        AA2CODON[aa] = codon


def reverse_complement(seq):
    table = {"A": "T", "T": "A", "C": "G", "G": "C"}
    return "".join(table[b] for b in reversed(seq))


def translate(seq):
    """按框 1 从头翻译到序列末尾或第一个终止子。"""
    protein = []
    for i in range(0, len(seq) - len(seq) % 3, 3):
        aa = CODONS[seq[i:i + 3]]
        if aa == "*":
            protein.append("*")
            break
        protein.append(aa)
    return "".join(protein)


def find_orfs(seq, min_aa=10):
    """在 6 个阅读框中找完整 ORF（ATG..终止子）。
    返回 (链, 框, 起点, 终点, 蛋白质)。同一 ORF 内部的 ATG 不重复开框（简化）。"""
    orfs = []
    for strand, s in (("+", seq), ("-", reverse_complement(seq))):
        for frame in range(3):
            i = frame
            while i + 3 <= len(s):
                if s[i:i + 3] != "ATG":
                    i += 3
                    continue
                j = i + 3
                prot = []
                closed = False
                while j + 3 <= len(s):
                    aa = CODONS[s[j:j + 3]]
                    if aa == "*":
                        closed = True
                        break
                    prot.append(aa)
                    j += 3
                if closed and len(prot) >= min_aa:
                    orfs.append((strand, frame + 1, i, j + 3, "".join(prot)))
                i = j + 3 if closed else len(s)
    return orfs


print("== 遗传密码表 ==")
print(f"  密码子总数 = {len(CODONS)}，其中终止子 {len(STOPS)} 个")
aa_count = len({aa for aa in CODONS.values() if aa != "*"})
print(f"  编码的氨基酸种类 = {aa_count}")
deg = sum(1 for c in CODONS.values() if c == "L")
print(f"  亮氨酸 L 有 {deg} 个密码子（简并性），而每个密码子只编码一种氨基酸")

print("\n== 翻译 ==")
demo = "ATGGCCATTGGAATTCGATAA"
protein = translate(demo)
print(f"  DNA:  {demo}")
print(f"  蛋白: {protein}   （ATG=M, GCC=A, ATT=I, GGA=G, ATT=I, TCG=S, GAT=D, TAA=终止）")

print("\n== 构造一条带已知蛋白的 DNA 再反查 ==")
rng = None  # 本课不用随机数
target_protein = "MAGFVLKT"
dna = "ATG" + "".join(AA2CODON[aa] for aa in target_protein[1:]) + "TAA"
flank = "CCCTTTCCCTTTCCCTTTCCCTTT"
full = flank + dna + flank
print(f"  目标蛋白: {target_protein}")
print(f"  反推 DNA: {dna}（简并表中每个氨基酸取第一个密码子）")
got = [o for o in find_orfs(full, min_aa=5)]
print(f"  找到 ORF 数 = {len(got)}")
for strand, frame, start, end, prot in got:
    print(f"    链{strand} 框{frame} [{start:>3},{end:>3}) 长 {len(prot)} aa: {prot}")
match = any(o[4] == target_protein for o in got)
print(f"  正链包含目标蛋白: {match}")

print("\n== 负链上的 ORF ==")
neg_orf_dna = "ATG" + "".join(AA2CODON[aa] for aa in "MFW") + "TAA"
neg_orf_rc = reverse_complement(neg_orf_dna)
host = "AAAACCCCGGGT" + neg_orf_rc + "TTTTGGGGCCCA"
found = find_orfs(host, min_aa=3)
for strand, frame, start, end, prot in found:
    print(f"  链{strand} 框{frame}: {prot}")
print(f"  负链 ORF 被发现: {any(o[4] == 'MFW' for o in found)}")

print("\n== 边界情况 ==")
no_stop = "ATG" + "".join(AA2CODON[aa] for aa in "MVW")            # 无终止子
no_start = "GGG" + "".join(AA2CODON[aa] for aa in "MVW") + "TAA"    # 无起始子
print(f"  跑出序列末端（无终止子）: 找到 ORF {len(find_orfs(no_stop, min_aa=2))} 个（不完整 ORF 不计）")
print(f"  无 ATG 起始:            找到 ORF {len(find_orfs(no_start, min_aa=2))} 个")

print("\n== 小结 ==")
for line in (
    "  翻译表是纯查表：64 个密码子构成完整、无歧义的映射",
    "  ORF 搜索 = 6 个阅读框上的线性扫描，是最朴素的基因预测方法",
    "  负链基因必须用反向互补才能被看到",
    "  真实基因预测还要看启动子、剪切位点等信号，ORF 只是第一层",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现密码子使用频率统计：给定 CDS 序列，输出 64 个密码子的使用次数与占比。
# 2. 实现「反向翻译的模糊版本」：蛋白质 -> 所有可能 DNA 序列数（按简并性相乘）。
# 3. 找出序列中所有 ORF（含不完整的：起点有 ATG 但无终止子），并标注「partial」。
# 4. 思考：为什么遗传密码是「简并但无歧义」的？这种设计对突变容错有什么好处？
